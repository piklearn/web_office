from django.contrib import admin
from django.utils.html import format_html
from .models import Currency, Category, Product, ProductFeature


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "rate_to_toman", "is_default", "is_active", "updated_at")
    list_editable = ("rate_to_toman", "is_default", "is_active")
    search_fields = ("code", "name")
    ordering = ("code",)

    fieldsets = (
        (None, {"fields": ("code", "name", "symbol")}),
        ("نرخ تبدیل", {
            "fields": ("rate_to_toman",),
            "description": ("نرخ را به‌صورت دستی وارد کنید: هر ۱ واحد از این ارز معادل چند تومان است. "
                             "برای خودِ تومان مقدار ۱ را وارد کنید. "
                             "دریافت خودکار آنلاین این نرخ‌ها در نسخه‌های بعدی اضافه خواهد شد."),
        }),
        ("وضعیت", {"fields": ("is_default", "is_active", "auto_update")}),
    )


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = ("title", "value", "order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "sku", "category", "display_price", "stock", "is_active", "created_at")
    list_filter = ("category", "currency", "is_active")
    search_fields = ("name", "sku", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductFeatureInline]
    list_editable = ("stock", "is_active")

    fieldsets = (
        ("اطلاعات کلی", {
            "fields": ("name", "slug", "category", "sku", "image"),
        }),
        ("توضیحات", {
            "fields": ("short_description", "description"),
        }),
        ("قیمت‌گذاری و موجودی", {
            "fields": ("price", "currency", "stock"),
        }),
        ("وضعیت", {
            "fields": ("is_active",),
        }),
    )

    def display_price(self, obj):
        return f"{obj.price:,} {obj.currency.symbol or obj.currency.code}"
    display_price.short_description = "قیمت"

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:8px;" />', obj.image.url)
        return "—"
    thumbnail.short_description = "تصویر"
