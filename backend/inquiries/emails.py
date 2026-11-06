import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def send_staff_notification(inquiry):
    """Email the Finesse team. Returns (ok, error_text). Never raises: the
    message is already saved, so an email problem must not lose it."""
    subject = f"[Finesse website] {inquiry.get_subject_display()} - {inquiry.name}"
    body = (
        f"New message from the Finesse website\n"
        f"{'-' * 40}\n"
        f"Name:     {inquiry.name}\n"
        f"Email:    {inquiry.email}\n"
        f"Subject:  {inquiry.get_subject_display()}\n"
        f"Language: {inquiry.language}\n"
        f"Received: {inquiry.created_at:%Y-%m-%d %H:%M} (Kabul time)\n"
        f"{'-' * 40}\n\n"
        f"{inquiry.message}\n\n"
        f"{'-' * 40}\n"
        f"Just press Reply: the answer goes to {inquiry.email}."
    )
    try:
        EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.CONTACT_NOTIFY_TO,
            reply_to=[inquiry.email],  # Reply goes to the visitor, not to ourselves
        ).send(fail_silently=False)
        return True, ""
    except Exception as exc:  # network down, wrong password, ...
        logger.exception("Could not send notification for inquiry %s", inquiry.pk)
        return False, f"{type(exc).__name__}: {exc}"[:500]
