from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("crm", "0005_chatthread_chatmessage_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserCRMSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("theme", models.CharField(
                    choices=[
                        ("default", "پیش‌فرض (آبی)"),
                        ("ocean", "اقیانوس"),
                        ("forest", "جنگلی"),
                        ("sunset", "غروب"),
                        ("purple", "بنفش"),
                        ("rose", "صورتی"),
                        ("dark", "تیره"),
                    ],
                    default="default",
                    max_length=20,
                    verbose_name="تم",
                )),
                ("dashboard_widgets", models.JSONField(
                    blank=True,
                    default=list,
                    help_text="لیست کلید ویجت‌هایی که در داشبورد اصلی نمایش داده شوند",
                    verbose_name="ویجت‌های داشبورد",
                )),
                ("customer_list_fields", models.JSONField(
                    blank=True,
                    default=list,
                    help_text="فیلدهایی که کنار نام مشتری در لیست مشتریان نشان داده شوند",
                    verbose_name="فیلدهای کنار نام مشتری",
                )),
                ("is_configured", models.BooleanField(
                    default=False,
                    help_text="اگر False باشد، کاربر برای اولین بار به صفحه تنظیمات هدایت می‌شود",
                    verbose_name="تنظیمات اولیه انجام شده",
                )),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="crm_settings",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="کاربر",
                )),
            ],
            options={
                "verbose_name": "تنظیمات CRM کاربر",
                "verbose_name_plural": "تنظیمات CRM کاربران",
            },
        ),
    ]
