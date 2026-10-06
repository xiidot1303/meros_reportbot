"""Sync SmartUp regions and warehouses from Oracle into `Region` / `Warehouse`.

They exist to route warehouse feedback to the right regional Telegram group:
order → warehouse → region → oblast → `Region.telegram_group_id`. The group id
is set by hand in the admin, so the sync only upserts the Oracle fields and
never touches it, and never deletes a row (that would lose the group id).
"""

import logging

from django.db import transaction
from django.utils import timezone

from app.models import Region, Warehouse
from app.services.oracle_service import OracleClient


logger = logging.getLogger(__name__)

REGION_FIELDS = ["name", "parent_id", "parent_name"]
WAREHOUSE_FIELDS = ["name", "region_id", "region_name"]


def _upsert(model, key, fields, items):
    """Create new rows and update changed ones, matched on `key`."""
    existing = model.objects.in_bulk([item[key] for item in items], field_name=key)
    now = timezone.now()
    to_create, to_update = [], []
    for item in items:
        obj = existing.get(item[key])
        if obj is None:
            to_create.append(model(**item))
        elif any(getattr(obj, f) != item[f] for f in fields):
            for f in fields:
                setattr(obj, f, item[f])
            # bulk_update bypasses auto_now, so stamp it by hand
            obj.updated_at = now
            to_update.append(obj)

    with transaction.atomic():
        model.objects.bulk_create(to_create, batch_size=500)
        if to_update:
            model.objects.bulk_update(
                to_update, fields + ["updated_at"], batch_size=500)
    return len(to_create), len(to_update)


def fetch_and_save_regions():
    rows = OracleClient().get_regions(Region.UZBEKISTAN_ID)
    items = [
        {
            "region_id": int(row["region_id"]),
            "name": row["name"] or "",
            "parent_id": int(row["parent_id"]),
            "parent_name": row["parent_name"],
        }
        for row in rows
    ]
    created, updated = _upsert(Region, "region_id", REGION_FIELDS, items)
    logger.info("Region sync: %s created, %s updated", created, updated)


def fetch_and_save_warehouses():
    rows = OracleClient().get_warehouses()
    # a warehouse can have several info rows; keep one per warehouse
    items = {
        int(row["warehouse_id"]): {
            "warehouse_id": int(row["warehouse_id"]),
            "name": row["warehouse_name"] or "",
            "region_id": int(row["region_id"]) if row["region_id"] else None,
            "region_name": row["region_name"],
        }
        for row in rows
    }
    created, updated = _upsert(
        Warehouse, "warehouse_id", WAREHOUSE_FIELDS, list(items.values()))
    logger.info("Warehouse sync: %s created, %s updated", created, updated)
