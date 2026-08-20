from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from app.models import OrderTransport
from app.services import notification_service


@receiver(post_save, sender=OrderTransport)
def notify_order_transport_created(sender, instance: OrderTransport, created, **kwargs):
    """A new transport row means the cargo is loaded and on its way — tell the client."""
    if not created:
        return

    transaction.on_commit(
        lambda: notification_service.order_transport_notify.delay(instance.pk)
    )
