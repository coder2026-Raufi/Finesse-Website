from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

LANGS = ("en", "fa", "ps", "ar")


class Project(models.Model):
    """One project shown on the website's Projects page."""

    class Category(models.TextChoices):
        RESEARCH = "research", "Research"
        MONITORING = "monitoring", "Monitoring & Evaluation"
        CAPACITY = "capacity", "Capacity Development"
        CONSULTING = "consulting", "Management Consulting"
        STRATEGY = "strategy", "Strategy"

    class Client(models.TextChoices):
        DEV = "dev", "Development partner"
        NGO = "ngo", "NGO"
        GOV = "gov", "Government"
        BIZ = "biz", "Private sector"

    # Text in 4 languages. English is required; if another language is empty,
    # the website falls back to the English text.
    title_en = models.CharField("Title (English)", max_length=120)
    title_fa = models.CharField("Title (Persian)", max_length=120, blank=True)
    title_ps = models.CharField("Title (Pashto)", max_length=120, blank=True)
    title_ar = models.CharField("Title (Arabic)", max_length=120, blank=True)

    description_en = models.TextField("Description (English)", max_length=1000)
    description_fa = models.TextField("Description (Persian)", max_length=1000, blank=True)
    description_ps = models.TextField("Description (Pashto)", max_length=1000, blank=True)
    description_ar = models.TextField("Description (Arabic)", max_length=1000, blank=True)

    category = models.CharField(max_length=12, choices=Category.choices)
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    duration_months = models.PositiveSmallIntegerField(
        "Duration (months)", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(240)]
    )
    client = models.CharField(max_length=4, choices=Client.choices, blank=True)
    image = models.ImageField(upload_to="projects/", blank=True)

    is_published = models.BooleanField("Visible on website", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-id"]

    def __str__(self):
        return self.title_en

    def text(self, base, lang):
        """title / description in a language, falling back to English."""
        return getattr(self, f"{base}_{lang}", "") or getattr(self, f"{base}_en")


# ---- keep the uploads folder clean -------------------------------------
@receiver(post_delete, sender=Project)
def _delete_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=Project)
def _delete_replaced_image(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Project.objects.get(pk=instance.pk).image
    except Project.DoesNotExist:
        return
    if old and old.name != instance.image.name:
        old.delete(save=False)
