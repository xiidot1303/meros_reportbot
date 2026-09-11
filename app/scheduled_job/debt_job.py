"""Daily overdue-payment alerts.

Runs once a day at 14:00. For every client with a linked cabinet it pulls the
current debt list from SmartUp, corrects `overdue_days` by the client's payment
deferment (see `app.services.debt_service`) and splits the result in two:

* rows already past their due date go out as one rich table, the same table
  the debts menu renders;
* a row two days from falling due gets its own message instead — a heads-up
  about a single payment reads better as prose than as a one-row table.
"""

from app.models import Order
from app.services.debt_service import client_deferment_days, debts_needing_alert
from app.services.error_service import notify_on_exception, report_exception
from app.services.notification_service import (
    send_newsletter,
    send_newsletter_rich_message,
)
from app.services.smartup_service import ApiMethods, SmartUpApiClient
from app.services.string_service import payment_debt_string, payment_debts_rich_tables
from bot.models import Cabinet


@notify_on_exception(reraise=False)
def notify_overdue_payments():
    api_client = SmartUpApiClient(ApiMethods.debts_list)

    for client in _clients_with_cabinets():
        # one client's failed debt fetch must not stop everyone else's alerts
        try:
            _notify_client_debts(api_client, client)
        except Exception as exc:
            report_exception(
                exc,
                "app.scheduled_job.debt_job.notify_overdue_payments",
                context={"client": client.name, "external_id": client.external_id},
            )


def _clients_with_cabinets():
    """Every distinct client someone has linked a cabinet to."""
    clients = []
    for cabinet in Cabinet.objects.filter(client__isnull=False).select_related("client"):
        client = cabinet.client
        if client and client.external_id and client not in clients:
            clients.append(client)
    return clients


def _notify_client_debts(api_client: SmartUpApiClient, client):
    debts = api_client.get_debts_by_client(client.external_id)
    if not debts:
        return

    bot_users = _client_bot_users(client)
    if not bot_users:
        return

    alerts = list(debts_needing_alert(debts, client))
    if not alerts:
        return

    overdue = [alert for alert in alerts if alert[0] == "overdue"]
    due_soon = [alert for alert in alerts if alert[0] == "due_soon"]

    deferment_days = client_deferment_days(client)
    for bot_user in bot_users:
        # rendered per user, since both forms are built in their own language
        if overdue:
            for html in payment_debts_rich_tables(
                overdue, deferment_days, user_id=bot_user.user_id
            ):
                send_newsletter_rich_message(bot_user.user_id, html)

        for kind, days_overdue, debt in due_soon:
            text = payment_debt_string(
                kind,
                days_overdue,
                debt,
                order=_find_order(debt),
                user_id=bot_user.user_id,
                deferment_days=deferment_days,
            )
            send_newsletter(bot_user.user_id, text)


def _client_bot_users(client):
    bot_users = []
    seen = set()
    for cabinet in Cabinet.objects.filter(client=client).select_related("bot_user"):
        bot_user = cabinet.bot_user
        if not bot_user or not bot_user.user_id or bot_user.user_id in seen:
            continue
        seen.add(bot_user.user_id)
        bot_users.append(bot_user)
    return bot_users


def _find_order(debt):
    """The local order behind a debt row, when it has been synced."""
    deal_id = debt.get("deal_id")
    if not deal_id:
        return None
    return Order.objects.filter(deal_id=deal_id).first()
