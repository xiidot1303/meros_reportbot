from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from app.resources.openapi import OPENAPI_SPEC
from app.utils.docs_auth import DOCS_LOGIN_URL, can_read_docs, docs_login_required


class DocsLoginView(View):
    """Login for the API documentation only.

    Separate from the admin login: authenticating here does not create admin
    access, and an account without docs access is refused even if it is a valid
    Django user.
    """

    template_name = "docs/login.html"

    def get(self, request, *args, **kwargs):
        if can_read_docs(request.user):
            return redirect(request.GET.get("next") or "/api/docs/")
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        error = None

        if form.is_valid():
            user = form.get_user()
            if can_read_docs(user):
                auth_login(request, user)
                return redirect(request.POST.get("next") or "/api/docs/")
            error = "Этой учётной записи не разрешён доступ к документации."

        return render(
            request,
            self.template_name,
            {"form": form, "access_error": error},
            status=401,
        )


class DocsLogoutView(View):
    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return redirect(DOCS_LOGIN_URL)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


@method_decorator(docs_login_required, name="dispatch")
class OpenAPISchemaView(View):
    """The raw OpenAPI 3.1 document, consumed by the doc renderers below."""

    def get(self, request, *args, **kwargs):
        return JsonResponse(OPENAPI_SPEC, json_dumps_params={"ensure_ascii": False})


@method_decorator(docs_login_required, name="dispatch")
class SwaggerUIView(View):
    """Swagger UI — interactive, with a Try-it-out console."""

    def get(self, request, *args, **kwargs):
        return render(request, "docs/swagger.html")


@method_decorator(docs_login_required, name="dispatch")
class StoplightDocsView(View):
    """Stoplight Elements — three-column reference layout."""

    def get(self, request, *args, **kwargs):
        return render(request, "docs/stoplight.html")
