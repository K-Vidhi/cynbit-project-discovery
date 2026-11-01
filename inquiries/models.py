import secrets

from django.db import models


def generate_reference():
    return "CY-" + secrets.token_hex(4).upper()


class Inquiry(models.Model):
    SERVICE_CHOICES = [
        ("software", "Software engineering"),
        ("ai", "AI automation"),
        ("cloud", "Cloud infrastructure"),
        ("marketing", "Digital marketing & SEO"),
        ("other", "Not sure yet"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("progress", "In progress"),
        ("completed", "Completed"),
    ]
    STATUS_ORDER = [key for key, _ in STATUS_CHOICES]
    BUDGET_CHOICES = [
        ("under-25k", "Under \u20b925,000"),
        ("25k-50k", "\u20b925,000 \u2013 \u20b950,000"),
        ("50k-1l", "\u20b950,000 \u2013 \u20b91,00,000"),
        ("1l-5l", "\u20b91,00,000 \u2013 \u20b95,00,000"),
        ("above-5l", "Above \u20b95,00,000"),
        ("not-sure", "Not sure yet"),
    ]
    TIMELINE_CHOICES = [
        ("asap", "As soon as possible"),
        ("1-3m", "1 \u2013 3 months"),
        ("3-6m", "3 \u2013 6 months"),
        ("6m+", "More than 6 months"),
        ("flexible", "Flexible"),
    ]

    reference = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=120, blank=True)
    industry = models.CharField(max_length=80, blank=True)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    project_type = models.CharField("project name", max_length=120, blank=True)
    requirements = models.TextField(blank=True)
    budget = models.CharField(max_length=20, choices=BUDGET_CHOICES, blank=True)
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, blank=True)
    description = models.TextField()
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

    def save(self, *args, **kwargs):
        if not self.reference:
            ref = generate_reference()
            while Inquiry.objects.filter(reference=ref).exists():
                ref = generate_reference()
            self.reference = ref
        super().save(*args, **kwargs)

    @property
    def status_index(self):
        return self.STATUS_ORDER.index(self.status)

    def __str__(self):
        return f"{self.reference} \u2014 {self.name}"
