"""Date wording shared by the bot handlers and the app-side jobs."""


def russian_days_plural(days: int) -> str:
    """день / дня / дней for a day count.

    Russian picks the form from the last digit, except in the teens where it is
    always "дней" (11 дней, not 11 день).
    """
    if 11 <= days % 100 <= 14:
        return "дней"
    last = days % 10
    if last == 1:
        return "день"
    if last in (2, 3, 4):
        return "дня"
    return "дней"


def format_doc_date(doc_date) -> str:
    """DD.MM.YYYY, the format every other date in the bot uses."""
    if not doc_date:
        return "—"
    return doc_date.strftime("%d.%m.%Y")
