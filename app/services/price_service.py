"""Sync the SmartUp price lists (25% / 100% prepayment) into `ProductPrice`.

Rows are kept per regional warehouse (`ProductPrice.WAREHOUSE_CHOICES`), since
each warehouse gets its own price list in the bot.

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
PRICE_TYPE_IDS = (ProductPrice.PREPAYMENT_25, ProductPrice.PREPAYMENT_100)

BULK_BATCH_SIZE = 500

# Fields overwritten on an existing row when the upsert hits a conflict.
SYNCED_FIELDS = [
    "price_type_name",
    "product_code",
    "product_name",
    "manufacturer",
    "box_quant",
    "card_code",
    "price",
    "quant",
    "expiry_date",
]

# `updated_at` is stamped by hand so every row of one sync shares a timestamp.
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
    warehouse_id = row.get("warehouse_id")
    if None in (price_type_id, product_id, card_id, warehouse_id):
        return None

    return ProductPrice(
        price_type_id=int(price_type_id),
        price_type_name=row.get("price_type_name"),
        product_id=int(product_id),
        product_code=row.get("product_code"),
        product_name=row.get("product_name"),
        manufacturer=row.get("manufacturer"),
        box_quant=parse_decimal(row.get("box_quant")),
        card_id=int(card_id),
        warehouse_id=int(warehouse_id),
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
        objects[(obj.price_type_id, obj.product_id, obj.card_id, obj.warehouse_id)] = obj

    if not objects:
        logger.warning("Price sync returned no usable rows; keeping existing prices")
        return 0, 0

    # only keys and ids — loading ~150k full model instances is needlessly heavy
    existing_map = {
        (price_type_id, product_id, card_id, warehouse_id): price_id
        for price_id, price_type_id, product_id, card_id, warehouse_id
        in ProductPrice.objects.filter(price_type_id__in=PRICE_TYPE_IDS).values_list(
            "id", "price_type_id", "product_id", "card_id", "warehouse_id")
    }

    now = timezone.now()
    for obj in objects.values():
        obj.updated_at = now

    created = sum(1 for key in objects if key not in existing_map)
    updated = len(objects) - created
    stale_ids = [
        price_id for key, price_id in existing_map.items() if key not in objects
    ]

    # One INSERT ... ON CONFLICT DO UPDATE per batch. `bulk_update` was used
    # here before, but it renders a CASE WHEN per field per row, and at ~150k
    # rows (7 warehouses × 2 price types) a sync took many minutes.
    rows_to_save = list(objects.values())
    with transaction.atomic():
        for i in range(0, len(rows_to_save), BULK_BATCH_SIZE):
            ProductPrice.objects.bulk_create(
                rows_to_save[i:i + BULK_BATCH_SIZE],
                update_conflicts=True,
                unique_fields=["price_type_id", "product_id", "card_id", "warehouse_id"],
                update_fields=UPDATE_FIELDS,
            )

        for i in range(0, len(stale_ids), BULK_BATCH_SIZE):
            ProductPrice.objects.filter(
                id__in=stale_ids[i:i + BULK_BATCH_SIZE]).delete()

    logger.info(
        "Price sync: %s created, %s updated, %s removed",
        created, updated, len(stale_ids),
    )
    return created, updated


def fetch_and_save_prices():
    """Pull both price lists from Oracle and mirror them into the local table."""
    rows = OracleClient().get_product_prices(PRICE_TYPE_IDS, ProductPrice.WAREHOUSE_IDS)
    return update_prices_by_data(rows)
