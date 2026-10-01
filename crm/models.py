from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# ───────────── کارکنان و نقش‌ها ─────────────
class Role(models.TextChoices):
    MANAGER = "manager", "مدیر"
    EMPLOYEE = "employee", "کارمند"
    SUPPORT = "support", "پشتیبان"
    SALES = "sales", "فروش"


class EmployeeProfile(models.Model):
    """نقش کارمند. نام، نام کاربری و فعال/غیرفعال از خود User استفاده می‌شود."""
    user = models.OneToOneField(User, verbose_name="کاربر", on_delete=models.CASCADE,
                                related_name="crm_profile")
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.EMPLOYEE)

    class Meta:
        verbose_name = "پروفایل کارمند"
        verbose_name_plural = "کارکنان (نقش‌ها)"

    def __str__(self):
        return f"{self.user} - {self.get_role_display()}"


def get_role(user):
    if user.is_superuser:
        return Role.MANAGER
    profile = getattr(user, "crm_profile", None)
    return profile.role if profile else Role.EMPLOYEE


def is_manager(user):
    return user.is_authenticated and get_role(user) == Role.MANAGER


def can_see_finance(user):
    return user.is_authenticated and get_role(user) in (Role.MANAGER, Role.SALES)


# ───────────── مشتری ─────────────
class CustomerStatus(models.TextChoices):
    NEW = "new", "جدید"
    REVIEWING = "reviewing", "در حال بررسی"
    ACTIVE = "active", "مشتری فعال"
    INACTIVE = "inactive", "مشتری غیرفعال"
    DROPPED = "dropped", "منصرف شده"


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "پرداخت نشده"
    DEPOSIT = "deposit", "بیعانه پرداخت شده"
    INSTALLMENT = "installment", "قسطی"
    SETTLED = "settled", "تسویه شده"


class Customer(models.Model):
    full_name = models.CharField("نام و نام خانوادگی", max_length=150)
    company_name = models.CharField("نام شرکت / کسب‌وکار", max_length=150, blank=True)
    national_id = models.CharField("کد ملی", max_length=15, blank=True, db_index=True)
    mobile = models.CharField("شماره موبایل", max_length=20, blank=True, db_index=True)
    landline = models.CharField("تلفن ثابت", max_length=20, blank=True)
    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)
    address = models.TextField("آدرس", blank=True)
    activity_type = models.CharField("نوع فعالیت", max_length=150, blank=True)
    description = models.TextField("توضیحات", blank=True)
    status = models.CharField("وضعیت مشتری", max_length=20, choices=CustomerStatus.choices,
                              default=CustomerStatus.NEW)
    owner = models.ForeignKey(User, verbose_name="کارمند مسئول", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="customers")
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    total_amount = models.DecimalField("مبلغ کل", max_digits=14, decimal_places=0, default=0)
    payment_status = models.CharField("وضعیت پرداخت", max_length=20,
                                      choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"
        ordering = ["-created_at"]

    def __str__(self):
        return self.company_name or self.full_name

    @property
    def paid_total(self):
        return self.payments.aggregate(s=Sum("amount"))["s"] or 0

    @property
    def remaining(self):
        return self.total_amount - self.paid_total

    @property
    def open_tasks(self):
        return Task.objects.open().filter(customer=self)


class Contact(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="contacts")
    name = models.CharField("نام", max_length=150)
    position = models.CharField("سمت", max_length=100, blank=True)
    phone = models.CharField("شماره تلفن", max_length=20, blank=True)
    description = models.CharField("توضیحات", max_length=250, blank=True)

    class Meta:
        verbose_name = "فرد تماس"
        verbose_name_plural = "افراد تماس"

    def __str__(self):
        return f"{self.name} ({self.position})" if self.position else self.name


# ───────────── نرم‌افزارها ─────────────
class Software(models.Model):
    name = models.CharField("نام نرم‌افزار", max_length=100, unique=True)

    class Meta:
        verbose_name = "نرم‌افزار"
        verbose_name_plural = "نرم‌افزارها"

    def __str__(self):
        return self.name


class SaleStatus(models.TextChoices):
    INITIAL = "initial", "درخواست اولیه"
    REVIEWING = "reviewing", "در حال بررسی"
    INTRODUCED = "introduced", "نرم‌افزار معرفی شد"
    WAITING_DECISION = "waiting_decision", "منتظر تصمیم مشتری"
    WAITING_PAYMENT = "waiting_payment", "در انتظار پرداخت"
    PURCHASED = "purchased", "خریداری شد"
    DROPPED = "dropped", "منصرف شد"


class DropReason(models.TextChoices):
    PRICE = "price", "قیمت"
    OTHER_SOFTWARE = "other_software", "انتخاب نرم‌افزار دیگر"
    NO_NEED = "no_need", "فعلاً نیاز ندارد"
    OTHER_COMPANY = "other_company", "خرید از شرکت دیگر"
    OTHER = "other", "سایر"


class CustomerSoftware(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="softwares")
    software = models.ForeignKey(Software, verbose_name="نرم‌افزار", on_delete=models.PROTECT)
    is_purchased = models.BooleanField("خریداری شده", default=False,
                                       help_text="اگر تیک نخورد یعنی مشتری فقط در حال بررسی است")
    sale_status = models.CharField("وضعیت فروش", max_length=20, choices=SaleStatus.choices,
                                   default=SaleStatus.INITIAL)
    drop_reason = models.CharField("دلیل انصراف", max_length=20, choices=DropReason.choices,
                                   blank=True)
    note = models.CharField("توضیحات", max_length=250, blank=True)

    class Meta:
        verbose_name = "نرم‌افزار مشتری"
        verbose_name_plural = "نرم‌افزارهای مشتری"

    def __str__(self):
        return f"{self.customer} - {self.software}"

    def save(self, *args, **kwargs):
        if self.sale_status == SaleStatus.PURCHASED:
            self.is_purchased = True
        super().save(*args, **kwargs)


# ───────────── پرداخت‌ها ─────────────
class PaymentMethod(models.TextChoices):
    CASH = "cash", "نقدی"
    CARD = "card", "کارت به کارت"
    POS = "pos", "کارتخوان"
    CHEQUE = "cheque", "چک"
    OTHER = "other", "سایر"


class Payment(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="payments")
    date = models.DateField("تاریخ", default=timezone.localdate)
    amount = models.DecimalField("مبلغ", max_digits=14, decimal_places=0)
    method = models.CharField("روش پرداخت", max_length=20, choices=PaymentMethod.choices,
                              default=PaymentMethod.CASH)
    description = models.CharField("توضیحات", max_length=250, blank=True)
    created_by = models.ForeignKey(User, verbose_name="ثبت‌کننده", null=True, blank=True,
                                   on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.customer} - {self.amount:,}"


# ───────────── درخواست و Task ─────────────
class Request(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="requests")
    subject = models.CharField("موضوع", max_length=200)
    description = models.TextField("توضیحات", blank=True)
    created_by = models.ForeignKey(User, verbose_name="ثبت‌کننده", null=True, blank=True,
                                   on_delete=models.SET_NULL)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "درخواست / مشکل"
        verbose_name_plural = "درخواست‌ها / مشکلات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer}: {self.subject}"

    @property
    def is_open(self):
        return self.tasks.exclude(status__in=Task.CLOSED).exists() or not self.tasks.exists()


class TaskStatus(models.TextChoices):
    NEW = "new", "جدید"
    REVIEWING = "reviewing", "در حال بررسی"
    WAITING_CUSTOMER = "waiting_customer", "منتظر مشتری"
    WAITING_COLLEAGUE = "waiting_colleague", "منتظر همکار"
    NEEDS_FOLLOWUP = "needs_followup", "نیاز به پیگیری"
    DONE = "done", "انجام شد"
    CANCELED = "canceled", "لغو شد"


class TaskQuerySet(models.QuerySet):
    def open(self):
        return self.exclude(status__in=Task.CLOSED)


class Task(models.Model):
    CLOSED = (TaskStatus.DONE, TaskStatus.CANCELED)

    request = models.ForeignKey(Request, verbose_name="درخواست", null=True, blank=True,
                                on_delete=models.CASCADE, related_name="tasks")
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="tasks")
    title = models.CharField("عنوان کار", max_length=200)
    assignee = models.ForeignKey(User, verbose_name="مسئول", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="crm_tasks")
    due_date = models.DateField("موعد", null=True, blank=True)
    due_time = models.TimeField("ساعت", null=True, blank=True)
    status = models.CharField("وضعیت", max_length=20, choices=TaskStatus.choices,
                              default=TaskStatus.NEW)
    result = models.CharField("نتیجه", max_length=250, blank=True)
    result_note = models.TextField("توضیحات نتیجه", blank=True)
    created_by = models.ForeignKey(User, verbose_name="ایجادکننده", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    completed_at = models.DateTimeField("تاریخ اتمام", null=True, blank=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        verbose_name = "وظیفه / پیگیری"
        verbose_name_plural = "وظایف و پیگیری‌ها"
        ordering = ["due_date", "due_time"]

    def __str__(self):
        return f"{self.title} ({self.customer})"

    @property
    def is_closed(self):
        return self.status in self.CLOSED

    @property
    def is_overdue(self):
        return bool(self.due_date and not self.is_closed and self.due_date < timezone.localdate())

    def save(self, *args, **kwargs):
        if self.customer_id is None and self.request_id:
            self.customer = self.request.customer
        if self.is_closed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_closed:
            self.completed_at = None
        super().save(*args, **kwargs)


# ───────────── تاریخچه فعالیت‌ها ─────────────
class Activity(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="مشتری", on_delete=models.CASCADE,
                                 related_name="activities")
    text = models.CharField("شرح", max_length=400)
    user = models.ForeignKey(User, verbose_name="کاربر", null=True, blank=True,
                             on_delete=models.SET_NULL)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "فعالیت"
        verbose_name_plural = "تاریخچه فعالیت‌ها"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.text
