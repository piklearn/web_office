import jdatetime
from django import forms
from django.core.exceptions import ValidationError


class JalaliDateInput(forms.TextInput):
    def __init__(self, attrs=None):
        default = {
            "placeholder": "۱۴۰۳/۰۷/۱۰",
            "autocomplete": "off",
            "dir": "ltr",
            "class": "jalali-date-input",
        }
        if attrs:
            default.update(attrs)
        super().__init__(default)

    def format_value(self, value):
        if value in (None, ""):
            return ""
        # اگر از دیتابیس Date آمده باشد
        if hasattr(value, "year") and not isinstance(value, str):
            try:
                return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")
            except Exception:
                return str(value)
        return value


class JalaliDateField(forms.CharField):
    """ورودی شمسی YYYY/MM/DD → خروجی date میلادی برای مدل."""
    widget = JalaliDateInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", "مثال: ۱۴۰۳/۰۷/۱۰")
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return None
        value = (
            str(value)
            .strip()
            .replace("-", "/")
            .replace(".", "/")
            .translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
        )
        parts = value.split("/")
        if len(parts) != 3:
            raise ValidationError("تاریخ را به صورت سال/ماه/روز وارد کنید.")
        try:
            y, m, d = map(int, parts)
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise ValidationError("تاریخ شمسی نامعتبر است.")