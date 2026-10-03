from django.db import models


class SiteSettings(models.Model):
    """
    تنظیمات کلی سایت - به‌صورت تک‌رکورد (Singleton).
    همه‌ی این موارد از پنل ادمین قابل ویرایش هستند.
    """

    # هویت سایت
    site_name = models.CharField("نام سایت / دفتر", max_length=150, default="دفتر ما")
    logo = models.ImageField("لوگو", upload_to="site/", blank=True, null=True)
    tagline = models.CharField("شعار کوتاه سایت", max_length=200, blank=True,
                                help_text="مثلاً: خدمات تعمیرات تخصصی")

    # بخش هیرو (صفحه اصلی)
    hero_title = models.CharField("عنوان اصلی صفحه نخست", max_length=200,
                                   default="به دفتر ما خوش آمدید")
    hero_subtitle = models.TextField("توضیح زیر عنوان اصلی", blank=True)

    # اطلاعات تماس و آدرس
    address = models.TextField("آدرس دفتر", blank=True)
    phone = models.CharField("شماره تماس دفتر", max_length=30, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    working_hours = models.CharField("ساعات کاری", max_length=150, blank=True,
                                      help_text="مثلاً: شنبه تا چهارشنبه، ۹ الی ۱۸")
    map_embed_url = models.URLField("لینک نقشه (Google Maps Embed)", blank=True)

    # شبکه‌های اجتماعی (اختیاری)
    instagram_url = models.URLField("اینستاگرام", blank=True)
    telegram_url = models.URLField("تلگرام", blank=True)
    whatsapp_number = models.CharField("شماره واتساپ", max_length=30, blank=True)

    # پشتیبانی فوری / پیگیری سریع
    urgent_support_title = models.CharField("عنوان پشتیبانی فوری", max_length=150,
                                             default="پشتیبانی فوری")
    urgent_support_text = models.TextField("توضیح پشتیبانی فوری", blank=True,
                                            default="برای دریافت پشتیبانی فوری با شماره زیر تماس بگیرید.")
    urgent_support_phone = models.CharField("شماره تماس پشتیبانی فوری", max_length=30, blank=True)

    # درباره‌ی ما
    about_text = models.TextField("متن درباره‌ی دفتر", blank=True)

    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # الگوی Singleton: همیشه فقط رکورد با pk=1 ذخیره می‌شود
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # جلوگیری از حذف تنظیمات سایت

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class UserAvatar(models.Model):
    """انتخاب تصویر پروفایل پیش‌فرض هر کاربر."""

    user = models.OneToOneField("auth.User", verbose_name="کاربر",
                                on_delete=models.CASCADE, related_name="avatar_choice")
    avatar = models.CharField("تصویر پروفایل", max_length=20)

    class Meta:
        verbose_name = "تصویر پروفایل کاربر"
        verbose_name_plural = "تصویر پروفایل کاربران"

    def __str__(self):
        return f"{self.user} — {self.avatar}"
