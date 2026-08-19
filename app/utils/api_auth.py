import base64
import binascii

from django.contrib.auth import authenticate
from django.http import JsonResponse


def authenticate_api_request(request):
    """Authenticate an inbound API caller as a Django user — either an active
    session or HTTP Basic credentials (for external systems)."""
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


def unauthorized_response(realm="api"):
    response = JsonResponse({"status": "error", "message": "Unauthorized."}, status=401)
    response["WWW-Authenticate"] = f'Basic realm="{realm}"'
    return response
