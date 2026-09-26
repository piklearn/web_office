from django import forms
from .models import RepairCase


class TrackingForm(forms.Form):
    """فرم پیگیری سریع در صفحه اصلی - جستجو بر اساس کد پیگیری یا شماره تماس."""
    query = forms.CharField(
        label="کد پیگیری یا شماره تماس",
        max_length=30,
        widget=forms.TextInput(attrs={
            "placeholder": "مثال: 0912xxxxxxx",
            "class": ("w-full rounded-xl border border-slate-300 px-4 py-3 text-right "
                      "focus:border-sky-500 focus:ring-2 focus:ring-sky-200 outline-none "
                      "transition-all duration-300"),
        })
    )


class RepairCaseForm(forms.ModelForm):
    """فرم ثبت کیس تعمیر - برای استفاده کارکنان دفتر."""

    class Meta:
        model = RepairCase
        fields = [
            "customer_name", "phone", "device_type", "device_model",
            "serial_number", "problem_description", "estimated_cost",
        ]
        widgets = {
            "problem_description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = ("w-full rounded-xl border border-slate-300 px-4 py-3 text-right "
                         "focus:border-sky-500 focus:ring-2 focus:ring-sky-200 outline-none "
                         "transition-all duration-300")
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_classes}".strip()
