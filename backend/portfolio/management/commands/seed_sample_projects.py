from django.core.management.base import BaseCommand

from portfolio.models import Project
from portfolio.samples import load_samples


class Command(BaseCommand):
    help = "Add the 6 sample projects from the old static page (only if there are no projects yet)."

    def handle(self, *args, **options):
        if Project.objects.exists():
            self.stdout.write("Projects already exist, nothing added.")
            return
        self.stdout.write(f"{load_samples()} sample projects added.")
