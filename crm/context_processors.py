from django.db.models import Count, Q
from django.utils import timezone

from .models import Task, is_manager


def crm_reminders(request):
    """تعداد کارهای عقب‌افتاده و امروز + پیام‌های خوانده‌نشده چت بازدیدکننده."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    today = timezone.localdate()
    qs = Task.objects.open()
    if not is_manager(user):
        qs = qs.filter(assignee=user)
    agg = qs.aggregate(
        overdue=Count("pk", filter=Q(due_date__lt=today)),
        today=Count("pk", filter=Q(due_date=today)),
    )
    livechat_unread = 0
    try:
        from main.models import LiveChatMessage, LiveChatConversation
        livechat_unread = LiveChatMessage.objects.filter(
            is_from_visitor=True,
            read_by_staff=False,
            conversation__status=LiveChatConversation.Status.OPEN,
        ).count()
    except Exception:
        pass
    return {
        "crm_overdue_count": agg["overdue"],
        "crm_today_count": agg["today"],
        "livechat_unread": livechat_unread,
    }
