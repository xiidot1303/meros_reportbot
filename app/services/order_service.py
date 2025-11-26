from app.models import Order, Client
from app.services import *
from app.services.notification_service import order_status_change_notify


def handle_orders_change(orders_list: list):
    for order in orders_list:
        status = order[11]
        deal_id = order[0]
        project = order[1]
        client_id = order[3]
        delivery_date = order[5]
        tin = order[6]
        price_type = order[7]
        manager = order[2]
        total_amount = order[10]
        client = Client.objects.filter(external_id=client_id).first()
        # create new order or get existing
        order_obj, created = Order.objects.get_or_create(
            deal_id=deal_id,
            defaults={
                "status": status,
                "project": project,
                "client": client,
                "delivery_date": datetime.strptime(delivery_date, "%d.%m.%Y").date() if delivery_date else None,
                "tin": tin,
                "price_type": price_type,
                "manager": manager,
                "total_amount": total_amount,
            }
        )

        if created:
            # notify about new order
            order_status_change_notify(order_obj)
        else:
            # check for status change
            if order_obj.status != status:
                order_obj.status = status
                order_obj.save()
                # notify about status change
                order_status_change_notify(order_obj)
         
            # check order price change
            if order_obj.total_amount != total_amount:
                order_obj.total_amount = total_amount
                order_obj.save()