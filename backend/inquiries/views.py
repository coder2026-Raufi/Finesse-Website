import json
import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .emails import send_staff_notification
from .forms import ContactForm
from .models import Inquiry
from .throttle import client_ip, hash_ip, is_duplicate, is_rate_limited

logger = logging.getLogger(__name__)


def _json(data, status=200):
    resp = JsonResponse(data, status=status)
    resp["Cache-Control"] = "no-store"
    return resp


@require_GET
def health(request):
    """Uptime check: also proves the database answers."""
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
    return _json({"ok": True})


# CSRF protects logged-in browser sessions. This public endpoint has no session;
# it is protected by: JSON-only content type, Origin check (middleware),
# honeypot, rate limit and server-side validation.
@csrf_exempt
@require_POST
def contact(request):
    if request.content_type != "application/json":
        return _json({"ok": False, "error": "json_required"}, status=415)

    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:  # bad JSON or body too large
        return _json({"ok": False, "error": "bad_request"}, status=400)

    form = ContactForm({k: v for k, v in payload.items() if isinstance(v, str)})
    if not form.is_valid():
        # Send machine-readable codes; the website shows its own translated texts.
        errors = {
            field: [e["code"] for e in errs]
            for field, errs in form.errors.get_json_data().items()
        }
        return _json({"ok": False, "error": "validation", "fields": errors}, status=400)

    data = form.cleaned_data
    ip_hash = hash_ip(client_ip(request))

    # Bots fill the hidden field. Pretend success so they don't adapt; store nothing.
    if data["website"]:
        logger.info("Honeypot triggered")
        return _json({"ok": True}, status=201)

    if is_rate_limited(ip_hash):
        resp = _json({"ok": False, "error": "rate_limited"}, status=429)
        resp["Retry-After"] = "3600"
        return resp

    if is_duplicate(ip_hash, data["email"], data["message"]):
        return _json({"ok": True}, status=201)  # a double-click, not a new message

    inquiry = Inquiry.objects.create(
        name=data["name"],
        email=data["email"],
        subject=data["subject"],
        message=data["message"],
        language=data["language"],
        ip_hash=ip_hash,
        user_agent=request.headers.get("User-Agent", "")[:255],
    )

    ok, err = send_staff_notification(inquiry)
    Inquiry.objects.filter(pk=inquiry.pk).update(notified=ok, notify_error=err)

    # The visitor's message is safely stored, so this is a success either way.
    return _json({"ok": True}, status=201)
