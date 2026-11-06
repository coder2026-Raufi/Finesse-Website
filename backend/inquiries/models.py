from django.db import models


class Inquiry(models.Model):
    """One message sent through the website's contact form."""

    class Subject(models.TextChoices):
        RESEARCH = "research", "Research & Analysis"
        ME = "me", "Monitoring & Evaluation"
        CAPACITY = "capacity", "Capacity Development & Training"
        MGMT = "mgmt", "Management Consulting"
        GENERAL = "general", "General inquiry"

    class Status(models.TextChoices):
        NEW = "new", "New"
        READ = "read", "Read"
        REPLIED = "replied", "Replied"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=40)
    email = models.EmailField(max_length=60)
    subject = models.CharField(max_length=20, choices=Subject.choices)
    message = models.TextField(max_length=5000)
    language = models.CharField(max_length=2, default="en")  # language the visitor was using

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)

    # Privacy: we keep a one-way hash of the IP (enough to rate-limit), not the IP itself.
    ip_hash = models.CharField(max_length=64, db_index=True, editable=False)
    user_agent = models.CharField(max_length=255, blank=True, editable=False)

    # Was the staff email delivered? If not, the message is still safe in the database.
    notified = models.BooleanField(default=False)
    notify_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "inquiry"
        verbose_name_plural = "inquiries"

    def __str__(self):
        return f"{self.name} — {self.get_subject_display()} ({self.created_at:%Y-%m-%d})"
