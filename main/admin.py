from django.contrib import admin
from .models import SiteSettings, LiveChatConversation, LiveChatMessage


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
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class LiveChatMessageInline(admin.TabularInline):
    model = LiveChatMessage
    extra = 0
    readonly_fields = ("is_from_visitor", "staff", "text", "created_at", "read_by_staff", "read_by_visitor")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LiveChatConversation)
class LiveChatConversationAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "visitor_phone", "status", "assigned_to",
                    "unread_for_staff", "last_message_at", "created_at")
    list_filter = ("status",)
    search_fields = ("visitor_name", "visitor_phone", "session_key")
    readonly_fields = ("session_key", "created_at", "updated_at", "last_message_at")
    inlines = [LiveChatMessageInline]
    date_hierarchy = "created_at"
