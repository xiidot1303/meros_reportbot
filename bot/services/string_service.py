from bot.bot import *
from app.models import Order, Client
from app.utils import format_number


async def order_history_string(context: CustomContext, client: Client):
    result = ""
    async for order in Order.objects.filter(client=client):
        text = (
            f"{context.words.order_no} {order.deal_id}"
            f"{context.words.order_history_info}".format(
                delivery_date=order.delivery_date.strftime("%d.%m.%Y"),
                total_amount=format_number(round(float(order.total_amount)))
            )
        )
        if order.status:
            text += f"🔸 {context.words.status}: {Order.get_status_label(order.status)}"

        result += (
            f"{text}" \
            "\n\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        )

    return result


async def completed_orders_history_string(context: CustomContext, orders):
    result = ""
    for order in orders:
        text = (
            f"{context.words.order_no} {order.deal_id}"
            f"{context.words.order_history_info}".format(
                delivery_date=order.delivery_date.strftime("%d.%m.%Y"),
                total_amount=format_number(round(float(order.total_amount)))
            )
        )
        result += (
            f"{text}" \
            "\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        )

    return result


async def debts_history_string(context: CustomContext, debts):
    if not debts:
        return [context.words.no_debts_found]

    def _format_debt_amount(raw_value):
        value = float(raw_value)
        return format_number(round(value, 2))

    def _build_table(table_rows):
        headers = [
            "Срок",
            "Сумма задолженности",
            "Дни просрочки",
            "Номер ТТН",
        ]
        widths = [len(head) for head in headers]
        for row in table_rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        separator = "+-" + "-+-".join("-" * w for w in widths) + "-+"
        header_line = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
        body_lines = [
            "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |"
            for row in table_rows
        ]

        return "\n".join([
            separator,
            header_line,
            separator,
            *body_lines,
            separator,
        ])

    normalized_rows = []
    total_amount = 0.0
    for debt in debts:
        _, expiry_date, debt_amount, overdue_days, delivery_number = debt
        total_amount += float(debt_amount)
        normalized_rows.append([
            str(expiry_date),
            _format_debt_amount(debt_amount),
            str(overdue_days),
            str(delivery_number),
        ])

    total_amount_text = format_number(round(total_amount, 2))
    result_messages = []
    chunk_size = 15
    chunk_number = 0
    for i in range(0, len(normalized_rows), chunk_size):
        chunk_number += 1
        chunk = normalized_rows[i:i + chunk_size]
        table_text = _build_table(chunk)

        prefix = ""
        if chunk_number == 1:
            prefix = (
                f"{context.words.total_debt_amount}".format(amount=total_amount_text)
                + "\n"
                + f"{context.words.total_debt_rows}".format(count=len(normalized_rows))
                + "\n\n"
            )

        result_messages.append(prefix + f"<pre>{table_text}</pre>")

    return result_messages


async def debts_history_rich_html(context: CustomContext, debts):
    if not debts:
        return []

    normalized_rows = []
    total_amount = 0.0
    for debt in debts:
        _, expiry_date, debt_amount, overdue_days, delivery_number = debt
        total_amount += float(debt_amount)
        normalized_rows.append([
            str(expiry_date),
            format_number(round(float(debt_amount), 2)),
            str(overdue_days),
            str(delivery_number),
        ])

    total_amount_text = format_number(round(total_amount, 2))
    chunk_size = 40
    result_html = []

    for chunk_index, i in enumerate(range(0, len(normalized_rows), chunk_size), start=1):
        chunk = normalized_rows[i:i + chunk_size]
        rows_html = ""
        for row in chunk:
            rows_html += (
                "<tr>"
                f"<td>{row[0]}</td>"
                f"<td>{row[1]}</td>"
                f"<td>{row[2]}</td>"
                f"<td>{row[3]}</td>"
                "</tr>"
            )

        summary_html = ""
        if chunk_index == 1:
            summary_html = (
                f"{context.words.total_debt_amount}".format(amount=total_amount_text)
                + "<br>"
                + f"{context.words.total_debt_rows}".format(count=len(normalized_rows))
                + "<br><br>"
            )

        table_html = (
            f"{summary_html}"
            "<table border=\"1\">"
            "<tr>"
            "<th>Срок</th>"
            "<th>Сумма задолженности</th>"
            "<th>Дни просрочки</th>"
            "<th>Номер ТТН</th>"
            "</tr>"
            f"{rows_html}"
            "</table>"
        )
        result_html.append(table_html)

    return result_html
