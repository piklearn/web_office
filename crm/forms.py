from django import forms
from django.contrib.auth import get_user_model
from .fields import JalaliDateField

from support.widgets import CommaNumberInput
from .models import (Customer, Contact, CustomerSoftware, Payment, Request, Task, TaskStatus)

BASE = ("w-full rounded-xl border border-slate-300 px-4 py-2.5 text-right "
        "focus:border-sky-500 focus:ring-2 focus:ring-sky-200 outline-none")


class StyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                continue
            f.widget.attrs["class"] = f"{f.widget.attrs.get('class', '')} {BASE}".strip()


class CustomerForm(StyledForm):
    birth_date = JalaliDateField(label="تاریخ تولد", required=False)
    class Meta:
        model = Customer
        fields = ["full_name", "company_name", "national_id", "mobile", "landline",
                  "birth_date", "address", "activity_type", "status", "owner", "description"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "address": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ContactForm(StyledForm):
    class Meta:
        model = Contact
        fields = ["name", "position", "phone", "description"]


class CustomerSoftwareForm(StyledForm):
    class Meta:
        model = CustomerSoftware
        fields = ["software", "is_purchased", "sale_status", "drop_reason", "note"]


class PaymentForm(StyledForm):
    date = JalaliDateField(label="تاریخ")
    class Meta:
        model = Payment
        fields = ["date", "amount", "method", "description"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "amount": CommaNumberInput()}


class RequestForm(StyledForm):
    class Meta:
        model = Request
        fields = ["subject", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class TaskForm(StyledForm):
    due_date = JalaliDateField(label="موعد", required=False)
    class Meta:
        model = Task
        fields = ["title", "assignee", "due_date", "due_time"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "due_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = get_user_model().objects.filter(is_active=True)


class TaskResultForm(StyledForm):
    """ثبت نتیجهٔ پیگیری و تغییر وضعیت یا تعیین پیگیری بعدی."""
    due_date = JalaliDateField(label="پیگیری بعدی (تاریخ)", required=False)
    class Meta:
        model = Task
        fields = ["status", "result", "result_note", "due_date", "due_time"]
        labels = {"due_date": "پیگیری بعدی (تاریخ)", "due_time": "پیگیری بعدی (ساعت)"}
        widgets = {"result_note": forms.Textarea(attrs={"rows": 3}),
                   "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "due_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M")}
