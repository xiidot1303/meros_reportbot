from app.services.smartup_service import *
from app.services.client_service import update_clients_by_data
from app.services.order_service import handle_orders_change

def fetch_clients():
    api_client = SmartUpApiClient(ApiMethods.clients_list)
    clients = api_client.get_clients()
    update_clients_by_data(clients)


def check_orders():
    api_client = SmartUpApiClient(ApiMethods.orders_list)
    orders = api_client.get_orders()
    handle_orders_change(orders)