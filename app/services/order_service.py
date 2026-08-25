from decimal import Decimal

from app.models import Order, Client
from app.services import *
from app.services import notification_service
from app.services.error_service import notify_on_exception
from django.db import transaction
from django.db.models import Q
from asgiref.sync import sync_to_async
from app.services.smartup_service import SmartUpApiClient, ApiMethods


@notify_on_exception
def handle_orders_change(orders_list: list):
    incoming_ids = [item[0] for item in orders_list]
    existing_orders = Order.objects.filter(deal_id__in=incoming_ids)
    existing_map = {c.deal_id: c for c in existing_orders}
    to_create = []
    to_update = []
    # orders to notify about; enqueued only after the transaction commits
    to_notify_ids = []
    to_notify_deal_ids = []

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
        delivery_number = order[12] if len(order) > 12 else None

        # update if exist
        if deal_id in existing_map:
            order_obj = existing_map[deal_id]
            have_to_update = False
            # TTN number is issued after the order ships, so it can appear later
            if delivery_number and order_obj.delivery_number != delivery_number:
                order_obj.delivery_number = delivery_number
                have_to_update = True
            # check for status change
            if order_obj.status != status:
                order_obj.status = status
                have_to_update = True
                # notify about status change if status is in
                if status in ["B#W", "B#S", "B#V", "A"]:
                    to_notify_ids.append(order_obj.id)

            # # check order price change
            # current_total = Decimal(str(order_obj.total_amount)) if order_obj.total_amount is not None else None
            # incoming_total = Decimal(str(total_amount)) if total_amount is not None else None
            # if current_total != incoming_total:
            #     old_price = order_obj.total_amount
            #     order_obj.total_amount = total_amount
            #     have_to_update = True
            #     # notify about price change
            #     notification_service.order_price_change_notify.delay(
            #         order_obj.id, old_price, total_amount)

            if have_to_update:
                to_update.append(order_obj)

        else:
            client = Client.objects.filter(external_id=client_id).first()

            # Prepare new object
            to_create.append(
                Order(
                    deal_id=deal_id,
                    delivery_number=delivery_number,
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

    # archived orders
    for order in Order.objects.filter(~Q(deal_id__in=incoming_ids) & ~Q(status="A")):
        order.status = "A"
        to_update.append(order)
        to_notify_ids.append(order.pk)

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
                    to_update[i:i+500],
                    ["status", "total_amount", "delivery_number"])

        # bulk_create(ignore_conflicts=True) leaves pks unset, so notify by deal_id
        to_notify_deal_ids.extend(order.deal_id for order in to_create)

        # enqueue only once the rows are actually written, otherwise the worker
        # can read the pre-update state (or a row that does not exist yet)
        transaction.on_commit(
            lambda: _enqueue_status_notifications(
                to_notify_ids, to_notify_deal_ids)
        )


def _enqueue_status_notifications(order_ids: list, order_deal_ids: list):
    for order_id in order_ids:
        notification_service.order_status_change_notify.delay(order_id=order_id)
    for deal_id in order_deal_ids:
        notification_service.order_status_change_notify.delay(
            order_deal_id=deal_id)



@sync_to_async
@notify_on_exception
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
        delivery_number = order[11] if len(order) > 11 else None

        orders_list.append(
            Order(
                deal_id=deal_id,
                delivery_number=delivery_number,
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