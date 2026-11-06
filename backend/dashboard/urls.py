from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .auth import ThrottledLoginView

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("login/", ThrottledLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page=reverse_lazy("dashboard:login")), name="logout"),
    path("messages/", views.message_list, name="messages"),
    path("messages/<int:pk>/", views.message_detail, name="message"),
    path("messages/<int:pk>/status/", views.message_status, name="message_status"),
    path("messages/<int:pk>/delete/", views.message_delete, name="message_delete"),
    path("projects/", views.project_list, name="projects"),
    path("projects/new/", views.project_new, name="project_new"),
    path("projects/samples/", views.project_load_samples, name="project_samples"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/toggle/", views.project_toggle, name="project_toggle"),
]
