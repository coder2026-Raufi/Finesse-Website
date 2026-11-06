from inquiries.models import Inquiry


def nav(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {"nav_new": Inquiry.objects.filter(status="new").count()}
    return {}
