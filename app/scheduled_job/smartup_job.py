from app.services.smartup_service import *
from app.services.client_service import update_clients_by_data
from app.services.order_service import handle_orders_change
from app.services.error_service import notify_on_exception
from bot.models import Cabinet

@notify_on_exception(reraise=False)
def fetch_clients():
    api_client = SmartUpApiClient(ApiMethods.clients_list)
    clients = api_client.get_clients()
    update_clients_by_data(clients)


@notify_on_exception(reraise=False)
def check_orders():
    api_client = SmartUpApiClient(ApiMethods.orders_list)
    clients_ids = list(Cabinet.objects.values_list('client__external_id', flat=True))
    orders = api_client.get_orders(clients_ids)
    handle_orders_change(orders)