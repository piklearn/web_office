"""
سرویس‌های مربوط به نرخ ارز.

فعلاً همه‌ی نرخ‌ها (rate_to_toman روی مدل Currency) به‌صورت دستی
در پنل ادمین وارد می‌شوند.

این فایل برای توسعه‌ی آینده رزرو شده: هر وقت خواستید نرخ ارزهای خارجی
(دلار، درهم، یورو و ...) را به‌صورت خودکار از اینترنت دریافت کنید،
کافی است تابع fetch_and_update_rates را کامل کنید و آن را از یک
Django management command یا یک دکمه‌ی Admin Action صدا بزنید.

نمونه‌ی پیاده‌سازی (غیرفعال - نیازمند بسته‌ی requests و دسترسی اینترنت
از سرور واقعی، نه محیط توسعه‌ی محلی):

    import requests
    from .models import Currency

    def fetch_and_update_rates(base_toman_rate_for_usd):
        # نرخ‌های ارز خارجی نسبت به دلار را از یک API رایگان جهانی می‌گیریم
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        data = resp.json()
        rates_to_usd = data["rates"]  # مثلاً {"AED": 3.67, "EUR": 0.92, ...}

        # چون نرخ تومان در این API موجود نیست، آن را دستی/از منبع دیگر می‌گیریم
        usd_to_toman = base_toman_rate_for_usd

        updated = []
        for currency in Currency.objects.filter(auto_update=True).exclude(code="IRT"):
            rate_vs_usd = rates_to_usd.get(currency.code)
            if rate_vs_usd:
                # مقدار هر واحد از این ارز بر حسب تومان
                currency.rate_to_toman = usd_to_toman / rate_vs_usd
                currency.save(update_fields=["rate_to_toman", "updated_at"])
                updated.append(currency.code)
        return updated
"""


def fetch_and_update_rates(*args, **kwargs):
    """
    نسخه‌ی فعلی: هنوز پیاده‌سازی نشده است.
    وقتی آماده بودید، طبق نمونه‌ی بالای همین فایل تکمیلش کنید.
    """
    raise NotImplementedError(
        "دریافت خودکار نرخ ارز هنوز فعال نشده است. "
        "فعلاً نرخ‌ها را از پنل ادمین (بخش واحدهای پول) دستی وارد کنید."
    )
