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


THEME_CSS = {
    "default": "",
    "ocean": """
[data-crm-theme="ocean"] .bg-brand-blue-50 { background-color: #ecfeff !important; }
[data-crm-theme="ocean"] .bg-brand-blue-100 { background-color: #cffafe !important; }
[data-crm-theme="ocean"] .bg-brand-blue-600 { background-color: #0891b2 !important; }
[data-crm-theme="ocean"] .bg-brand-blue-700,
[data-crm-theme="ocean"] .hover\\:bg-brand-blue-700:hover { background-color: #0e7490 !important; }
[data-crm-theme="ocean"] .text-brand-blue-600,
[data-crm-theme="ocean"] .text-brand-blue-700,
[data-crm-theme="ocean"] .hover\\:text-brand-blue-600:hover,
[data-crm-theme="ocean"] .hover\\:text-brand-blue-700:hover { color: #0e7490 !important; }
[data-crm-theme="ocean"] .border-brand-blue-400,
[data-crm-theme="ocean"] .hover\\:border-brand-blue-400:hover { border-color: #22d3ee !important; }
[data-crm-theme="ocean"] .ring-brand-blue-400 { --tw-ring-color: #22d3ee !important; }
""",
    "forest": """
[data-crm-theme="forest"] .bg-brand-blue-50 { background-color: #ecfdf5 !important; }
[data-crm-theme="forest"] .bg-brand-blue-100 { background-color: #d1fae5 !important; }
[data-crm-theme="forest"] .bg-brand-blue-600 { background-color: #059669 !important; }
[data-crm-theme="forest"] .bg-brand-blue-700,
[data-crm-theme="forest"] .hover\\:bg-brand-blue-700:hover { background-color: #047857 !important; }
[data-crm-theme="forest"] .text-brand-blue-600,
[data-crm-theme="forest"] .text-brand-blue-700,
[data-crm-theme="forest"] .hover\\:text-brand-blue-600:hover { color: #047857 !important; }
[data-crm-theme="forest"] .border-brand-blue-400,
[data-crm-theme="forest"] .hover\\:border-brand-blue-400:hover { border-color: #34d399 !important; }
""",
    "sunset": """
[data-crm-theme="sunset"] .bg-brand-blue-50 { background-color: #fff7ed !important; }
[data-crm-theme="sunset"] .bg-brand-blue-100 { background-color: #ffedd5 !important; }
[data-crm-theme="sunset"] .bg-brand-blue-600 { background-color: #ea580c !important; }
[data-crm-theme="sunset"] .bg-brand-blue-700,
[data-crm-theme="sunset"] .hover\\:bg-brand-blue-700:hover { background-color: #c2410c !important; }
[data-crm-theme="sunset"] .text-brand-blue-600,
[data-crm-theme="sunset"] .text-brand-blue-700,
[data-crm-theme="sunset"] .hover\\:text-brand-blue-600:hover { color: #c2410c !important; }
[data-crm-theme="sunset"] .border-brand-blue-400,
[data-crm-theme="sunset"] .hover\\:border-brand-blue-400:hover { border-color: #fb923c !important; }
""",
    "purple": """
[data-crm-theme="purple"] .bg-brand-blue-50 { background-color: #f5f3ff !important; }
[data-crm-theme="purple"] .bg-brand-blue-100 { background-color: #ede9fe !important; }
[data-crm-theme="purple"] .bg-brand-blue-600 { background-color: #7c3aed !important; }
[data-crm-theme="purple"] .bg-brand-blue-700,
[data-crm-theme="purple"] .hover\\:bg-brand-blue-700:hover { background-color: #6d28d9 !important; }
[data-crm-theme="purple"] .text-brand-blue-600,
[data-crm-theme="purple"] .text-brand-blue-700,
[data-crm-theme="purple"] .hover\\:text-brand-blue-600:hover { color: #6d28d9 !important; }
[data-crm-theme="purple"] .border-brand-blue-400,
[data-crm-theme="purple"] .hover\\:border-brand-blue-400:hover { border-color: #a78bfa !important; }
""",
    "rose": """
[data-crm-theme="rose"] .bg-brand-blue-50 { background-color: #fff1f2 !important; }
[data-crm-theme="rose"] .bg-brand-blue-100 { background-color: #ffe4e6 !important; }
[data-crm-theme="rose"] .bg-brand-blue-600 { background-color: #e11d48 !important; }
[data-crm-theme="rose"] .bg-brand-blue-700,
[data-crm-theme="rose"] .hover\\:bg-brand-blue-700:hover { background-color: #be123c !important; }
[data-crm-theme="rose"] .text-brand-blue-600,
[data-crm-theme="rose"] .text-brand-blue-700,
[data-crm-theme="rose"] .hover\\:text-brand-blue-600:hover { color: #be123c !important; }
[data-crm-theme="rose"] .border-brand-blue-400,
[data-crm-theme="rose"] .hover\\:border-brand-blue-400:hover { border-color: #fb7185 !important; }
""",
    "dark": """
/* ── تم تیره: پس‌زمینه و متن پایه ── */
[data-crm-theme="dark"] {
  color-scheme: dark;
}
[data-crm-theme="dark"] body,
body[data-crm-theme="dark"] {
  background-color: #0b1220 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .bg-slate-50,
[data-crm-theme="dark"] .bg-stone-50,
[data-crm-theme="dark"] .bg-gray-50 {
  background-color: #0b1220 !important;
}
[data-crm-theme="dark"] .bg-white,
[data-crm-theme="dark"] .bg-white\\/80,
[data-crm-theme="dark"] .bg-white\\/90 {
  background-color: #1a2332 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .bg-slate-100,
[data-crm-theme="dark"] .bg-stone-100,
[data-crm-theme="dark"] .bg-gray-100 {
  background-color: #243044 !important;
}
[data-crm-theme="dark"] .bg-slate-200 {
  background-color: #334155 !important;
}
[data-crm-theme="dark"] .hover\\:bg-slate-50:hover,
[data-crm-theme="dark"] .hover\\:bg-stone-50:hover {
  background-color: #243044 !important;
}

/* متن‌ها */
[data-crm-theme="dark"] .text-slate-900,
[data-crm-theme="dark"] .text-slate-800,
[data-crm-theme="dark"] .text-stone-800,
[data-crm-theme="dark"] .text-gray-900 {
  color: #f1f5f9 !important;
}
[data-crm-theme="dark"] .text-slate-700,
[data-crm-theme="dark"] .text-stone-700 {
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .text-slate-600,
[data-crm-theme="dark"] .text-stone-600 {
  color: #cbd5e1 !important;
}
[data-crm-theme="dark"] .text-slate-500,
[data-crm-theme="dark"] .text-slate-400,
[data-crm-theme="dark"] .text-stone-400 {
  color: #94a3b8 !important;
}

/* بوردرها */
[data-crm-theme="dark"] .border,
[data-crm-theme="dark"] .border-b,
[data-crm-theme="dark"] .border-t,
[data-crm-theme="dark"] .border-l,
[data-crm-theme="dark"] .border-r,
[data-crm-theme="dark"] .border-slate-100,
[data-crm-theme="dark"] .border-slate-200,
[data-crm-theme="dark"] .border-stone-100,
[data-crm-theme="dark"] .border-stone-200,
[data-crm-theme="dark"] .divide-y > :not([hidden]) ~ :not([hidden]) {
  border-color: #334155 !important;
}
[data-crm-theme="dark"] .border-red-100,
[data-crm-theme="dark"] .border-red-300 { border-color: #7f1d1d !important; }
[data-crm-theme="dark"] .border-orange-100 { border-color: #7c2d12 !important; }
[data-crm-theme="dark"] .border-amber-100 { border-color: #78350f !important; }
[data-crm-theme="dark"] .border-sky-100 { border-color: #0c4a6e !important; }

/* هدر و فوتر و منوها */
[data-crm-theme="dark"] header,
[data-crm-theme="dark"] footer {
  background-color: rgba(15, 23, 42, 0.92) !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] header .text-slate-800,
[data-crm-theme="dark"] header .text-slate-600 {
  color: #e2e8f0 !important;
}

/* کارت‌های رنگی بخش‌های داشبورد */
[data-crm-theme="dark"] .bg-red-50 { background-color: #450a0a !important; }
[data-crm-theme="dark"] .bg-orange-50 { background-color: #431407 !important; }
[data-crm-theme="dark"] .bg-amber-50 { background-color: #451a03 !important; }
[data-crm-theme="dark"] .bg-sky-50 { background-color: #0c4a6e !important; }
[data-crm-theme="dark"] .bg-emerald-50 { background-color: #064e3b !important; }
[data-crm-theme="dark"] .bg-violet-50 { background-color: #2e1065 !important; }
[data-crm-theme="dark"] .bg-brand-blue-50 { background-color: #132d4c !important; }
[data-crm-theme="dark"] .bg-brand-blue-100 { background-color: #1a4876 !important; color: #93d3fd !important; }

/* برند آبی در تم تیره کمی روشن‌تر */
[data-crm-theme="dark"] .bg-brand-blue-600 { background-color: #3b82f6 !important; }
[data-crm-theme="dark"] .bg-brand-blue-700,
[data-crm-theme="dark"] .hover\\:bg-brand-blue-700:hover { background-color: #2563eb !important; }
[data-crm-theme="dark"] .text-brand-blue-600,
[data-crm-theme="dark"] .text-brand-blue-700,
[data-crm-theme="dark"] .hover\\:text-brand-blue-600:hover { color: #60a5fa !important; }
[data-crm-theme="dark"] .hover\\:border-brand-blue-400:hover,
[data-crm-theme="dark"] .border-brand-blue-400 { border-color: #60a5fa !important; }

/* اینپوت و سلکت */
[data-crm-theme="dark"] input,
[data-crm-theme="dark"] select,
[data-crm-theme="dark"] textarea,
[data-crm-theme="dark"] .float-field > input,
[data-crm-theme="dark"] .float-field > textarea,
[data-crm-theme="dark"] .float-field > select {
  background-color: #1a2332 !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] input::placeholder,
[data-crm-theme="dark"] textarea::placeholder {
  color: #64748b !important;
}
[data-crm-theme="dark"] .float-field > .float-label {
  background-color: #1a2332 !important;
  color: #94a3b8 !important;
}

/* ساب‌نوی CRM */
[data-crm-theme="dark"] nav a {
  color: #cbd5e1;
}
[data-crm-theme="dark"] nav a:hover {
  background-color: #243044 !important;
}

/* بج‌ها و اسپن‌های رنگی خوانا بمانند */
[data-crm-theme="dark"] .bg-red-100 { background-color: #7f1d1d !important; color: #fecaca !important; }
[data-crm-theme="dark"] .text-red-600, [data-crm-theme="dark"] .text-red-700 { color: #fca5a5 !important; }
[data-crm-theme="dark"] .bg-orange-100 { background-color: #7c2d12 !important; color: #fed7aa !important; }
[data-crm-theme="dark"] .text-orange-500, [data-crm-theme="dark"] .text-orange-700 { color: #fdba74 !important; }
[data-crm-theme="dark"] .bg-sky-100 { background-color: #0c4a6e !important; color: #bae6fd !important; }
[data-crm-theme="dark"] .text-sky-600, [data-crm-theme="dark"] .text-sky-700 { color: #7dd3fc !important; }
[data-crm-theme="dark"] .bg-emerald-100 { background-color: #064e3b !important; color: #a7f3d0 !important; }
[data-crm-theme="dark"] .text-emerald-600, [data-crm-theme="dark"] .text-emerald-700 { color: #6ee7b7 !important; }
[data-crm-theme="dark"] .bg-amber-100 { background-color: #78350f !important; color: #fde68a !important; }
[data-crm-theme="dark"] .bg-violet-100 { background-color: #4c1d95 !important; color: #ddd6fe !important; }
[data-crm-theme="dark"] .bg-slate-100.text-slate-600 { background-color: #334155 !important; color: #e2e8f0 !important; }

/* سایه و اسکرول */
[data-crm-theme="dark"] ::-webkit-scrollbar-track { background: #0b1220 !important; }
[data-crm-theme="dark"] ::-webkit-scrollbar-thumb { background: #475569 !important; }
[data-crm-theme="dark"] .shadow-sm,
[data-crm-theme="dark"] .shadow-md,
[data-crm-theme="dark"] .shadow-lg {
  --tw-shadow-color: rgb(0 0 0 / 0.4);
  box-shadow: 0 4px 16px rgb(0 0 0 / 0.35) !important;
}

/* جزئیات و دراپ‌داون */
[data-crm-theme="dark"] details > div,
[data-crm-theme="dark"] .absolute.bg-white {
  background-color: #1a2332 !important;
  border-color: #334155 !important;
}

/* ── ساعت ── */
[data-crm-theme="dark"] .crm-clock {
  background: linear-gradient(to bottom, #1a2332, #1e293b) !important;
  border-color: #334155 !important;
  box-shadow: 0 4px 16px rgb(0 0 0 / 0.35) !important;
}
[data-crm-theme="dark"] .crm-clock-time,
[data-crm-theme="dark"] .crm-clock-date,
[data-crm-theme="dark"] .crm-clock .text-stone-800 {
  color: #f1f5f9 !important;
}
[data-crm-theme="dark"] .crm-clock-meta,
[data-crm-theme="dark"] .crm-clock .text-stone-500 {
  color: #94a3b8 !important;
}
[data-crm-theme="dark"] .crm-clock-msg,
[data-crm-theme="dark"] .crm-clock .text-stone-400 {
  color: #64748b !important;
}

/* ── پیام‌رسان ── */
[data-crm-theme="dark"] .crm-chat-panel,
[data-crm-theme="dark"] .crm-chat-panel .bg-stone-50\\/50,
[data-crm-theme="dark"] .bg-stone-50\\/50 {
  background-color: #151c2a !important;
}
[data-crm-theme="dark"] .crm-chat-panel .border-stone-200,
[data-crm-theme="dark"] .crm-chat-panel .border-stone-100,
[data-crm-theme="dark"] .border-stone-200,
[data-crm-theme="dark"] .border-stone-100 {
  border-color: #334155 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .text-stone-700,
[data-crm-theme="dark"] .text-stone-700 {
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .text-stone-600,
[data-crm-theme="dark"] .text-stone-600 {
  color: #cbd5e1 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .text-stone-400,
[data-crm-theme="dark"] .text-stone-400 {
  color: #94a3b8 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .hover\\:bg-stone-100:hover,
[data-crm-theme="dark"] .hover\\:bg-stone-100:hover {
  background-color: #243044 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .bg-white {
  background-color: #1a2332 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .crm-chat-panel .bg-stone-800,
[data-crm-theme="dark"] .bg-stone-800 {
  background-color: #3b82f6 !important;
  border-color: #3b82f6 !important;
  color: #fff !important;
}
[data-crm-theme="dark"] .crm-chat-panel input,
[data-crm-theme="dark"] .crm-chat-panel textarea {
  background-color: #0f172a !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .crm-chat-panel #chat-box {
  background-color: #0f172a !important;
  border-color: #334155 !important;
}
/* حباب پیام‌ها */
[data-crm-theme="dark"] .bg-stone-100 {
  background-color: #243044 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .text-stone-800 {
  color: #f1f5f9 !important;
}
[data-crm-theme="dark"] .from-stone-50 {
  --tw-gradient-from: #1a2332 !important;
}
[data-crm-theme="dark"] .to-amber-50\\/40 {
  --tw-gradient-to: #1e293b !important;
}

/* ── پنل کناری (یادداشت / todo) ── */
[data-crm-theme="dark"] .crm-side-panel,
[data-crm-theme="dark"] aside.crm-side-panel {
  background-color: #1a2332 !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .crm-side-panel textarea,
[data-crm-theme="dark"] .crm-side-panel input {
  background-color: #0f172a !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}
[data-crm-theme="dark"] .crm-side-panel .bg-slate-800 {
  background-color: #3b82f6 !important;
}
[data-crm-theme="dark"] .bg-stone-50 {
  background-color: #1a2332 !important;
}
[data-crm-theme="dark"] .bg-gradient-to-b.from-stone-50 {
  background-image: linear-gradient(to bottom, #1a2332, #1e293b) !important;
}

""",
}



def crm_user_theme(request):
    """تم و تنظیمات شخصی کاربر برای قالب‌های CRM."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"crm_theme": "default", "crm_theme_css": ""}
    try:
        from .models import UserCRMSettings
        s = UserCRMSettings.objects.filter(user=request.user).first()
        if not s:
            return {"crm_theme": "default", "crm_theme_css": ""}
        theme = s.theme or "default"
        return {
            "crm_theme": theme,
            "crm_theme_css": THEME_CSS.get(theme, ""),
            "crm_user_settings": s,
        }
    except Exception:
        return {"crm_theme": "default", "crm_theme_css": ""}
