"""Overdue-payment detection for the debts SmartUp returns.

SmartUp's `overdue_days` counts from the delivery, not from the moment the
payment actually falls due — the client's payment deferment has to be
subtracted before the number means anything. Everything here works on that
corrected figure.
"""

from app.models import Client


# How many days ahead of the due date the client gets a heads-up.
DUE_SOON_DAYS = 2


def client_deferment_days(client: Client) -> int:
    """The deferment to charge this client's debts against.

    `deferment_days` is the contractual figure; `secondary_deferment_days` is
    the fallback SmartUp fills in for clients without one. A client with
    neither gets 0 — their payment is due on delivery.
    """
    if client.deferment_days is not None:
        return client.deferment_days
    if client.secondary_deferment_days is not None:
        return client.secondary_deferment_days
    return 0


def parse_debt_row(row):
    """One `get_debts_by_client` row as a dict.

    The API answers with positional lists in the order the request's `column`
    list asked for them, so a row that is short or malformed is dropped rather
    than unpacked blindly.
    """
    if not row or len(row) < 5:
        return None

    deal_id, expiry_date, debt_amount, overdue_days, delivery_number = row[:5]
    return {
        "deal_id": str(deal_id) if deal_id is not None else None,
        "expiry_date": expiry_date,
        "debt_amount": debt_amount,
        "overdue_days": _to_int(overdue_days),
        "delivery_number": delivery_number,
    }


def _to_int(value):
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def effective_overdue_days(raw_overdue_days, deferment_days: int):
    """Days past the real due date — negative while the payment is still due.

    SmartUp counts `overdue_days` from delivery, so the deferment the client
    was granted has to come off before the number describes an actual
    overdue.
    """
    if raw_overdue_days is None:
        return None
    return raw_overdue_days - deferment_days


def classify_debt(debt, deferment_days: int):
    """Whether this debt warrants an alert today, and which one.

    Returns "overdue" for a payment past its due date (alerted every day),
    "due_soon" exactly `DUE_SOON_DAYS` out (alerted once), and None for a debt
    that needs no message.
    """
    overdue = effective_overdue_days(debt.get("overdue_days"), deferment_days)
    if overdue is None:
        return None, None

    if overdue > 0:
        return "overdue", overdue
    if overdue == -DUE_SOON_DAYS:
        return "due_soon", overdue
    return None, overdue


def debts_needing_alert(debts, client: Client):
    """The rows of a client's debt list that should be messaged today.

    Yields `(kind, days_overdue, debt)` so the caller only has to pick the
    wording — the deferment arithmetic is already applied.
    """
    deferment_days = client_deferment_days(client)

    for row in debts or []:
        debt = parse_debt_row(row)
        if not debt:
            continue

        kind, overdue = classify_debt(debt, deferment_days)
        if kind:
            yield kind, overdue, debt
