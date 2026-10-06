from app.services.region_service import fetch_and_save_regions, fetch_and_save_warehouses
from app.services.error_service import notify_on_exception


@notify_on_exception(reraise=False)
def sync_regions():
    """Refresh regions, then warehouses — routing of warehouse feedback reads both."""
    fetch_and_save_regions()
    fetch_and_save_warehouses()
