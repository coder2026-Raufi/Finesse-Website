from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from inquiries.models import Inquiry
from portfolio.models import Project
from portfolio.samples import load_samples

from .auth import staff_required
from .forms import ProjectForm


def _email_is_real():
    return "smtp" in settings.EMAIL_BACKEND


@staff_required
def overview(request):
    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    per_day = {
        r["d"]: r["n"]
        for r in Inquiry.objects.filter(created_at__date__gte=days[0])
        .annotate(d=TruncDate("created_at")).values("d").annotate(n=Count("id"))
    }
    counts = [per_day.get(d, 0) for d in days]
    top = max(counts) or 1
    chart = [{"label": d.strftime("%d %b"), "n": n, "h": max(4, round(n / top * 100)) if n else 2}
             for d, n in zip(days, counts)]

    total = Inquiry.objects.count()
    by_subject = [
        {"label": label, "n": n, "w": round(n / total * 100) if total else 0}
        for value, label in Inquiry.Subject.choices
        for n in [Inquiry.objects.filter(subject=value).count()]
    ]
    ctx = {
        "total": total,
        "new_count": Inquiry.objects.filter(status="new").count(),
        "week": Inquiry.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
        "projects_live": Project.objects.filter(is_published=True).count(),
        "projects_all": Project.objects.count(),
        "chart": chart,
        "by_subject": by_subject,
        "recent": Inquiry.objects.all()[:6],
        "email_real": _email_is_real(),
        "unsent": Inquiry.objects.filter(notified=False).count(),
    }
    ctx["active"] = "overview"
    return render(request, "dashboard/overview.html", ctx)


@staff_required
def message_list(request):
    qs = Inquiry.objects.all()
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    if status in dict(Inquiry.Status.choices):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/messages.html", {
        "active": "messages",
        "page": page, "status": status, "q": q, "statuses": Inquiry.Status.choices,
        "counts": {s: Inquiry.objects.filter(status=s).count() for s, _ in Inquiry.Status.choices},
    })


@staff_required
def message_detail(request, pk):
    obj = get_object_or_404(Inquiry, pk=pk)
    if obj.status == Inquiry.Status.NEW:
        Inquiry.objects.filter(pk=pk).update(status=Inquiry.Status.READ)
        obj.status = Inquiry.Status.READ
    return render(request, "dashboard/message_detail.html", {"active": "messages", "m": obj, "statuses": Inquiry.Status.choices})


@staff_required
@require_POST
def message_status(request, pk):
    new = request.POST.get("status")
    if new in dict(Inquiry.Status.choices):
        Inquiry.objects.filter(pk=pk).update(status=new)
        messages.success(request, "Message updated.")
    return redirect(request.POST.get("next") or "dashboard:messages")


@staff_required
@require_POST
def message_delete(request, pk):
    get_object_or_404(Inquiry, pk=pk).delete()
    messages.success(request, "Message deleted.")
    return redirect("dashboard:messages")


# ------------------------------------------------------------ projects
@staff_required
def project_list(request):
    return render(request, "dashboard/projects.html", {"active": "projects", "projects": Project.objects.all()})


@staff_required
def project_new(request):
    form = ProjectForm(request.POST or None, request.FILES or None, initial={"year": timezone.localdate().year})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added. It is now on the website." if form.instance.is_published
                         else "Project saved (hidden from the website).")
        return redirect("dashboard:projects")
    return render(request, "dashboard/project_form.html", {"active": "projects", "form": form, "title": "Add a project"})


@staff_required
def project_edit(request, pk):
    obj = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated.")
        return redirect("dashboard:projects")
    return render(request, "dashboard/project_form.html", {"active": "projects", "form": form, "title": "Edit project", "obj": obj})


@staff_required
@require_POST
def project_delete(request, pk):
    obj = get_object_or_404(Project, pk=pk)
    name = obj.title_en
    obj.delete()
    messages.success(request, f"“{name}” was deleted.")
    return redirect("dashboard:projects")


@staff_required
@require_POST
def project_toggle(request, pk):
    obj = get_object_or_404(Project, pk=pk)
    obj.is_published = not obj.is_published
    obj.save(update_fields=["is_published", "updated_at"])
    messages.success(request, "Now visible on the website." if obj.is_published else "Hidden from the website.")
    return redirect("dashboard:projects")


@staff_required
@require_POST
def project_load_samples(request):
    if Project.objects.exists():
        messages.error(request, "You already have projects, so nothing was added.")
    else:
        messages.success(request, f"{load_samples()} sample projects added. Edit or delete them as you like.")
    return redirect("dashboard:projects")
