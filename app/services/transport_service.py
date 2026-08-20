from app.models import Order, OrderTransport
from app.services.error_service import notify_on_exception


def find_order(order_id):
    """Resolve an incoming order_id against SmartUp's deal_id first, then the
    local primary key — the external system may send either."""
    if order_id is None:
        return None

    order = Order.objects.filter(deal_id=str(order_id)).first()
    if order:
        return order

    try:
        return Order.objects.filter(pk=int(order_id)).first()
    except (TypeError, ValueError):
        return None


@notify_on_exception
def save_order_transport(order_id, car_model=None, car_brand=None, car_autonum=None,
                         firstname=None, lastname=None, phone_number=None):
    """Create or update the transport (car + driver) attached to an order.

    Keyed on order_id so repeated posts for the same order update the existing
    row instead of piling up duplicates. Returns (OrderTransport, created).
    """
    order = find_order(order_id)

    transport, created = OrderTransport.objects.update_or_create(
        order_id_external=str(order_id),
        defaults={
            "order": order,
            "car_model": car_model,
            "car_brand": car_brand,
            "car_autonum": car_autonum,
            "firstname": firstname,
            "lastname": lastname,
            "phone_number": phone_number,
        },
    )
    return transport, created
