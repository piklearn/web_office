from django.contrib import admin

from sales.templatetags.date_tags import to_jalali
from support.widgets import CommaNumberInput
from django import forms
from .models import WorkGroup

from .models import (Activity, Contact, Customer, CustomerSoftware, EmployeeProfile,
                     Payment, Request, Software, Task, can_see_finance, is_manager)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


class CustomerSoftwareInline(admin.TabularInline):
    model = CustomerSoftware
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    formfield_overrides = {}

    def has_view_permission(self, request, obj=None):
        return can_see_finance(request.user)

    def has_add_permission(self, request, obj=None):
        return can_see_finance(request.user)

    def has_change_permission(self, request, obj=None):
        return can_see_finance(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_see_finance(request.user)


class CustomerAdminForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        widgets = {"total_amount": CommaNumberInput()}


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    form = CustomerAdminForm
    list_display = ("__str__", "full_name", "mobile", "status", "owner", "created_jalali")
    list_filter = ("status", "payment_status", "owner")
    search_fields = ("full_name", "company_name", "mobile", "national_id", "landline",
                     "softwares__software__name")
    inlines = [ContactInline, CustomerSoftwareInline, PaymentInline]

    @admin.display(description="تاریخ ثبت", ordering="created_at")
    def created_jalali(self, obj):
        return to_jalali(obj.created_at)

    def get_exclude(self, request, obj=None):
        return None if can_see_finance(request.user) else ("total_amount", "payment_status")


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("subject", "customer", "created_by", "created_jalali")
    search_fields = ("subject", "customer__full_name", "customer__company_name")
    autocomplete_fields = ("customer",)

    @admin.display(description="تاریخ", ordering="created_at")
    def created_jalali(self, obj):
        return to_jalali(obj.created_at)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "assignee", "due_jalali", "status")
    list_filter = ("status", "assignee")
    list_editable = ("status",)
    search_fields = ("title", "customer__full_name", "customer__company_name")
    autocomplete_fields = ("customer", "request")

    @admin.display(description="موعد", ordering="due_date")
    def due_jalali(self, obj):
        return to_jalali(obj.due_date)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if is_manager(request.user) else qs.filter(assignee=request.user)


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)

    def has_module_permission(self, request):
        return is_manager(request.user)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("customer", "text", "user", "created_at")
    search_fields = ("text", "customer__full_name")
    readonly_fields = ("customer", "text", "user", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    filter_horizontal = ("members",)