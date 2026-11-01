import csv
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from .emails import dispatch_inquiry_emails
from .forms import InquiryForm, TrackForm
from .models import Inquiry

RATE_WINDOW = 3600  # seconds


# ---- small helpers -------------------------------------------------------
def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "unknown")


def _rl_key(request, scope):
    return "rl:%s:%s" % (scope, hashlib.sha256(client_ip(request).encode()).hexdigest()[:16])


def is_limited(request, scope, limit):
    return cache.get(_rl_key(request, scope), 0) >= limit


def record_hit(request, scope):
    key = _rl_key(request, scope)
    if not cache.add(key, 1, RATE_WINDOW):
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, RATE_WINDOW)


def safe_csv(value):
    """Stop spreadsheet formula injection when staff open the export in Excel."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


# ---- public pages --------------------------------------------------------
def home(request):
    status = 200
    if request.method == "POST":
        if is_limited(request, "submit", settings.INQUIRY_RATE_LIMIT):
            form = InquiryForm(request.POST)
            messages.error(request, "You have sent several briefs recently. Please try again in an hour, or email us directly.")
            status = 429
        else:
            form = InquiryForm(request.POST)
            if form.is_valid():
                inquiry = form.save(commit=False)
                inquiry.consent = True
                inquiry.save()
                record_hit(request, "submit")
                request.session["last_inquiry_reference"] = inquiry.reference
                dispatch_inquiry_emails(inquiry)
                return redirect("thank_you", reference=inquiry.reference)
            status = 400
    else:
        form = InquiryForm()
    return render(request, "inquiries/home.html", {"form": form}, status=status)


def thank_you(request, reference):
    # Only the visitor who just submitted can see their own summary.
    if request.session.get("last_inquiry_reference") != reference:
        return redirect("home")
    inquiry = get_object_or_404(Inquiry, reference=reference)
    return render(request, "inquiries/thank_you.html", {"inquiry": inquiry})


def track(request):
    inquiry, searched, form = None, False, TrackForm(request.POST or None)
    if request.method == "POST":
        if is_limited(request, "track", 15):
            messages.error(request, "Too many lookups. Please try again later.")
        elif form.is_valid():
            searched = True
            record_hit(request, "track")
            inquiry = Inquiry.objects.filter(
                reference=form.cleaned_data["reference"], email__iexact=form.cleaned_data["email"]
            ).first()
    return render(request, "inquiries/track.html", {"form": form, "inquiry": inquiry, "searched": searched})


def not_found(request, exception=None):
    return render(request, "inquiries/404.html", status=404)


# ---- staff area ----------------------------------------------------------
def _filtered(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    service = request.GET.get("service", "")
    qs = Inquiry.objects.all()
    if query:
        qs = qs.filter(
            Q(reference__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query) | Q(company__icontains=query)
        )
    if status in Inquiry.STATUS_ORDER:
        qs = qs.filter(status=status)
    else:
        status = ""
    if service in dict(Inquiry.SERVICE_CHOICES):
        qs = qs.filter(service=service)
    else:
        service = ""
    return qs, query, status, service


@staff_member_required
def dashboard(request):
    qs, query, status, service = _filtered(request)
    week_ago = timezone.now() - timedelta(days=7)
    by_service = {row["service"]: row["n"] for row in Inquiry.objects.values("service").annotate(n=Count("id"))}
    page = Paginator(qs, 15).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    context = {
        "page": page,
        "query": query,
        "selected_status": status,
        "selected_service": service,
        "statuses": Inquiry.STATUS_CHOICES,
        "services": Inquiry.SERVICE_CHOICES,
        "total": Inquiry.objects.count(),
        "new_count": Inquiry.objects.filter(status="new").count(),
        "week_count": Inquiry.objects.filter(created_at__gte=week_ago).count(),
        "service_stats": [(label, by_service.get(key, 0)) for key, label in Inquiry.SERVICE_CHOICES],
        "querystring": params.urlencode(),
    }
    return render(request, "inquiries/dashboard.html", context)


@staff_member_required
def inquiry_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in Inquiry.STATUS_ORDER:
            inquiry.status = new_status
            inquiry.admin_notes = request.POST.get("admin_notes", "").strip()
            inquiry.save(update_fields=["status", "admin_notes", "updated_at"])
            messages.success(request, f"{inquiry.reference} updated.")
        else:
            messages.error(request, "Please choose a valid status.")
        return redirect("inquiry_detail", pk=inquiry.pk)
    return render(request, "inquiries/inquiry_detail.html", {"inquiry": inquiry, "statuses": Inquiry.STATUS_CHOICES})


@staff_member_required
def export_csv(request):
    qs, *_ = _filtered(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="cynbit-inquiries.csv"'
    writer = csv.writer(response)
    writer.writerow(["Reference", "Received", "Name", "Email", "Phone", "Company", "Industry", "Service", "Project",
                     "Budget", "Timeline", "Status", "Overview", "Requirements", "Internal notes"])
    for i in qs:
        writer.writerow([safe_csv(v) for v in (
            i.reference, timezone.localtime(i.created_at).strftime("%Y-%m-%d %H:%M"), i.name, i.email, i.phone,
            i.company, i.industry, i.get_service_display(), i.project_type, i.get_budget_display(),
            i.get_timeline_display(), i.get_status_display(), i.description, i.requirements, i.admin_notes)])
    return response
