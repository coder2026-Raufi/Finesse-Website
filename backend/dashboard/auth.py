from functools import wraps

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse

from inquiries.throttle import client_ip, hash_ip

MAX_FAILS = 5
LOCK_SECONDS = 15 * 60


def staff_required(view):
    @wraps(view)
    @login_required(login_url="dashboard:login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


class ThrottledLoginView(auth_views.LoginView):
    """Normal login, but 5 wrong passwords lock that visitor out for 15 minutes
    (stops password guessing)."""

    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        key = "login-fail:" + hash_ip(client_ip(request))
        if cache.get(key, 0) >= MAX_FAILS:
            form = self.get_form()
            return TemplateResponse(request, self.template_name, {"form": form, "locked": True}, status=429)
        response = super().post(request, *args, **kwargs)
        if response.status_code == 302:
            cache.delete(key)
        else:
            cache.set(key, cache.get(key, 0) + 1, LOCK_SECONDS)
        return response
