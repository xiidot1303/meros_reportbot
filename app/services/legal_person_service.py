"""Bulk-update legal persons' phone numbers in SmartUp from an xlsx file.

Driven by the admin-only `/update_phones` bot command. The flow is:

    xlsx (column A = ТИН, column D = phone)
      -> parse_workbook          — validate the sheet's shape, collect rows
      -> SmartUp legal_person$export  — every person, in memory only
      -> match on `tin`
      -> build_import_payload    — the exported record, `main_phone` replaced
      -> SmartUp legal_person$import  — write back

SmartUp's import is a *full record* write, not a patch: whatever the payload
omits is cleared on their side. So the payload is always built from that
person's exported record, and `main_phone` is the single field allowed to
differ — see `build_import_payload`. Columns B and C of the sheet are ignored
by design; the client fills them in with whatever they find useful.

Nothing here is persisted. The export is large and goes stale immediately, so
it lives only for the duration of one run.
"""

import logging
import re

from openpyxl import load_workbook

from app.services.error_service import report_exception
from app.services.smartup_service import ApiMethods, SmartUpApiClient


logger = logging.getLogger(__name__)


# 0-based sheet columns. B and C carry free-form notes and are not read.
TIN_COLUMN = 0
PHONE_COLUMN = 3

# The sheet must have at least this many columns for column D to exist at all.
MIN_COLUMNS = 4

# Rows are sent in batches rather than one request per person: a single
# 1000-person import would sit well past the timeout, and one request per row
# would be ~1000 round trips.
IMPORT_BATCH_SIZE = 50

# Every field the import accepts. The export returns these plus the nested
# `groups` / `bank_accounts` / `rooms` collections, which the import must not
# carry — sending them would rewrite those relations too.
IMPORT_FIELDS = (
    "person_id",
    "name",
    "short_name",
    "code",
    "latlng",
    "tin",
    "cea",
    "main_phone",
    "web",
    "address",
    "post_address",
    "address_guide",
    "region_id",
    "region_code",
    "primary_person_code",
    "parent_person_code",
    "allow_owner",
    "vat_code",
    "barcode",
    "zip_code",
    "email",
    "is_budgetarian",
    "is_client",
    "is_supplier",
    "state",
)


class WorkbookFormatError(Exception):
    """The uploaded file is not the expected two-meaningful-columns sheet."""


def normalize_tin(value):
    """ТИН as bare digits.

    The sheet may hold it as a number (openpyxl then hands back an int, or a
    float like 305018351.0), and SmartUp writes some as "203809202-1" — the
    suffix marks a branch, so it is kept as part of the identity and only the
    formatting noise is stripped.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    # drop spaces and separators Excel or a human may have introduced, but keep
    # the "-N" branch suffix
    text = re.sub(r"[\s_]+", "", text)
    return text


def normalize_phone(value):
    """The phone exactly as the admin typed it, minus stray whitespace.

    Deliberately not reformatted: SmartUp stores phones in several shapes
    ("97 791-71-78(1)", "+99891000000") and re-writing them is not what was
    asked for. Only an Excel-numeric cell is coerced, since openpyxl would
    otherwise yield "998910000000.0".
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


# The header the client's export writes, normalized for comparison. Only A and
# D are checked — B ("Название") and C ("Рабочиезоны") carry notes we never read,
# so their wording is allowed to drift.
TIN_HEADERS = ("инн", "тин", "stir")
PHONE_HEADERS = ("телефон", "telefon", "phone")


def _header_text(value):
    """A header cell folded for comparison: lowercase, no spaces."""
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def _is_header_row(row):
    """True for a row whose ТИН cell holds no digits — i.e. a title/header."""
    tin = normalize_tin(row[TIN_COLUMN] if len(row) > TIN_COLUMN else None)
    return not any(char.isdigit() for char in tin)


def _check_header(row):
    """Reject a sheet whose A/D headers are not ИНН and Телефон.

    Guards against the likeliest mistake — a file with the right shape but the
    columns in a different order, which would otherwise write phone numbers
    onto whatever happened to sit in column A.
    """
    tin_header = _header_text(row[TIN_COLUMN])
    phone_header = _header_text(row[PHONE_COLUMN])

    if not any(h in tin_header for h in TIN_HEADERS):
        raise WorkbookFormatError("bad_tin_header")
    if not any(h in phone_header for h in PHONE_HEADERS):
        raise WorkbookFormatError("bad_phone_header")


def parse_workbook(file_bytes):
    """Read (tin, phone) pairs off the first sheet.

    Returns `(rows, skipped)` where `rows` is a list of `(tin, phone)` in sheet
    order and `skipped` counts rows dropped for missing a ТИН or a phone.

    Raises `WorkbookFormatError` when the file is not a readable xlsx, has too
    few columns, or yields no usable row — the command refuses anything that
    is not the agreed format rather than guessing at it.
    """
    try:
        workbook = load_workbook(file_bytes, read_only=True, data_only=True)
    except Exception as exc:
        raise WorkbookFormatError("unreadable") from exc

    try:
        sheet = workbook.worksheets[0]

        if sheet.max_column is not None and sheet.max_column < MIN_COLUMNS:
            raise WorkbookFormatError("too_few_columns")

        rows = []
        skipped = 0
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            if row is None or not any(cell is not None for cell in row):
                continue
            if len(row) < MIN_COLUMNS:
                skipped += 1
                continue
            if index == 0 and _is_header_row(row):
                # the sheet leads with "ИНН / Название / Рабочие зоны / Телефон";
                # verify it rather than merely skipping it
                _check_header(row)
                continue

            tin = normalize_tin(row[TIN_COLUMN])
            phone = normalize_phone(row[PHONE_COLUMN])
            if not tin or not phone:
                skipped += 1
                continue
            rows.append((tin, phone))
    finally:
        workbook.close()

    if not rows:
        raise WorkbookFormatError("no_rows")

    return rows, skipped


def build_import_payload(person, phone):
    """That person's exported record with `main_phone` swapped for `phone`.

    Only the fields the import knows about are copied, and each keeps its
    exported value — the nested collections are dropped and nothing else is
    touched. A field the export omitted is sent as null so the record stays
    complete.
    """
    payload = {field: person.get(field) for field in IMPORT_FIELDS}
    payload["main_phone"] = phone
    return payload


def _index_by_tin(persons):
    """Map normalized ТИН -> exported person.

    SmartUp can hold several records under one ТИН (a branch and its parent);
    the first one wins, matching the order the export returns.
    """
    index = {}
    for person in persons:
        tin = normalize_tin(person.get("tin"))
        if tin and tin not in index:
            index[tin] = person
    return index


def update_phone_numbers(file_bytes, progress=None):
    """Run one whole update pass. Blocking — call it off the event loop.

    `progress` is an optional callable taking a short status string, used by
    the bot command to keep the admin informed while the export downloads.

    Returns a result dict: `updated`, `not_found` (ТИНs absent from SmartUp),
    `unchanged` (phone already correct), `skipped` (unusable sheet rows),
    `failed_batches`, and `total` sheet rows.
    """
    rows, skipped = parse_workbook(file_bytes)

    if progress:
        progress("export")

    client = SmartUpApiClient(ApiMethods.legal_person_export)
    persons = client.export_legal_persons()
    by_tin = _index_by_tin(persons)

    if progress:
        progress("match")

    to_import = []
    not_found = []
    unchanged = 0
    # one phone per ТИН — a repeated ТИН later in the sheet overrides an
    # earlier row rather than being sent twice
    seen = {}
    for tin, phone in rows:
        person = by_tin.get(tin)
        if person is None:
            if tin not in seen:
                not_found.append(tin)
            continue
        if normalize_phone(person.get("main_phone")) == phone:
            unchanged += 1
            continue
        seen[tin] = phone

    for tin, phone in seen.items():
        to_import.append(build_import_payload(by_tin[tin], phone))

    if progress:
        progress("import")

    updated = 0
    failed_batches = 0
    for start in range(0, len(to_import), IMPORT_BATCH_SIZE):
        batch = to_import[start:start + IMPORT_BATCH_SIZE]
        try:
            client.import_legal_persons(batch)
            updated += len(batch)
        except Exception as exc:
            # one bad batch must not abandon the rest of the file
            failed_batches += 1
            logger.exception("legal_person import batch failed")
            report_exception(
                exc,
                "app.services.legal_person_service.update_phone_numbers",
                {"batch_start": start, "batch_size": len(batch)},
            )

    return {
        "total": len(rows),
        "updated": updated,
        "unchanged": unchanged,
        "not_found": not_found,
        "skipped": skipped,
        "failed_batches": failed_batches,
    }
