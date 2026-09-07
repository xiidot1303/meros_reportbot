from app.services.price_service import fetch_and_save_prices
from app.services.error_service import notify_on_exception


@notify_on_exception(reraise=False)
def sync_prices():
    fetch_and_save_prices()
