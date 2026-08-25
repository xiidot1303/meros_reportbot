"""Which clients a phone number may open a cabinet for.

Two independent grants exist and they merge into one list:

* **owner** — the phone matches `app.Client.phone`, the number SmartUp holds
  for the organization. One number can own several clients; that is the
  pre-existing multi-cabinet behaviour.
* **staff** — an owner listed the phone in `bot.ClientStaff` for one of the
  clients they own.

Both are keyed on the phone number, so somebody who directs their own
organizations and is staff at someone else's simply gets the union.
"""

from asgiref.sync import sync_to_async
from django.db.models import Q

from app.models import Client
from bot.models import Cabinet, ClientStaff


def normalize_phone(phone):
    """Bring a phone to the `+998XXXXXXXXX` shape `Client.phone` is stored in.

    Mirrors the normalization `app.services.client_service` applies to the
    SmartUp payload, so a contact shared through Telegram ("+998 90 123-45-67")
    and a typed one ("901234567") land on the same string.
    """
    if not phone:
        return None

    phone = str(phone).strip()
    for char in " -()., :":
        phone = phone.replace(char, "")
    if "+998998" in phone and len(phone) == 16:
        phone = phone.replace("+998998", "+998")
    phone = phone.replace("+", "")
    if len(phone) == 9:
        phone = "998" + phone
    phone = phone[:12]
    if not phone.isdigit():
        return None
    return "+" + phone


def phone_tail(phone):
    """The last 9 digits — the part that identifies the subscriber.

    Legacy `Bot_user.phone` values were saved verbatim from Telegram and are
    not all normalized, so lookups compare on the tail rather than demanding
    an exact match.
    """
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    return normalized[-9:]


def accessible_clients(phone):
    """Every client the phone may open, owned and staffed alike."""
    tail = phone_tail(phone)
    if not tail:
        return Client.objects.none()

    staff_client_ids = ClientStaff.objects.filter(
        phone__endswith=tail).values_list("client_id", flat=True)
    return Client.objects.filter(
        Q(phone__endswith=tail) | Q(id__in=staff_client_ids)
    ).distinct()


def owned_clients(phone):
    """Only the clients the phone owns — the ones whose staff it may manage."""
    tail = phone_tail(phone)
    if not tail:
        return Client.objects.none()
    return Client.objects.filter(phone__endswith=tail)


def is_owner(phone, client):
    """Whether the phone owns this client, i.e. may add or remove its staff."""
    tail = phone_tail(phone)
    if not tail or not client or not client.phone:
        return False
    client_tail = phone_tail(client.phone)
    return bool(client_tail) and client_tail == tail


def has_access(phone, client):
    tail = phone_tail(phone)
    if not tail or not client:
        return False
    if is_owner(phone, client):
        return True
    return ClientStaff.objects.filter(client=client, phone__endswith=tail).exists()


def revoke_staff(client, phone):
    """Drop a grant and close the cabinet it was holding open.

    Deleting the `Cabinet` stops notifications immediately; without it the
    revoked member would keep receiving them until their next interaction.
    Owners are never revoked this way — their access comes from `Client.phone`.
    """
    tail = phone_tail(phone)
    if not tail:
        return 0

    deleted, _ = ClientStaff.objects.filter(
        client=client, phone__endswith=tail).delete()
    if deleted:
        Cabinet.objects.filter(
            client=client, bot_user__phone__endswith=tail).delete()
    return deleted


# async wrappers — the bot handlers run on the event loop
accessible_clients_async = sync_to_async(accessible_clients)
is_owner_async = sync_to_async(is_owner)
has_access_async = sync_to_async(has_access)
revoke_staff_async = sync_to_async(revoke_staff)
