import base64
import binascii
import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.services.payment_service import notify_payment, parse_amount, parse_datetime


def _authenticate(request):
    """Authenticate the caller as a Django user — either an active session or
    HTTP Basic credentials (for the external payment system)."""
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user

    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return None

    try:
        username, _, password = base64.b64decode(header[6:]).decode("utf-8").partition(":")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None

    return authenticate(request, username=username, password=password)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentReceiveView(View):
    """Receives client payments from the external payment system and notifies
    the client's cabinets over the bot. Nothing is stored on this side.

    Auth: Django user via HTTP Basic (or an active session).
    POST {"doc_id": ..., "amount": ..., "datetime": ..., "tin": ..., "purpose": ...}
    """

    def post(self, request, *args, **kwargs):
        user = _authenticate(request)
        if not user or not user.is_active:
            response = JsonResponse({"status": "error", "message": "Unauthorized."}, status=401)
            response["WWW-Authenticate"] = 'Basic realm="payments"'
            return response

        try:
            data = json.loads(request.body or b"{}")
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

        doc_id = data.get("doc_id")
        if not doc_id:
            return JsonResponse({"status": "error", "message": "doc_id is required."}, status=400)

        tin = data.get("tin")
        tin = str(tin).strip() if tin else None

        notified = notify_payment(
            tin=tin,
            amount=parse_amount(data.get("amount")),
            datetime_value=parse_datetime(data.get("datetime")),
            purpose=data.get("purpose"),
        )

        return JsonResponse({
            "status": "success",
            "message": "Payment received.",
            "doc_id": str(doc_id),
            "notified": notified,
        })
