from django import template

from crm.models import TaskStatus

register = template.Library()

BADGES = {
    # مشتری / کار / فروش (مقدارها بین مدل‌ها مشترک‌اند و رنگ یکسان دارند)
    "new": "bg-sky-100 text-sky-700",
    "reviewing": "bg-amber-100 text-amber-700",
    "active": "bg-emerald-100 text-emerald-700",
    "inactive": "bg-slate-100 text-slate-600",
    "dropped": "bg-red-100 text-red-700",
    "waiting_customer": "bg-violet-100 text-violet-700",
    "waiting_colleague": "bg-indigo-100 text-indigo-700",
    "needs_followup": "bg-orange-100 text-orange-700",
    "done": "bg-emerald-100 text-emerald-700",
    "canceled": "bg-slate-100 text-slate-500",
    "initial": "bg-slate-100 text-slate-600",
    "introduced": "bg-sky-100 text-sky-700",
    "waiting_decision": "bg-violet-100 text-violet-700",
    "waiting_payment": "bg-orange-100 text-orange-700",
    "purchased": "bg-emerald-100 text-emerald-700",
}


@register.filter
def badge(value):
    """کلاس‌های Tailwind برای نشان رنگی وضعیت."""
    return BADGES.get(str(value), "bg-slate-100 text-slate-600")


@register.simple_tag
def task_statuses():
    return TaskStatus.choices


@register.filter
def money(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


@register.filter
def initial(value):
    return (str(value).strip() or "?")[:1]


@register.filter
def activity_icon(text):
    """آیکن تایم‌لاین بر اساس ابتدای جملهٔ ثبت‌شده توسط signals.py."""
    text = str(text)
    for prefix, icon in (("پرداخت", "💰"), ("نرم‌افزار", "💻"), ("درخواست", "📩"),
                         ("کار", "✅"), ("وضعیت کار", "🔄"), ("مشتری", "🆕")):
        if text.startswith(prefix):
            return icon
    return "•"
