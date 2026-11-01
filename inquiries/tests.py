from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Inquiry

VALID = {
    "name": "Asha Verma",
    "email": "asha@example.com",
    "phone": "+91 98765 43210",
    "company": "Verma Textiles",
    "industry": "Retail & E-commerce",
    "service": "ai",
    "project_type": "Support chatbot",
    "requirements": "Answer FAQs in English and Hindi",
    "budget": "50k-1l",
    "timeline": "1-3m",
    "description": "We want an AI assistant that answers common customer questions on WhatsApp.",
    "consent": "on",
    "website": "",
}


@override_settings(INQUIRY_EMAIL_ASYNC=False, INQUIRY_NOTIFY_EMAIL="team@example.com", INQUIRY_RATE_LIMIT=5)
class PublicFlowTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_home_renders_all_steps(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        for text in ("Who are we connecting with?", "What are we architecting?", "Define the opportunity."):
            self.assertContains(r, text)

    def test_valid_submission_saves_and_redirects(self):
        r = self.client.post(reverse("home"), VALID)
        inquiry = Inquiry.objects.get()
        self.assertRedirects(r, reverse("thank_you", args=[inquiry.reference]))
        self.assertRegex(inquiry.reference, r"^CY-[0-9A-F]{8}$")
        self.assertEqual(inquiry.status, "new")
        self.assertTrue(inquiry.consent)

    def test_emails_sent_to_visitor_and_team(self):
        self.client.post(reverse("home"), VALID)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["asha@example.com"])
        self.assertEqual(mail.outbox[1].to, ["team@example.com"])

    def test_rejects_bad_input(self):
        cases = {
            "email": "not-an-email",
            "description": "too short",
            "phone": "abc",
            "service": "hacking",
            "name": "A",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                r = self.client.post(reverse("home"), {**VALID, field: value})
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.context["form"].errors)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_consent_is_required(self):
        data = {k: v for k, v in VALID.items() if k != "consent"}
        r = self.client.post(reverse("home"), data)
        self.assertEqual(r.status_code, 400)
        self.assertIn("consent", r.context["form"].errors)

    def test_honeypot_blocks_bots(self):
        r = self.client.post(reverse("home"), {**VALID, "website": "http://spam.example"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_rate_limit_after_five_briefs(self):
        for _ in range(5):
            self.assertEqual(self.client.post(reverse("home"), VALID).status_code, 302)
        r = self.client.post(reverse("home"), VALID)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(Inquiry.objects.count(), 5)

    def test_server_error_keeps_typed_values(self):
        r = self.client.post(reverse("home"), {**VALID, "email": "bad"})
        self.assertContains(r, "Asha Verma", status_code=400)
        self.assertContains(r, "data-has-error", status_code=400)

    def test_thank_you_only_for_the_submitter(self):
        self.client.post(reverse("home"), VALID)
        ref = Inquiry.objects.get().reference
        self.assertEqual(self.client.get(reverse("thank_you", args=[ref])).status_code, 200)
        other = self.client_class()
        self.assertRedirects(other.get(reverse("thank_you", args=[ref])), reverse("home"))

    def test_tracking_needs_reference_and_matching_email(self):
        self.client.post(reverse("home"), VALID)
        ref = Inquiry.objects.get().reference
        ok = self.client.post(reverse("track"), {"reference": ref.lower(), "email": "ASHA@example.com"})
        self.assertContains(ok, "New")
        self.assertIsNotNone(ok.context["inquiry"])
        bad = self.client.post(reverse("track"), {"reference": ref, "email": "someone@else.com"})
        self.assertIsNone(bad.context["inquiry"])
        self.assertContains(bad, "couldn")

    def test_unknown_page_uses_branded_404(self):
        with override_settings(DEBUG=False):
            r = self.client.get("/does-not-exist/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "could not be found", status_code=404)


@override_settings(INQUIRY_EMAIL_ASYNC=False, INQUIRY_NOTIFY_EMAIL="")
class StaffAreaTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.staff = User.objects.create_user("staff", "s@example.com", "pass-12345-x", is_staff=True)
        self.visitor = User.objects.create_user("visitor", "v@example.com", "pass-12345-x")
        self.i1 = Inquiry.objects.create(name="Asha", email="a@example.com", service="ai", description="x" * 30)
        self.i2 = Inquiry.objects.create(name="Ravi", email="r@example.com", service="cloud", status="reviewed", description="y" * 30)

    def test_anonymous_and_non_staff_are_redirected(self):
        for url in (reverse("dashboard"), reverse("inquiry_detail", args=[self.i1.pk]), reverse("export_csv")):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="visitor", password="pass-12345-x")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_staff_dashboard_filters(self):
        self.client.login(username="staff", password="pass-12345-x")
        r = self.client.get(reverse("dashboard"), {"status": "reviewed"})
        self.assertContains(r, "Ravi")
        self.assertNotContains(r, "Asha")
        r = self.client.get(reverse("dashboard"), {"q": self.i1.reference})
        self.assertContains(r, "Asha")

    def test_staff_can_update_status_and_notes(self):
        self.client.login(username="staff", password="pass-12345-x")
        self.client.post(reverse("inquiry_detail", args=[self.i1.pk]), {"status": "progress", "admin_notes": "Called client"})
        self.i1.refresh_from_db()
        self.assertEqual((self.i1.status, self.i1.admin_notes), ("progress", "Called client"))
        self.client.post(reverse("inquiry_detail", args=[self.i1.pk]), {"status": "bogus"})
        self.i1.refresh_from_db()
        self.assertEqual(self.i1.status, "progress")

    def test_script_in_name_is_escaped(self):
        Inquiry.objects.create(name="<script>alert(1)</script>", email="x@example.com", service="ai", description="z" * 30)
        self.client.login(username="staff", password="pass-12345-x")
        r = self.client.get(reverse("dashboard"))
        self.assertNotContains(r, "<script>alert(1)</script>")

    def test_csv_export_blocks_formula_injection(self):
        Inquiry.objects.create(name="=HYPERLINK(\"http://evil\")", email="x@example.com", service="ai", description="z" * 30)
        self.client.login(username="staff", password="pass-12345-x")
        r = self.client.get(reverse("export_csv"))
        body = r.content.decode()
        self.assertEqual(r["Content-Type"], "text/csv")
        self.assertIn("'=HYPERLINK", body)
        self.assertNotIn(",=HYPERLINK", body)
