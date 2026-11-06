import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from inquiries.models import Inquiry
from portfolio.models import Project

TMP_MEDIA = tempfile.mkdtemp()


def png(size=(3000, 1500)):
    buf = io.BytesIO()
    Image.new("RGBA", size, (200, 30, 30, 128)).save(buf, "PNG")
    return SimpleUploadedFile("photo.png", buf.getvalue(), content_type="image/png")


def project_data(**kw):
    d = dict(title_en="Water Survey", description_en="A survey of wells.", category="research",
             year=2025, duration_months=6, client="ngo", is_published="on")
    d.update(kw)
    return d


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class DashboardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        U = get_user_model()
        U.objects.create_user("staff", password="a-long-test-password-1", is_staff=True)
        U.objects.create_user("visitor", password="a-long-test-password-1", is_staff=False)
        self.client.login(username="staff", password="a-long-test-password-1")

    # ---- access control
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        for url in ["/dashboard/", "/dashboard/messages/", "/dashboard/projects/", "/dashboard/projects/new/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/dashboard/login/", r["Location"])

    def test_non_staff_forbidden(self):
        self.client.logout()
        self.client.login(username="visitor", password="a-long-test-password-1")
        self.assertEqual(self.client.get("/dashboard/").status_code, 403)

    def test_anonymous_cannot_delete_or_post(self):
        p = Project.objects.create(title_en="x", description_en="y", category="research", year=2024)
        self.client.logout()
        self.client.post(f"/dashboard/projects/{p.pk}/delete/")
        self.assertTrue(Project.objects.filter(pk=p.pk).exists())

    def test_login_lockout_after_5_failures(self):
        self.client.logout()
        for _ in range(5):
            r = self.client.post("/dashboard/login/", {"username": "staff", "password": "wrong"})
            self.assertEqual(r.status_code, 200)
        r = self.client.post("/dashboard/login/", {"username": "staff", "password": "a-long-test-password-1"})
        self.assertEqual(r.status_code, 429)  # even the right password is refused while locked

    def test_login_works(self):
        self.client.logout()
        r = self.client.post("/dashboard/login/", {"username": "staff", "password": "a-long-test-password-1"})
        self.assertEqual(r.status_code, 302)

    # ---- pages
    def test_overview_and_lists_render(self):
        Inquiry.objects.create(name="A", email="a@b.co", subject="me", message="hello there friend", ip_hash="x" * 64)
        for url in ["/dashboard/", "/dashboard/messages/", "/dashboard/messages/?status=new&q=hello", "/dashboard/projects/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get("/dashboard/"), "Email is not set up yet")  # console backend in tests

    def test_message_open_marks_read_and_delete(self):
        m = Inquiry.objects.create(name="A", email="a@b.co", subject="me", message="hello there friend", ip_hash="x" * 64)
        self.assertEqual(self.client.get(f"/dashboard/messages/{m.pk}/").status_code, 200)
        m.refresh_from_db(); self.assertEqual(m.status, "read")
        self.client.post(f"/dashboard/messages/{m.pk}/status/", {"status": "replied"})
        m.refresh_from_db(); self.assertEqual(m.status, "replied")
        self.client.post(f"/dashboard/messages/{m.pk}/delete/")
        self.assertFalse(Inquiry.objects.exists())

    def test_message_text_is_escaped(self):
        m = Inquiry.objects.create(name="<script>alert(1)</script>", email="a@b.co", subject="me",
                                   message="<img src=x onerror=alert(1)>", ip_hash="x" * 64)
        r = self.client.get(f"/dashboard/messages/{m.pk}/")
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertNotContains(r, "<img src=x")

    # ---- projects
    def test_add_project_with_image_resizes_it(self):
        r = self.client.post("/dashboard/projects/new/", {**project_data(), "image": png()})
        self.assertEqual(r.status_code, 302)
        p = Project.objects.get()
        self.assertTrue(p.image.name.endswith(".jpg"))
        with Image.open(p.image.path) as im:
            self.assertLessEqual(max(im.size), 1600)
            self.assertEqual(im.format, "JPEG")

    def test_add_project_validation(self):
        r = self.client.post("/dashboard/projects/new/", project_data(title_en="", year=1800))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)

    def test_fake_image_rejected(self):
        bad = SimpleUploadedFile("evil.png", b"<?php echo 1; ?>", content_type="image/png")
        r = self.client.post("/dashboard/projects/new/", {**project_data(), "image": bad})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)

    def test_delete_project_removes_photo_file(self):
        self.client.post("/dashboard/projects/new/", {**project_data(), "image": png((400, 300))})
        p = Project.objects.get()
        path = p.image.path
        import os
        self.assertTrue(os.path.exists(path))
        self.client.post(f"/dashboard/projects/{p.pk}/delete/")
        self.assertEqual(Project.objects.count(), 0)
        self.assertFalse(os.path.exists(path))

    def test_edit_and_toggle(self):
        self.client.post("/dashboard/projects/new/", project_data())
        p = Project.objects.get()
        self.client.post(f"/dashboard/projects/{p.pk}/edit/", project_data(title_en="Renamed", title_fa="نام جدید"))
        p.refresh_from_db(); self.assertEqual(p.title_en, "Renamed"); self.assertEqual(p.title_fa, "نام جدید")
        self.client.post(f"/dashboard/projects/{p.pk}/toggle/")
        p.refresh_from_db(); self.assertFalse(p.is_published)

    def test_get_does_not_delete(self):
        p = Project.objects.create(title_en="x", description_en="y", category="research", year=2024)
        self.client.get(f"/dashboard/projects/{p.pk}/delete/")
        self.assertTrue(Project.objects.filter(pk=p.pk).exists())

    def test_load_samples_only_when_empty(self):
        self.client.post("/dashboard/projects/samples/")
        self.assertEqual(Project.objects.count(), 6)
        self.assertTrue(all(p.image for p in Project.objects.all()))
        self.client.post("/dashboard/projects/samples/")
        self.assertEqual(Project.objects.count(), 6)

    # ---- public API
    def test_public_api_lists_only_published_with_fallback(self):
        Project.objects.create(title_en="Live", title_fa="زنده", description_en="d", category="research", year=2025)
        Project.objects.create(title_en="Secret", description_en="d", category="research", year=2025, is_published=False)
        self.client.logout()
        data = self.client.get("/api/projects/").json()["projects"]
        self.assertEqual([p["title"]["en"] for p in data], ["Live"])
        self.assertEqual(data[0]["title"]["fa"], "زنده")
        self.assertEqual(data[0]["title"]["ps"], "Live")  # empty Pashto falls back to English
        self.assertIsNone(data[0]["image"])

    def test_deleting_everything_gives_empty_list(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/projects/").json(), {"projects": []})

    def test_api_cors_for_allowed_origin(self):
        with override_settings(CORS_ALLOWED_ORIGINS=["https://finesse.example"]):
            r = self.client.get("/api/projects/", HTTP_ORIGIN="https://finesse.example")
            self.assertEqual(r["Access-Control-Allow-Origin"], "https://finesse.example")
