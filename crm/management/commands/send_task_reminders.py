"""یادآوری ایمیلی کارهای عقب‌افتاده و امروز برای مسئول هر کار.

اجرا (مثلاً هر روز صبح با cron):
    python3 manage.py send_task_reminders
    python3 manage.py send_task_reminders --dry-run
"""
from collections import defaultdict

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Task


class Command(BaseCommand):
    help = "ارسال ایمیل یادآوری کارهای عقب‌افتاده و امروز به مسئولان"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="فقط گزارش بده، ایمیل نفرست")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        tasks = (Task.objects.open().filter(due_date__lte=today, assignee__isnull=False)
                 .select_related("customer", "assignee"))
        per_user = defaultdict(list)
        for t in tasks:
            per_user[t.assignee].append(t)

        sent = 0
        for user, items in per_user.items():
            if not user.email:
                self.stdout.write(f"- {user}: ایمیل ندارد، رد شد")
                continue
            lines = [f"• {t.title} — {t.customer} "
                     f"({'عقب‌افتاده' if t.due_date < today else 'امروز'})" for t in items]
            body = "کارهای نیازمند پیگیری شما:\n\n" + "\n".join(lines)
            if not opts["dry_run"]:
                send_mail(f"یادآوری: {len(items)} کار نیاز به پیگیری دارد", body, None, [user.email])
            sent += 1
            self.stdout.write(f"- {user}: {len(items)} کار")
        self.stdout.write(self.style.SUCCESS(f"{sent} کاربر یادآوری {'(آزمایشی) ' if opts['dry_run'] else ''}دریافت کردند."))
