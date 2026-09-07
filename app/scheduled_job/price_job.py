from app.services.price_service import fetch_and_save_prices
from app.services.price_report_service import generate_price_list_files
from app.services.error_service import notify_on_exception


@notify_on_exception(reraise=False)
def sync_prices():
    """Refresh the price tables, then rebuild the xlsx the bot hands out.

    The files are built here rather than on each click: the price list is the
    same for every client, and openpyxl is CPU-bound, so generating on demand
    would block the bot's event loop for ~2s per request.
    """
    fetch_and_save_prices()
    generate_price_list_files()
