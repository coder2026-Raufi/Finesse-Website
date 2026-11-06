import json
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings

from .models import Inquiry

GOOD = {
    "name": "Ahmad Karimi",
    "email": "ahmad@example.org",
    "subject": "research",
    "message": "We would like to discuss a baseline survey.",
    "language": "fa",
    "website": "",
}


def post(client, data, **extra):
    return client.post("/api/contact/", data=json.dumps(data), content_type="application/json", **extra)


@override_settings(CORS_ALLOWED_ORIGINS=["https://finesse.example"], EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ContactApiTests(TestCase):
    def test_valid_message_is_saved_and_emailed(self):
        r = post(self.client, GOOD)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json(), {"ok": True})
        inq = Inquiry.objects.get()
        self.assertEqual(inq.name, "Ahmad Karimi")
        self.assertEqual(inq.language, "fa")
        self.assertTrue(inq.notified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ["ahmad@example.org"])
        self.assertIn("baseline survey", mail.outbox[0].body)

    def test_ip_is_stored_hashed_not_raw(self):
        post(self.client, GOOD, REMOTE_ADDR="203.0.113.9")
        inq = Inquiry.objects.get()
        self.assertNotIn("203.0.113.9", inq.ip_hash)
        self.assertEqual(len(inq.ip_hash), 64)

    def test_validation_errors_return_field_codes(self):
        r = post(self.client, {**GOOD, "name": "A", "email": "nope", "subject": "x", "message": "short"})
        self.assertEqual(r.status_code, 400)
        fields = r.json()["fields"]
        self.assertEqual(set(fields), {"name", "email", "subject", "message"})
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_missing_fields_rejected(self):
        r = post(self.client, {})
        self.assertEqual(r.status_code, 400)

    def test_non_string_values_do_not_crash(self):
        r = post(self.client, {**GOOD, "name": {"a": 1}, "message": ["x"]})
        self.assertEqual(r.status_code, 400)

    def test_honeypot_pretends_success_but_stores_nothing(self):
        r = post(self.client, {**GOOD, "website": "http://spam.example"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CONTACT_RATE_LIMIT=2)
    def test_rate_limit_per_visitor(self):
        for i in range(2):
            self.assertEqual(post(self.client, {**GOOD, "message": f"message number {i} here"}).status_code, 201)
        r = post(self.client, {**GOOD, "message": "a third different message"})
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json()["error"], "rate_limited")
        # a different visitor is not affected
        r2 = post(self.client, {**GOOD, "message": "from someone else entirely"}, REMOTE_ADDR="198.51.100.7")
        self.assertEqual(r2.status_code, 201)

    def test_identical_double_submit_is_stored_once(self):
        post(self.client, GOOD)
        r = post(self.client, GOOD)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_failure_still_saves_message(self):
        with mock.patch("inquiries.emails.EmailMessage.send", side_effect=OSError("smtp down")):
            r = post(self.client, GOOD)
        self.assertEqual(r.status_code, 201)
        inq = Inquiry.objects.get()
        self.assertFalse(inq.notified)
        self.assertIn("smtp down", inq.notify_error)

    def test_retry_command_resends_failed(self):
        with mock.patch("inquiries.emails.EmailMessage.send", side_effect=OSError("down")):
            post(self.client, GOOD)
        from django.core.management import call_command
        call_command("retry_notifications")
        self.assertTrue(Inquiry.objects.get().notified)
        self.assertEqual(len(mail.outbox), 1)

    def test_requires_json_content_type(self):
        r = self.client.post("/api/contact/", data="name=a", content_type="application/x-www-form-urlencoded")
        self.assertEqual(r.status_code, 415)

    def test_malformed_json(self):
        r = self.client.post("/api/contact/", data="{oops", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_oversized_body_rejected(self):
        r = post(self.client, {**GOOD, "message": "x" * 30_000})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/api/contact/").status_code, 405)

    def test_header_injection_in_name_is_neutralised(self):
        r = post(self.client, {**GOOD, "name": "Eve\r\nBcc: victim@example.com"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(mail.outbox[0].bcc, [])
        self.assertNotIn("\n", mail.outbox[0].subject)

    # ---- origin / CORS
    def test_allowed_origin_gets_cors_headers(self):
        r = post(self.client, GOOD, HTTP_ORIGIN="https://finesse.example")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r["Access-Control-Allow-Origin"], "https://finesse.example")

    def test_unknown_origin_blocked(self):
        r = post(self.client, GOOD, HTTP_ORIGIN="https://evil.example")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_preflight(self):
        r = self.client.options("/api/contact/", HTTP_ORIGIN="https://finesse.example",
                                HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST")
        self.assertEqual(r.status_code, 204)
        self.assertIn("POST", r["Access-Control-Allow-Methods"])

    def test_no_origin_header_is_allowed(self):
        # curl, server-to-server and same-origin GET-less posts carry no Origin
        self.assertEqual(post(self.client, GOOD).status_code, 201)

    def test_health(self):
        r = self.client.get("/api/health/")
        self.assertEqual(r.json(), {"ok": True})


class AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_superuser("boss", "b@example.com", "a-long-test-password-1")
        self.client.login(username="boss", password="a-long-test-password-1")
        self.inq = Inquiry.objects.create(
            name="=cmd", email="x@example.org", subject="mgmt",
            message="=HYPERLINK(\"http://x\") hello there", ip_hash="h" * 64,
        )

    def test_list_and_detail_open(self):
        self.assertEqual(self.client.get("/admin/inquiries/inquiry/").status_code, 200)
        r = self.client.get(f"/admin/inquiries/inquiry/{self.inq.pk}/change/")
        self.assertEqual(r.status_code, 200)
        self.inq.refresh_from_db()
        self.assertEqual(self.inq.status, "read")  # opening marks as read

    def test_csv_export_blocks_formula_injection(self):
        r = self.client.post("/admin/inquiries/inquiry/", {
            "action": "export_csv", "_selected_action": [self.inq.pk]})
        body = r.content.decode("utf-8-sig")
        self.assertIn("'=cmd", body)
        self.assertIn("'=HYPERLINK", body)

    def test_cannot_add_from_admin(self):
        self.assertEqual(self.client.get("/admin/inquiries/inquiry/add/").status_code, 403)
