from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from support.forms import TrackingForm
from . import avatars
from .models import UserAvatar


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
