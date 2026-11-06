"""Loads the sample projects that were written by hand in projects.html, so the
dashboard starts with something and you can edit or delete them."""
import json
from pathlib import Path

from django.conf import settings
from django.core.files import File

from .models import Project

DATA = Path(__file__).with_name("sample_projects.json")


def load_samples():
    created = 0
    for row in json.loads(DATA.read_text(encoding="utf-8")):
        p = Project(
            title_en=row["title"][0], title_fa=row["title"][1], title_ps=row["title"][2], title_ar=row["title"][3],
            description_en=row["desc"][0], description_fa=row["desc"][1], description_ps=row["desc"][2], description_ar=row["desc"][3],
            category=row["category"], year=row["year"], duration_months=row["months"], client=row["client"],
        )
        src = Path(settings.SITE_DIR) / "IMAGES" / "web" / row["image"]
        if src.exists():
            with open(src, "rb") as fh:
                p.image.save(row["image"], File(fh), save=False)
        p.save()
        created += 1
    return created
