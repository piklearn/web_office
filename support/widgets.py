from django import forms


class CommaNumberInput(forms.TextInput):
    """
    ورودی متنی برای اعداد که هنگام تایپ، به‌صورت لحظه‌ای هر سه رقم را با کاما جدا می‌کند
    (مثلاً 1500000 در حین تایپ به‌صورت 1,500,000 نمایش داده می‌شود).
    کاماها قبل از رسیدن به اعتبارسنجی فیلد عددی، به‌صورت خودکار حذف می‌شوند.
    """

    class Media:
        js = ("js/admin/comma_number_input.js",)

    def __init__(self, attrs=None):
        default_attrs = {
            "class": "comma-number-input vTextField",
            "inputmode": "numeric",
            "autocomplete": "off",
            "dir": "ltr",
            "style": "text-align: left;",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def value_from_datadict(self, data, files, name):
        """قبل از رسیدن مقدار به فیلد عددی، کاماها و جداکننده‌های فارسی/عربی حذف می‌شوند."""
        value = super().value_from_datadict(data, files, name)
        if value:
            value = value.replace(",", "").replace("،", "").strip()
        return value

    def format_value(self, value):
        """مقدار ذخیره‌شده در دیتابیس را هنگام نمایش فرم، با کاما فرمت می‌کند."""
        if value in (None, ""):
            return ""
        try:
            number = int(float(value))
        except (ValueError, TypeError):
            return value
        return "{:,}".format(number)
