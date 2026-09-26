from django.db import models


class DeviceType(models.TextChoices):
    PC = "pc", "سیستم (کیس)"
    LAPTOP = "laptop", "لپ‌تاپ"
    PRINTER = "printer", "پرینتر"
    MONITOR = "monitor", "مانیتور"
    NETWORK = "network", "تجهیزات شبکه"
    OTHER = "other", "سایر"


class CaseStatus(models.TextChoices):
    RECEIVED = "received", "دریافت شده"
    IN_PROGRESS = "in_progress", "در حال بررسی"
    REPAIRING = "repairing", "در حال تعمیر"
    WAITING_PARTS = "waiting_parts", "در انتظار قطعه"
    READY = "ready", "آماده تحویل"
    DELIVERED = "delivered", "تحویل داده شده"
    CANCELED = "canceled", "لغو شده"


class RepairCase(models.Model):
    """
    ثبت سیستم/کیس و سایر تجهیزاتی که برای تعمیر به دفتر آورده می‌شود.
    کد پیگیری بر اساس شماره تماس مشتری ساخته می‌شود.
    """

    # اطلاعات مشتری
    customer_name = models.CharField("نام مشتری", max_length=150)
    phone = models.CharField("شماره تماس مشتری", max_length=20,
                              help_text="این شماره مبنای کد پیگیری خواهد بود")

    # کد پیگیری - بر اساس شماره مشتری ساخته و به‌صورت یکتا ذخیره می‌شود
    tracking_code = models.CharField("کد پیگیری", max_length=30, unique=True,
                                      blank=True, editable=False)

    # اطلاعات دستگاه
    device_type = models.CharField("نوع دستگاه", max_length=20,
                                    choices=DeviceType.choices, default=DeviceType.PC)
    device_model = models.CharField("مدل / برند دستگاه", max_length=150, blank=True)
    serial_number = models.CharField("شماره سریال (در صورت وجود)", max_length=100, blank=True)
    problem_description = models.TextField("شرح مشکل / درخواست مشتری")

    # وضعیت و پیگیری داخلی
    status = models.CharField("وضعیت", max_length=20,
                               choices=CaseStatus.choices, default=CaseStatus.RECEIVED)
    technician_notes = models.TextField("یادداشت‌های فنی (داخلی)", blank=True,
                                         help_text="این بخش برای مشتری نمایش داده نمی‌شود")
    estimated_cost = models.DecimalField("هزینه تخمینی (تومان)", max_digits=12, decimal_places=0,
                                          null=True, blank=True)

    received_at = models.DateTimeField("تاریخ دریافت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)
    delivered_at = models.DateTimeField("تاریخ تحویل", null=True, blank=True)

    class Meta:
        verbose_name = "کیس تعمیر"
        verbose_name_plural = "کیس‌های تعمیر"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.tracking_code} - {self.customer_name}"

    def generate_tracking_code(self):
        """کد پیگیری را بر اساس شماره مشتری می‌سازد و در صورت تکرار، پسوند عددی اضافه می‌کند."""
        digits = "".join(ch for ch in self.phone if ch.isdigit())
        base_code = digits[-10:] if digits else "0000000000"

        existing_count = RepairCase.objects.filter(phone=self.phone).exclude(pk=self.pk).count()
        if existing_count == 0:
            return base_code
        return f"{base_code}-{existing_count + 1}"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)
