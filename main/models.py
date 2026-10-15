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


# ───────────── چت آنلاین با بازدیدکنندگان ─────────────
class LiveChatConversation(models.Model):
    """گفتگوی بازدیدکننده با تیم دفتر."""

    class Status(models.TextChoices):
        OPEN = "open", "باز"
        CLOSED = "closed", "بسته"

    session_key = models.CharField("کلید نشست", max_length=64, db_index=True)
    visitor_name = models.CharField("نام بازدیدکننده", max_length=100)
    visitor_phone = models.CharField("شماره تماس", max_length=30, blank=True)
    status = models.CharField("وضعیت", max_length=10, choices=Status.choices,
                              default=Status.OPEN, db_index=True)
    assigned_to = models.ForeignKey(
        "auth.User", verbose_name="مسئول پاسخ",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="livechat_assigned",
    )
    created_at = models.DateTimeField("شروع", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین فعالیت", auto_now=True)
    last_message_at = models.DateTimeField("آخرین پیام", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "گفتگوی آنلاین"
        verbose_name_plural = "گفتگوهای آنلاین"
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return f"{self.visitor_name} ({self.get_status_display()})"

    @property
    def unread_for_staff(self):
        return self.messages.filter(is_from_visitor=True, read_by_staff=False).count()


class LiveChatMessage(models.Model):
    conversation = models.ForeignKey(
        LiveChatConversation, verbose_name="گفتگو",
        on_delete=models.CASCADE, related_name="messages",
    )
    is_from_visitor = models.BooleanField("از طرف بازدیدکننده", default=True)
    staff = models.ForeignKey(
        "auth.User", verbose_name="کارمند",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="livechat_sent",
    )
    text = models.TextField("متن پیام", max_length=2000)
    created_at = models.DateTimeField("زمان", auto_now_add=True)
    read_by_staff = models.BooleanField("خوانده‌شده توسط کارمند", default=False)
    read_by_visitor = models.BooleanField("خوانده‌شده توسط بازدیدکننده", default=False)

    class Meta:
        verbose_name = "پیام چت آنلاین"
        verbose_name_plural = "پیام‌های چت آنلاین"
        ordering = ["created_at"]

    def __str__(self):
        who = self.visitor_name if self.is_from_visitor else (self.staff or "کارمند")
        return f"{who}: {self.text[:40]}"

    @property
    def visitor_name(self):
        return self.conversation.visitor_name
