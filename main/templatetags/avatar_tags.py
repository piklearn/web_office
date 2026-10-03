from django import template

from main import avatars
from main.models import UserAvatar

register = template.Library()


@register.simple_tag
def avatar_src(user, key=None):
    """آدرس (data URI) تصویر پروفایل کاربر؛ با key می‌توان یک پیش‌فرض مشخص را گرفت."""
    if key is None:
        key = (UserAvatar.objects.filter(user=user).values_list("avatar", flat=True).first()
               or avatars.default_key(user))
    return avatars.data_uri(key)


@register.simple_tag
def avatar_choices():
    return avatars.AVATARS
