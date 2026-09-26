from django.contrib import admin
from .models import RepairCase


@admin.register(RepairCase)
class RepairCaseAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "customer_name", "phone", "device_type",
                     "status", "received_at", "updated_at")
    list_filter = ("status", "device_type", "received_at")
    search_fields = ("tracking_code", "customer_name", "phone", "device_model", "serial_number")
    readonly_fields = ("tracking_code", "received_at", "updated_at")
    list_editable = ("status",)
    date_hierarchy = "received_at"

    fieldsets = (
        ("اطلاعات مشتری", {
            "fields": ("customer_name", "phone", "tracking_code"),
        }),
        ("اطلاعات دستگاه", {
            "fields": ("device_type", "device_model", "serial_number", "problem_description"),
        }),
        ("وضعیت و پیگیری داخلی", {
            "fields": ("status", "technician_notes", "estimated_cost", "delivered_at"),
        }),
        ("زمان‌ها", {
            "fields": ("received_at", "updated_at"),
        }),
    )
