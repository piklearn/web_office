from django import forms
from django.contrib import admin
from sales.templatetags.date_tags import to_jalali
from .models import RepairCase, AccompanyingItem
from .widgets import CommaNumberInput


class RepairCaseAdminForm(forms.ModelForm):
    class Meta:
        model = RepairCase
        fields = "__all__"
        widgets = {
            "estimated_cost": CommaNumberInput(),
        }


class AccompanyingItemInline(admin.TabularInline):
    """اقلامی که همراه دستگاه در حال تعمیر تحویل داده شده‌اند (کیف، شارژر، ماوس و ...)."""
    model = AccompanyingItem
    extra = 1
    fields = ("name", "quantity", "note")


@admin.register(RepairCase)
class RepairCaseAdmin(admin.ModelAdmin):
    form = RepairCaseAdminForm
    list_display = ("tracking_code", "customer_name", "phone", "device_type",
                     "status", "received_at_jalali", "updated_at")
    list_filter = ("status", "device_type", "received_at")
    search_fields = ("tracking_code", "customer_name", "phone", "device_model", "serial_number")
    readonly_fields = ("tracking_code", "received_at_jalali", "updated_at")
    list_editable = ("status",)
    date_hierarchy = "received_at"
    inlines = [AccompanyingItemInline]

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
            "fields": ("received_at_jalali", "updated_at"),
        }),
    )

    def received_at_jalali(self, obj):
        if not obj.received_at:
            return "—"
        return f"{to_jalali(obj.received_at)} - {obj.received_at.strftime('%H:%M')}"
    received_at_jalali.short_description = "تاریخ دریافت"
    received_at_jalali.admin_order_field = "received_at"
