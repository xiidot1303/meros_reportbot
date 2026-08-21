import base64
import binascii
import hashlib

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.http import JsonResponse

# HTTP Basic verifies the password on every request, and Django's default
# PBKDF2 hasher costs ~220ms per verify. External systems poll these endpoints
# with the same credentials every time, so the verified result is cached
# indefinitely, keyed on a hash of the credentials — one slow verify per
# credential instead of one per request.
#
# NOTE: entries never expire, so a rotated password keeps authenticating until
# its key is cleared from the cache. Revoke access by setting is_active=False
# (checked against the DB on every hit, so it takes effect immediately).


def _credential_cache_key(username, password):
    """Key on a salted digest so the raw password never reaches the cache."""
    digest = hashlib.sha256(
        f"{settings.SECRET_KEY}:{username}:{password}".encode("utf-8")
    ).hexdigest()
    return f"api_auth:basic:{digest}"


def _authenticate_basic(request, username, password):
    key = _credential_cache_key(username, password)
    user_id = cache.get(key)

    if user_id is not None:
        # Re-read the user so a deactivated or deleted account stops working
        # immediately instead of lingering until the entry expires.
        user = get_user_model().objects.filter(pk=user_id).first()
        if user and user.is_active:
            return user
        cache.delete(key)
        return None

    user = authenticate(request, username=username, password=password)
    if user is not None:
        cache.set(key, user.pk, timeout=None)  # None == never expire
    return user


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

    return _authenticate_basic(request, username, password)


def unauthorized_response(realm="api"):
    response = JsonResponse({"status": "error", "message": "Unauthorized."}, status=401)
    response["WWW-Authenticate"] = f'Basic realm="{realm}"'
    return response
