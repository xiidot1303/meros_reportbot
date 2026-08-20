import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.services.payment_service import notify_payment, parse_amount, parse_datetime
from app.services.error_service import report_exception
from app.utils.api_auth import authenticate_api_request, unauthorized_response


@method_decorator(csrf_exempt, name="dispatch")
class PaymentReceiveView(View):
    """Receives client payments from the external payment system and notifies
    the client's cabinets over the bot. Nothing is stored on this side.

    Auth: Django user via HTTP Basic (or an active session).
    POST {"doc_id": ..., "amount": ..., "datetime": ..., "tin": ..., "purpose": ...}
    """

    def post(self, request, *args, **kwargs):
        user = authenticate_api_request(request)
        if not user or not user.is_active:
            return unauthorized_response("payments")

        try:
            data = json.loads(request.body or b"{}")
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

        doc_id = data.get("doc_id")
        if not doc_id:
            return JsonResponse({"status": "error", "message": "doc_id is required."}, status=400)

        tin = data.get("tin")
        tin = str(tin).strip() if tin else None

        try:
            notified = notify_payment(
                tin=tin,
                amount=parse_amount(data.get("amount")),
                datetime_value=parse_datetime(data.get("datetime")),
                purpose=data.get("purpose"),
            )
        except Exception as exc:
            report_exception(
                exc,
                "app.views.payment.PaymentReceiveView",
                context={"doc_id": doc_id, "tin": tin},
            )
            return JsonResponse(
                {"status": "error", "message": "Internal error."}, status=500
            )

        return JsonResponse({
            "status": "success",
            "message": "Payment received.",
            "doc_id": str(doc_id),
            "notified": notified,
        })
