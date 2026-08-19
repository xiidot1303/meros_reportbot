from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from app.resources.openapi import OPENAPI_SPEC


@method_decorator(login_required, name="dispatch")
class OpenAPISchemaView(View):
    """The raw OpenAPI 3.1 document, consumed by the doc renderers below."""

    def get(self, request, *args, **kwargs):
        return JsonResponse(OPENAPI_SPEC, json_dumps_params={"ensure_ascii": False})


@method_decorator(login_required, name="dispatch")
class SwaggerUIView(View):
    """Swagger UI — interactive, with a Try-it-out console."""

    def get(self, request, *args, **kwargs):
        return render(request, "docs/swagger.html")


@method_decorator(login_required, name="dispatch")
class StoplightDocsView(View):
    """Stoplight Elements — three-column reference layout."""

    def get(self, request, *args, **kwargs):
        return render(request, "docs/stoplight.html")
