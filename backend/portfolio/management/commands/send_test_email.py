from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send one test email to check your email settings:  python manage.py send_test_email you@example.com"

    def add_arguments(self, parser):
        parser.add_argument("to")

    def handle(self, *args, to, **options):
        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
        if "console" in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                "No email password is set, so the email is only PRINTED below (not really sent). "
                "Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env."))
        try:
            send_mail("Finesse website: test email", "If you can read this, email works.",
                      settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
        except Exception as exc:
            raise CommandError(f"Sending failed: {type(exc).__name__}: {exc}")
        self.stdout.write(self.style.SUCCESS("Done."))
