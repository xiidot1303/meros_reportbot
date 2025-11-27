from app.models import Order, Client
from app.services import *
from app.services import notification_service
from django.db import transaction


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
                notification_service.order_status_change_notify.delay(order_obj.id)

            # check order price change
            if order_obj.total_amount != total_amount:
                old_price = order_obj.total_amount
                order_obj.total_amount = total_amount
                have_to_update = True
                # notify about price change
                notification_service.order_price_change_notify.delay(order_obj.id, old_price)

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
                created_orders = Order.objects.bulk_create(to_create[i:i+500], ignore_conflicts=True)
                for created_order in created_orders:
                    notification_service.order_status_change_notify.delay(created_order.id)

        if to_update:
            # Update existing clients by 500 to avoid too large queries
            for i in range(0, len(to_update), 500):
                Order.objects.bulk_update(to_update[i:i+500], ["status", "total_amount"])

        
        
        