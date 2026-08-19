import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.services.transport_service import save_order_transport
from app.utils.api_auth import authenticate_api_request, unauthorized_response


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


@method_decorator(csrf_exempt, name="dispatch")
class OrderTransportView(View):
    """Receives the car/driver assigned to an order from the external system.

    Auth: Django user via HTTP Basic (or an active session).
    POST {"order_id": ..., "car_model": ..., "car_brand": ...,
          "car_autonum": ..., "firstname": ..., "lastname": ...}
    """

    def post(self, request, *args, **kwargs):
        user = authenticate_api_request(request)
        if not user or not user.is_active:
            return unauthorized_response("orders")

        try:
            data = json.loads(request.body or b"{}")
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

        order_id = _clean(data.get("order_id"))
        if not order_id:
            return JsonResponse(
                {"status": "error", "message": "order_id is required."}, status=400
            )

        transport, created = save_order_transport(
            order_id=order_id,
            car_model=_clean(data.get("car_model")),
            car_brand=_clean(data.get("car_brand")),
            car_autonum=_clean(data.get("car_autonum")),
            firstname=_clean(data.get("firstname")),
            lastname=_clean(data.get("lastname")),
        )

        return JsonResponse({
            "status": "success",
            "message": "Transport saved." if created else "Transport updated.",
            "transport_id": transport.id,
            "order_id": order_id,
            "order_matched": transport.order_id is not None,
            "created": created,
        })
