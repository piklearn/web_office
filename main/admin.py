from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("هویت سایت", {
            "fields": ("site_name", "logo", "tagline"),
        }),
        ("صفحه اصلی (هیرو)", {
            "fields": ("hero_title", "hero_subtitle"),
        }),
        ("پشتیبانی فوری", {
            "fields": ("urgent_support_title", "urgent_support_text", "urgent_support_phone"),
        }),
        ("اطلاعات تماس و آدرس", {
            "fields": ("address", "phone", "email", "working_hours", "map_embed_url"),
        }),
        ("شبکه‌های اجتماعی", {
            "fields": ("instagram_url", "telegram_url", "whatsapp_number"),
            "classes": ("collapse",),
        }),
        ("درباره‌ی ما", {
            "fields": ("about_text",),
        }),
    )

    def has_add_permission(self, request):
        # فقط یک رکورد تنظیمات مجاز است
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
