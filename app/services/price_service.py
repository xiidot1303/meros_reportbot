"""Sync the SmartUp price lists (25% / 100% prepayment) into `ProductPrice`.

Rows come straight from the Oracle DB ([app/services/oracle_service.py](app/services/oracle_service.py));
this module only maps them onto the model and upserts in bulk. Rows that
disappear from Oracle — a product that ran out of stock or lost its price —
are deleted so the local table always mirrors the current price list.
"""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from app.models import ProductPrice
from app.services.oracle_service import OracleClient


logger = logging.getLogger(__name__)


# Both price lists we mirror locally.
PRICE_TYPE_IDS = (ProductPrice.NEGOTIATED, ProductPrice.PREPAYMENT_100)

BULK_BATCH_SIZE = 500

# Fields copied from the freshly fetched row onto an existing one.
SYNCED_FIELDS = [
    "price_type_name",
    "product_name",
    "manufacturer",
    "box_quant",
    "card_code",
    "price",
    "quant",
    "expiry_date",
]

# `updated_at` is stamped by hand because `auto_now` never fires on bulk_update.
UPDATE_FIELDS = SYNCED_FIELDS + ["updated_at"]


def parse_expiry_date(value):
    """`EXPIRY_DATE_ID` is an Oracle number shaped as YYYYMMDD, e.g. 20271201."""
    if not value:
        return None
    try:
        return datetime.strptime(str(int(value)), "%Y%m%d").date()
    except (TypeError, ValueError):
        logger.warning("Unparseable EXPIRY_DATE_ID: %r", value)
        return None


def parse_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def build_price_object(row):
    """Map one Oracle row onto an unsaved `ProductPrice`, or None if unusable."""
    price_type_id = row.get("price_type_id")
    product_id = row.get("product_id")
    card_id = row.get("card_id")
    if price_type_id is None or product_id is None or card_id is None:
        return None

    return ProductPrice(
        price_type_id=int(price_type_id),
        price_type_name=row.get("price_type_name"),
        product_id=int(product_id),
        product_name=row.get("product_name"),
        manufacturer=row.get("manufacturer"),
        box_quant=parse_decimal(row.get("box_quant")),
        card_id=int(card_id),
        card_code=row.get("card_code"),
        price=parse_decimal(row.get("price")),
        quant=parse_decimal(row.get("quant")),
        expiry_date=parse_expiry_date(row.get("expiry_date_id")),
    )


def update_prices_by_data(rows):
    """Upsert the fetched rows and drop the ones Oracle no longer returns."""
    objects = {}
    for row in rows:
        obj = build_price_object(row)
        if obj is None:
            continue
        # Oracle can return the same key twice if a product sits on several
        # cards with the same id; last one wins, as it would in the DB.
        objects[(obj.price_type_id, obj.product_id, obj.card_id)] = obj

    if not objects:
        logger.warning("Price sync returned no usable rows; keeping existing prices")
        return 0, 0

    existing = ProductPrice.objects.filter(price_type_id__in=PRICE_TYPE_IDS)
    existing_map = {
        (p.price_type_id, p.product_id, p.card_id): p for p in existing
    }

    now = timezone.now()
    to_create = []
    to_update = []
    for key, obj in objects.items():
        current = existing_map.get(key)
        if current is None:
            to_create.append(obj)
            continue
        for field in SYNCED_FIELDS:
            setattr(current, field, getattr(obj, field))
        current.updated_at = now
        to_update.append(current)

    stale_ids = [
        price.id for key, price in existing_map.items() if key not in objects
    ]

    with transaction.atomic():
        for i in range(0, len(to_create), BULK_BATCH_SIZE):
            ProductPrice.objects.bulk_create(
                to_create[i:i + BULK_BATCH_SIZE], ignore_conflicts=True)

        for i in range(0, len(to_update), BULK_BATCH_SIZE):
            ProductPrice.objects.bulk_update(
                to_update[i:i + BULK_BATCH_SIZE], UPDATE_FIELDS)

        for i in range(0, len(stale_ids), BULK_BATCH_SIZE):
            ProductPrice.objects.filter(
                id__in=stale_ids[i:i + BULK_BATCH_SIZE]).delete()

    logger.info(
        "Price sync: %s created, %s updated, %s removed",
        len(to_create), len(to_update), len(stale_ids),
    )
    return len(to_create), len(to_update)


def fetch_and_save_prices():
    """Pull both price lists from Oracle and mirror them into the local table."""
    rows = OracleClient().get_product_prices(PRICE_TYPE_IDS)
    return update_prices_by_data(rows)
