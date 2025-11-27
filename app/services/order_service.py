from app.models import Order, Client
from app.services import *
from app.services import notification_service
from django.db import transaction
from django.db.models import Q
from asgiref.sync import sync_to_async
from app.services.smartup_service import SmartUpApiClient, ApiMethods


def handle_orders_change(orders_list: list):
    incoming_ids = [item[0] for item in orders_list]
    existing_orders = Order.objects.filter(deal_id__in=incoming_ids)
    existing_map = {c.deal_id: c for c in existing_orders}
    to_create = []
    to_update = []

    for order in orders_list:
        status = order[11]
        deal_id = order[0]
        project = order[1]
        client_id = order[3]
        delivery_date = order[5]
        tin = order[6]
        price_type = order[7]
        manager = order[2]
        deal_time = order[9]
        total_amount = order[10]

        # update if exist
        if deal_id in existing_map:
            order_obj = existing_map[deal_id]
            have_to_update = False
            # check for status change
            if order_obj.status != status:
                order_obj.status = status
                have_to_update = True
                # notify about status change
                notification_service.order_status_change_notify.delay(
                    order_obj.id)

            # check order price change
            if int(order_obj.total_amount) != int(total_amount):
                old_price = order_obj.total_amount
                order_obj.total_amount = total_amount
                have_to_update = True
                # notify about price change
                notification_service.order_price_change_notify.delay(
                    order_obj.id, old_price)

            if have_to_update:
                to_update.append(order_obj)

        else:
            client = Client.objects.filter(external_id=client_id).first()

            # Prepare new object
            to_create.append(
                Order(
                    deal_id=deal_id,
                    status=status,
                    project=project,
                    client=client,
                    delivery_date=datetime.strptime(
                        delivery_date, "%d.%m.%Y").date() if delivery_date else None,
                    deal_datetime=datetime.strptime(
                        deal_time, "%d.%m.%Y %H:%M:%S") if deal_time else None,
                    tin=tin,
                    price_type=price_type,
                    manager=manager,
                    total_amount=total_amount,
                )
            )

    # Perform bulk operations
    with transaction.atomic():
        if to_create:
            # deal by 500 to avoid too large queries
            for i in range(0, len(to_create), 500):
                created_orders = Order.objects.bulk_create(
                    to_create[i:i+500], ignore_conflicts=True)

        if to_update:
            # Update existing clients by 500 to avoid too large queries
            for i in range(0, len(to_update), 500):
                Order.objects.bulk_update(
                    to_update[i:i+500], ["status", "total_amount"])

    # send notification to all created orders
    for created_order in to_create:
        notification_service.order_status_change_notify.delay(
            order_deal_id=created_order.deal_id
        )

    # delete orders
    Order.objects.exclude(
        deal_id__in=incoming_ids
    ).delete()


@sync_to_async
def get_archived_orders_by_client(client: Client, offset=0):
    smartup_client = SmartUpApiClient(ApiMethods.archived_orders_list)
    data = smartup_client.get_archived_orders_by_client(
        client.external_id, offset=offset)
    orders_list = []
    for order in data:
        deal_id = order[0]
        project = order[1]
        client_id = order[3]
        delivery_date = order[5]
        tin = order[6]
        price_type = order[7]
        manager = order[2]
        deal_time = order[9]
        total_amount = order[10]

        orders_list.append(
            Order(
                deal_id=deal_id,
                project=project,
                client=client,
                delivery_date=datetime.strptime(
                    delivery_date, "%d.%m.%Y").date() if delivery_date else None,
                deal_datetime=datetime.strptime(
                    deal_time, "%d.%m.%Y %H:%M:%S") if deal_time else None,
                tin=tin,
                price_type=price_type,
                manager=manager,
                total_amount=total_amount,
            )
        )

    return orders_list