from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_file
from django.views.generic import RedirectView

from inquiries import views
from portfolio import api

urlpatterns = [
    path("api/health/", views.health),
    path("api/contact/", views.contact),
    path("api/projects/", api.project_list),
    path("dashboard/", include("dashboard.urls")),
    # uploaded project photos (the folder is created by the dashboard)
    re_path(r"^media/(?P<path>.+)$", serve_file, {"document_root": settings.MEDIA_ROOT}),
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
]

if settings.DEBUG:
    # Development convenience ONLY: also serve the website itself, so
    #   python manage.py runserver   ->   http://127.0.0.1:8000/
    # shows the whole site and the form works without any CORS settings.
    # Only the public site folders are exposed (never the backend folder).
    serve = serve_file

    urlpatterns += [
        re_path(r"^(?P<path>(?:CSS|JS|IMAGES|FONTS|HTML)/.+)$", serve, {"document_root": settings.SITE_DIR}),
        path("", serve, {"path": "index.html", "document_root": settings.SITE_DIR}),
    ]
else:
    # API-only server: the home address goes to the dashboard
    urlpatterns += [path("", RedirectView.as_view(pattern_name="dashboard:overview"))]
