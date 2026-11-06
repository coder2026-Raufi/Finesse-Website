"""Small, dependable spam protection that works across several server processes
because it counts rows in the database (no extra service such as Redis needed)."""
import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Inquiry


def client_ip(request):
    """Real visitor IP. Only trust X-Forwarded-For when NUM_PROXIES says there is
    a reverse proxy of ours in front (otherwise anyone could fake the header)."""
    n = settings.NUM_PROXIES
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if n > 0 and xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if len(parts) >= n:
            return parts[-n]
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def hash_ip(ip):
    return hmac.new(settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()


def is_rate_limited(ip_hash):
    since = timezone.now() - timedelta(minutes=settings.CONTACT_RATE_WINDOW_MIN)
    recent = Inquiry.objects.filter(ip_hash=ip_hash, created_at__gte=since).count()
    return recent >= settings.CONTACT_RATE_LIMIT


def is_duplicate(ip_hash, email, message):
    """Same person sending the identical message again within a day."""
    since = timezone.now() - timedelta(days=1)
    return Inquiry.objects.filter(
        ip_hash=ip_hash, email__iexact=email, message=message, created_at__gte=since
    ).exists()
