from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_GET

from support.forms import TrackingForm
from . import avatars
from .models import UserAvatar, LiveChatConversation, LiveChatMessage


SESSION_CONV_KEY = "livechat_conversation_id"


def home(request):
    """صفحه اصلی سایت شامل معرفی، پشتیبانی فوری و فرم پیگیری سریع."""
    context = {
        "tracking_form": TrackingForm(),
    }
    return render(request, "main/home.html", context)


@login_required
@require_POST
def set_avatar(request):
    """تغییر تصویر پروفایل از بین پروفایل‌های پیش‌فرض."""
    key = request.POST.get("avatar")
    if key in avatars.AVATAR_KEYS:
        UserAvatar.objects.update_or_create(user=request.user, defaults={"avatar": key})
    nxt = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        nxt = "/"
    return redirect(nxt)


# ───────────── چت آنلاین عمومی ─────────────
def _get_or_create_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _active_conversation(request):
    cid = request.session.get(SESSION_CONV_KEY)
    if not cid:
        return None
    try:
        conv = LiveChatConversation.objects.get(
            pk=cid, session_key=request.session.session_key,
            status=LiveChatConversation.Status.OPEN,
        )
        return conv
    except LiveChatConversation.DoesNotExist:
        request.session.pop(SESSION_CONV_KEY, None)
        return None


@require_GET
def livechat_widget(request):
    """ویجت شناور چت — حالت بسته یا باز با فرم/گفتگو."""
    conv = _active_conversation(request)
    open_panel = request.GET.get("open") == "1"
    context = {
        "conversation": conv,
        "open_panel": open_panel,
        "messages": list(conv.messages.all()) if conv else [],
    }
    return render(request, "main/livechat_widget.html", context)


@require_POST
def livechat_start(request):
    """شروع گفتگو با نام (و شماره اختیاری)."""
    name = (request.POST.get("visitor_name") or "").strip()
    phone = (request.POST.get("visitor_phone") or "").strip()
    if not name or len(name) < 2:
        return HttpResponseBadRequest("نام الزامی است")
    session_key = _get_or_create_session(request)

    # اگر گفتگوی باز قبلی هست همان را برگردان
    conv = _active_conversation(request)
    if not conv:
        conv = LiveChatConversation.objects.create(
            session_key=session_key,
            visitor_name=name[:100],
            visitor_phone=phone[:30],
        )
        # پیام خوش‌آمد خودکار
        LiveChatMessage.objects.create(
            conversation=conv,
            is_from_visitor=False,
            text="سلام! 👋 یکی از همکاران به‌زودی پاسخ می‌دهد. لطفاً سوال‌تون رو بنویسید.",
            read_by_visitor=True,
        )
        conv.last_message_at = timezone.now()
        conv.save(update_fields=["last_message_at"])
        request.session[SESSION_CONV_KEY] = conv.pk

    messages = list(conv.messages.all())
    return render(request, "main/livechat_panel.html", {
        "conversation": conv,
        "messages": messages,
    })


@require_POST
def livechat_send(request):
    """ارسال پیام از طرف بازدیدکننده."""
    conv = _active_conversation(request)
    if not conv:
        return HttpResponseBadRequest("گفتگویی فعال نیست")
    text = (request.POST.get("text") or "").strip()
    if not text:
        return HttpResponseBadRequest("پیام خالی است")
    msg = LiveChatMessage.objects.create(
        conversation=conv,
        is_from_visitor=True,
        text=text[:2000],
        read_by_visitor=True,
    )
    conv.last_message_at = timezone.now()
    conv.save(update_fields=["last_message_at", "updated_at"])
    messages = list(conv.messages.all())
    return render(request, "main/_livechat_messages.html", {
        "conversation": conv,
        "messages": messages,
    })


@require_GET
def livechat_poll(request):
    """پولینگ پیام‌های جدید برای بازدیدکننده."""
    conv = _active_conversation(request)
    if not conv:
        return HttpResponse("")
    # علامت خوانده‌شدن پیام‌های کارمند
    conv.messages.filter(is_from_visitor=False, read_by_visitor=False).update(read_by_visitor=True)
    messages = list(conv.messages.all())
    return render(request, "main/_livechat_messages.html", {
        "conversation": conv,
        "messages": messages,
    })


@require_POST
def livechat_close_visitor(request):
    """بستن گفتگو از سمت بازدیدکننده (اختیاری)."""
    conv = _active_conversation(request)
    if conv:
        conv.status = LiveChatConversation.Status.CLOSED
        conv.save(update_fields=["status", "updated_at"])
        request.session.pop(SESSION_CONV_KEY, None)
    return render(request, "main/livechat_widget.html", {
        "conversation": None,
        "open_panel": False,
        "messages": [],
    })
