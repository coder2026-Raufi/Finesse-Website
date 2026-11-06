import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Inquiry

admin.site.site_header = "Finesse — Website Administration"
admin.site.site_title = "Finesse Admin"
admin.site.index_title = "Messages from the website"


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "email", "subject", "status", "notified")
    list_filter = ("status", "subject", "notified", "language", "created_at")
    search_fields = ("name", "email", "message")
    date_hierarchy = "created_at"
    list_per_page = 50
    actions = ["mark_read", "mark_replied", "mark_archived", "export_csv"]

    # Staff may change only the status. The visitor's words are never editable.
    readonly_fields = (
        "name", "email_link", "subject", "message", "language", "created_at",
        "notified", "notify_error", "user_agent",
    )
    fields = (
        "status", "name", "email_link", "subject", "message", "language",
        "created_at", "notified", "notify_error", "user_agent",
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Email (click to reply)")
    def email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.email)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Opening a new message marks it as read.
        obj = self.get_object(request, object_id)
        if obj and obj.status == Inquiry.Status.NEW and request.method == "GET":
            Inquiry.objects.filter(pk=obj.pk).update(status=Inquiry.Status.READ)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        queryset.update(status=Inquiry.Status.READ)

    @admin.action(description="Mark selected as replied")
    def mark_replied(self, request, queryset):
        queryset.update(status=Inquiry.Status.REPLIED)

    @admin.action(description="Archive selected")
    def mark_archived(self, request, queryset):
        queryset.update(status=Inquiry.Status.ARCHIVED)

    @admin.action(description="Export selected to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="finesse-inquiries.csv"'
        response.write("\ufeff")  # so Excel reads Persian / Pashto / Arabic correctly
        w = csv.writer(response)
        w.writerow(["Date", "Name", "Email", "Subject", "Status", "Language", "Message"])
        for i in queryset:
            def safe(v):  # stop spreadsheet formula injection (=, +, -, @)
                v = str(v)
                return "'" + v if v[:1] in ("=", "+", "-", "@") else v
            w.writerow([
                i.created_at.strftime("%Y-%m-%d %H:%M"), safe(i.name), safe(i.email),
                i.get_subject_display(), i.get_status_display(), i.language, safe(i.message),
            ])
        return response
