from django.core.management.base import BaseCommand

from inquiries.emails import send_staff_notification
from inquiries.models import Inquiry


class Command(BaseCommand):
    help = "Re-send the staff email for messages whose notification failed (run it from a daily cron job)."

    def handle(self, *args, **options):
        pending = Inquiry.objects.filter(notified=False).order_by("created_at")
        sent = 0
        for inquiry in pending:
            ok, err = send_staff_notification(inquiry)
            Inquiry.objects.filter(pk=inquiry.pk).update(notified=ok, notify_error=err)
            sent += ok
        self.stdout.write(f"{sent} of {pending.count()} notifications sent.")
