from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0002_useravatar"),
    ]

    operations = [
        migrations.CreateModel(
            name="LiveChatConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=64, verbose_name="کلید نشست")),
                ("visitor_name", models.CharField(max_length=100, verbose_name="نام بازدیدکننده")),
                ("visitor_phone", models.CharField(blank=True, max_length=30, verbose_name="شماره تماس")),
                ("status", models.CharField(choices=[("open", "باز"), ("closed", "بسته")], db_index=True, default="open", max_length=10, verbose_name="وضعیت")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="شروع")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین فعالیت")),
                ("last_message_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="آخرین پیام")),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="livechat_assigned", to=settings.AUTH_USER_MODEL, verbose_name="مسئول پاسخ")),
            ],
            options={
                "verbose_name": "گفتگوی آنلاین",
                "verbose_name_plural": "گفتگوهای آنلاین",
                "ordering": ["-last_message_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LiveChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_from_visitor", models.BooleanField(default=True, verbose_name="از طرف بازدیدکننده")),
                ("text", models.TextField(max_length=2000, verbose_name="متن پیام")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان")),
                ("read_by_staff", models.BooleanField(default=False, verbose_name="خوانده‌شده توسط کارمند")),
                ("read_by_visitor", models.BooleanField(default=False, verbose_name="خوانده‌شده توسط بازدیدکننده")),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="main.livechatconversation", verbose_name="گفتگو")),
                ("staff", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="livechat_sent", to=settings.AUTH_USER_MODEL, verbose_name="کارمند")),
            ],
            options={
                "verbose_name": "پیام چت آنلاین",
                "verbose_name_plural": "پیام‌های چت آنلاین",
                "ordering": ["created_at"],
            },
        ),
    ]
