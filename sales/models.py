from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Currency(models.Model):
    """
    واحد پول قابل استفاده برای قیمت‌گذاری کالاها.
    از پیش، تومان/دلار/درهم قابل تعریف هستند و می‌توانید هر واحد دیگری هم اضافه کنید.

    نرخ تبدیل (rate_to_toman) فعلاً به‌صورت دستی در پنل ادمین وارد می‌شود.
    ساختار به‌گونه‌ای است که بعداً می‌توان یک دکمه/دستور برای دریافت خودکار
    نرخ ارزهای خارجی از اینترنت اضافه کرد (نگاه کنید به sales/services.py) و
    فقط نرخ پایه (مثلاً تومان به دلار) را به‌صورت دستی وارد کرد - چون نرخ تومان
    در APIهای رایگان جهانی به دلیل تحریم‌ها معمولاً موجود نیست.
    """

    code = models.CharField("کد ارز", max_length=10, unique=True,
                             help_text="مثلاً: USD ، AED ، IRT")
    name = models.CharField("نام واحد", max_length=100,
                             help_text="مثلاً: دلار آمریکا، درهم امارات، تومان")
    symbol = models.CharField("نماد/علامت", max_length=10, blank=True,
                               help_text="مثلاً: $ یا د.إ یا تومان")

    rate_to_toman = models.DecimalField(
        "نرخ برابری با تومان", max_digits=18, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="هر یک واحد از این ارز معادل چند تومان است؟ (برای خود تومان مقدار 1 وارد کنید)"
    )

    is_default = models.BooleanField(
        "واحد پیش‌فرض فروشگاه", default=False,
        help_text="در صورت فعال بودن، به‌عنوان واحد پیش‌فرض نمایش قیمت‌ها استفاده می‌شود"
    )
    auto_update = models.BooleanField(
        "دریافت خودکار نرخ از اینترنت (به‌زودی)", default=False,
        help_text="این گزینه برای آینده رزرو شده؛ فعلاً همه‌ی نرخ‌ها دستی وارد می‌شوند"
    )
    is_active = models.BooleanField("فعال", default=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "واحد پول"
        verbose_name_plural = "واحدهای پول"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Currency.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def to_toman(self, amount):
        """تبدیل مبلغی از این واحد به تومان."""
        return (Decimal(amount) * self.rate_to_toman).quantize(Decimal("1"))


class Category(models.Model):
    """دسته‌بندی کالاها (اختیاری، برای سازمان‌دهی فروشگاه)."""

    name = models.CharField("نام دسته", max_length=150)
    slug = models.SlugField("اسلاگ", max_length=170, unique=True, blank=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    """کالای قابل فروش، با قیمت در واحد دلخواه (تومان، دلار، درهم یا هر ارز دیگری)."""

    name = models.CharField("نام کالا", max_length=200)
    slug = models.SlugField("اسلاگ (آدرس صفحه)", max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, verbose_name="دسته‌بندی", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="products")
    sku = models.CharField("کد کالا (SKU)", max_length=60, unique=True)

    short_description = models.CharField("توضیح کوتاه", max_length=300, blank=True,
                                          help_text="در لیست کالاها نمایش داده می‌شود")
    description = models.TextField("توضیحات کامل", blank=True)

    price = models.DecimalField("قیمت", max_digits=18, decimal_places=2,
                                 validators=[MinValueValidator(Decimal("0"))])
    currency = models.ForeignKey(Currency, verbose_name="واحد قیمت",
                                  on_delete=models.PROTECT, related_name="products")

    stock = models.PositiveIntegerField("موجودی انبار", default=0)
    image = models.ImageField("تصویر کالا", upload_to="products/", blank=True, null=True)

    is_active = models.BooleanField("فعال / نمایش در فروشگاه", default=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True) or "product"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sales:product_detail", kwargs={"slug": self.slug})

    @property
    def price_in_toman(self):
        """قیمت معادل به تومان، بر اساس نرخ ثبت‌شده برای واحد این کالا."""
        return self.currency.to_toman(self.price)

    @property
    def in_stock(self):
        return self.stock > 0


class ProductFeature(models.Model):
    """
    ویژگی/مشخصه‌ی فنی کالا به‌صورت جفت عنوان-مقدار.
    مثال: رنگ = قرمز، وزن = ۲ کیلوگرم، گارانتی = ۱۸ ماهه
    """

    product = models.ForeignKey(Product, verbose_name="کالا", on_delete=models.CASCADE,
                                 related_name="features")
    title = models.CharField("عنوان ویژگی", max_length=100)
    value = models.CharField("مقدار", max_length=300)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "ویژگی کالا"
        verbose_name_plural = "ویژگی‌های کالا"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title}: {self.value}"
