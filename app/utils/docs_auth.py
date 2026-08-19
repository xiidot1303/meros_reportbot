"""Access control for the API documentation.

Deliberately separate from the Django admin: a docs user is a plain, non-staff
account in the `api_docs` group. They can read the docs and nothing else — no
admin, no models. Superusers are allowed through as a convenience.
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url


DOCS_GROUP = "api_docs"
DOCS_LOGIN_URL = "/api/login/"


def can_read_docs(user):
    if not (user and user.is_authenticated and user.is_active):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=DOCS_GROUP).exists()


def docs_login_required(view_func):
    """Gate a view on docs access, sending everyone else to the docs login page.

    Anonymous users are redirected to log in. An authenticated user who lacks
    docs access is also sent there — never to the admin login — so an admin
    session alone does not unlock the docs, and vice versa.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if can_read_docs(request.user):
            return view_func(request, *args, **kwargs)
        return redirect_to_login(
            request.get_full_path(), resolve_url(DOCS_LOGIN_URL), "next"
        )

    return wrapper
