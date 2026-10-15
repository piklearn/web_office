from django import forms
from django.contrib.auth import get_user_model
from .fields import JalaliDateField

from support.widgets import CommaNumberInput
from .models import (Customer, WorkGroup, Contact, CustomerSoftware, Payment, Request, Task, TaskStatus)

# کلاس‌های اینپوت توسط CSS .float-field کنترل می‌شوند؛ فقط placeholder برای لیبل شناور لازم است.
BASE = "w-full text-right outline-none"


class StyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "rounded border-slate-300 text-sky-600 focus:ring-sky-500")
                continue
            # کلاس‌های بصری را CSS .float-field می‌دهد؛ فقط کلاس‌های منطقی را نگه دار
            prev = (w.attrs.get("class") or "")
            keep = []
            for c in prev.split():
                if c in ("jalali-date-input", "jalali-date", "comma-number") or c.startswith("js-"):
                    keep.append(c)
            keep.append("w-full")
            keep.append("text-right")
            keep.append("outline-none")
            w.attrs["class"] = " ".join(dict.fromkeys(keep))
            if not isinstance(w, (forms.Select, forms.SelectMultiple)):
                # فاصله برای :placeholder-shown
                w.attrs["placeholder"] = w.attrs.get("placeholder") or " "
                if not str(w.attrs["placeholder"]).strip() and "jalali" not in " ".join(keep):
                    w.attrs["placeholder"] = " "


class CustomerForm(StyledForm):
    birth_date = JalaliDateField(label="تاریخ تولد", required=False)

    class Meta:
        model = Customer
        fields = [
            "full_name", "company_name", "national_id", "mobile", "landline",
            "birth_date", "activity_type", "status", "owner",
            "address", "description",
        ]
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
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "amount": CommaNumberInput(),
        }


class RequestForm(StyledForm):
    class Meta:
        model = Request
        fields = ["subject", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class TaskForm(StyledForm):
    due_date = JalaliDateField(label="موعد", required=False)

    class Meta:
        model = Task
        fields = ["title", "group", "assignee", "due_date", "due_time"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = WorkGroup.objects.filter(is_active=True)
        self.fields["group"].required = False
        self.fields["assignee"].queryset = get_user_model().objects.filter(is_active=True)
        self.fields["assignee"].required = False
        self.fields["assignee"].label = "مسئول (اختیاری)"


class TaskResultForm(StyledForm):
    due_date = JalaliDateField(label="پیگیری بعدی (تاریخ)", required=False)

    class Meta:
        model = Task
        fields = ["status", "result", "result_note", "due_date", "due_time"]
        labels = {"due_date": "پیگیری بعدی (تاریخ)", "due_time": "پیگیری بعدی (ساعت)"}
        widgets = {
            "result_note": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }