"""Confirmation and team-notification emails for new project briefs."""
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(inquiry):
    first = inquiry.name.split()[0].title()
    try:
        send_mail(
            subject=f"We received your project brief ({inquiry.reference})",
            message=(
                f"Hi {first},\n\n"
                f"Thank you for sharing your project with us. Your reference is {inquiry.reference}.\n"
                f"Service: {inquiry.get_service_display()}\n\n"
                "A member of the team will review your brief and reply within 24 hours.\n"
                "You can follow its progress on the Track page using this reference and your email.\n\n"
                "This is an automated message from an assessment prototype."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
            fail_silently=False,
        )
        if settings.INQUIRY_NOTIFY_EMAIL:
            send_mail(
                subject=f"New project brief {inquiry.reference}: {inquiry.get_service_display()}",
                message=(
                    f"Reference: {inquiry.reference}\nName: {inquiry.name}\nEmail: {inquiry.email}\n"
                    f"Phone: {inquiry.phone or '-'}\nCompany: {inquiry.company or '-'}\n"
                    f"Industry: {inquiry.industry or '-'}\nService: {inquiry.get_service_display()}\n"
                    f"Budget: {inquiry.get_budget_display() or '-'}\nTimeline: {inquiry.get_timeline_display() or '-'}\n\n"
                    f"Project: {inquiry.project_type or '-'}\nRequirements: {inquiry.requirements or '-'}\n\n"
                    f"Overview:\n{inquiry.description}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.INQUIRY_NOTIFY_EMAIL],
                fail_silently=False,
            )
    except Exception:  # never let an email problem break the visitor's submission
        logger.exception("Could not send emails for %s", inquiry.reference)


def dispatch_inquiry_emails(inquiry):
    """Send emails in a background thread so the visitor is never kept waiting."""
    if settings.INQUIRY_EMAIL_ASYNC:
        threading.Thread(target=_send, args=(inquiry,), daemon=True).start()
    else:
        _send(inquiry)
