from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "email", "service", "budget", "status", "created_at")
    list_filter = ("service", "status", "budget", "created_at")
    search_fields = ("reference", "name", "email", "company", "description")
    readonly_fields = ("reference", "created_at", "updated_at")
