import requests
from django.core.cache import cache

from app.services.error_service import notify_on_exception, report_exception
from config import SOLIQ_BASE_URL, SOLIQ_PASSWORD, SOLIQ_USERNAME

SOLIQ_TOKEN_CACHE_KEY = "soliq:auth_token"
SOLIQ_TOKEN_CACHE_TIMEOUT = 28000


def get_cached_token():
    cached = cache.get(SOLIQ_TOKEN_CACHE_KEY)
    if cached and isinstance(cached, dict) and cached.get("accessToken") and cached.get("platformId"):
        return {"accessToken": cached["accessToken"], "platformId": cached["platformId"]}
    return {}


def set_cached_token(token_payload):
    normalized = {
        "accessToken": token_payload.get("accessToken") or token_payload.get("access_token"),
        "platformId": token_payload.get("platformId") or token_payload.get("platform_id"),
    }
    cache.set(SOLIQ_TOKEN_CACHE_KEY, normalized, SOLIQ_TOKEN_CACHE_TIMEOUT)
    return normalized


def clear_cached_token():
    cache.delete(SOLIQ_TOKEN_CACHE_KEY)


def _looks_like_auth_error(response):
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        return True

    text = getattr(response, "text", "") or ""
    lower_text = text.lower()
    auth_markers = [
        "unauthorized",
        "authorization",
        "token",
        "forbidden",
        "expired",
        "invalid",
        "auth",
    ]
    return any(marker in lower_text for marker in auth_markers)


@notify_on_exception
def authenticate(username=None, password=None):
    login_username = username or SOLIQ_USERNAME
    login_password = password or SOLIQ_PASSWORD

    if not login_username or not login_password:
        raise ValueError("Soliq credentials are not configured. Set SOLIQ_USERNAME and SOLIQ_PASSWORD.")

    response = requests.post(
        f"{SOLIQ_BASE_URL}/api/login",
        headers={"accept": "application/json", "content-type": "application/json"},
        json={"username": login_username, "password": login_password},
        timeout=30,
    )

    if response.status_code != 201:
        error_payload = response.text
        try:
            error_payload = response.json()
        except ValueError:
            pass
        raise PermissionError(f"Soliq authentication failed ({response.status_code}): {error_payload}")

    payload = response.json()
    data = payload.get("data", {})
    access_token = data.get("token", {}).get("access_token")
    platform_id = data.get("client_platform", {}).get("id")

    if not access_token or not platform_id:
        raise ValueError(f"Soliq login response is missing access_token/platform_id: {payload}")

    token = {"accessToken": access_token, "platformId": platform_id}
    set_cached_token(token)
    return token


def get_valid_token(force_refresh=False):
    if force_refresh:
        return authenticate()

    cached = get_cached_token()
    if not cached:
        return authenticate()

    return cached


@notify_on_exception
def soliqRequest(path, options=None):
    options = dict(options or {})
    method = str(options.get("method", "get")).lower()
    token = get_valid_token(force_refresh=False)
    headers = {
        "authorization": f"Bearer {token['accessToken']}",
        "platform-id": str(token["platformId"]),
        "accept": options.get("accept", "*/*"),
        "connection": options.get("connection", "keep-alive"),
    }
    request_headers = options.get("headers") or {}
    headers.update(request_headers)

    request_kwargs = {
        "method": method,
        "url": f"{SOLIQ_BASE_URL}{path}",
        "headers": headers,
        "timeout": options.get("timeout", 30),
        "params": options.get("params"),
        "json": options.get("json"),
        "data": options.get("data"),
    }

    response = requests.request(**request_kwargs)

    if response.status_code in (401, 403) or _looks_like_auth_error(response):
        refreshed = authenticate()
        request_kwargs["headers"] = {
            "authorization": f"Bearer {refreshed['accessToken']}",
            "platform-id": str(refreshed["platformId"]),
            "accept": options.get("accept", "*/*"),
            "connection": options.get("connection", "keep-alive"),
            **(options.get("headers") or {}),
        }
        response = requests.request(**request_kwargs)

    if response.status_code in (401, 403) or _looks_like_auth_error(response):
        raise PermissionError(f"Soliq request failed with auth error: {response.text}")

    try:
        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload
    except (ValueError, TypeError):
        pass

    if response.content:
        headers = getattr(response, "headers", None) or {}
        content_type = ""
        if hasattr(headers, "get"):
            content_type = str(headers.get("content-type", "") or "")
        elif isinstance(headers, dict):
            content_type = str(headers.get("content-type", "") or "")

        if "application/json" in content_type.lower():
            try:
                return response.json()
            except ValueError:
                pass
        if "text/plain" in content_type.lower() and response.text.strip().startswith("{"):
            try:
                return response.json()
            except ValueError:
                pass
        if isinstance(response.text, str) and response.text.strip().startswith("{"):
            try:
                return response.json()
            except ValueError:
                pass
        return response.content
    return {}


PENDING_DOC_STATUS = "header_receive,pending"


@notify_on_exception
def fetch_pending_documents(client, limit=100) -> list:
    """Fetch the client's unaccepted (pending) factura documents from Soliq.

    The request is filtered server-side to ``header_receive,pending``, so the
    response only ever contains documents the client has not accepted yet.
    """
    if not client or not client.tin:
        return []

    response = soliqRequest(
        "/api/v3/lists",
        {
            "method": "get",
            "params": [
                ("path", "sent"),
                ("offset", 0),
                ("limit", limit),
                ("docStatus", ""),
                ("folderId", 0),
                ("docType", "factura"),
                ("tin", client.tin),
                ("docStatus", PENDING_DOC_STATUS),
            ],
        },
    )
    if not isinstance(response, dict):
        return []
    return response.get("data", {}).get("documents", []) or []


def download_factura_pdf(doc_id):
    """Download the PDF file for a factura document from Soliq."""
    if not doc_id:
        return None

    try:
        response = soliqRequest(
            "/api/get-pdf",
            {
                "method": "get",
                "params": [("doc_id", doc_id), ("doc_type", "factura")],
                "timeout": 60,
            },
        )
        if isinstance(response, bytes):
            return response
        return None
    except Exception as exc:
        report_exception(
            exc,
            "app.services.soliq_service.download_factura_pdf",
            context={"doc_id": doc_id},
        )
        return None
