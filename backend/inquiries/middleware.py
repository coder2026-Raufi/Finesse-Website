"""CORS + origin check for the /api/ endpoints.

The website (HTML) may be hosted on a different domain than this API.
Browsers then block the request unless the API says "that origin is allowed".
We also refuse requests whose Origin is not on the list (blocks other sites
from posting to our form from a visitor's browser)."""
from urllib.parse import urlsplit

from django.conf import settings
from django.http import JsonResponse


def _allowed(request, origin):
    if origin in settings.CORS_ALLOWED_ORIGINS:
        return True
    parts = urlsplit(origin)
    # same-origin (site served by this same server, e.g. during development)
    return parts.netloc == request.get_host() and parts.scheme == request.scheme


class ApiOriginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        origin = request.headers.get("Origin")
        ok = bool(origin) and _allowed(request, origin)

        if origin and not ok:
            return JsonResponse({"ok": False, "error": "origin_not_allowed"}, status=403)

        if request.method == "OPTIONS":  # browser "preflight" check
            from django.http import HttpResponse

            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if ok:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type"
            response["Access-Control-Max-Age"] = "600"
            response["Vary"] = "Origin"
        return response
