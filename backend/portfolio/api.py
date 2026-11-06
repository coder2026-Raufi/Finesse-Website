from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import LANGS, Project


def serialize(p, request):
    return {
        "id": p.pk,
        "category": p.category,
        "year": p.year,
        "duration_months": p.duration_months,
        "client": p.client,
        "image": request.build_absolute_uri(p.image.url) if p.image else None,
        "title": {l: p.text("title", l) for l in LANGS},
        "description": {l: p.text("description", l) for l in LANGS},
    }


@require_GET
def project_list(request):
    """Public: only projects marked 'Visible on website'."""
    qs = Project.objects.filter(is_published=True)
    resp = JsonResponse({"projects": [serialize(p, request) for p in qs]})
    resp["Cache-Control"] = "public, max-age=30"  # new projects appear within seconds
    return resp
