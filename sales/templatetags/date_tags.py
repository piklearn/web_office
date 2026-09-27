from django import template
import jdatetime

register = template.Library()


@register.filter
def to_jalali(value):
    if not value:
        return ""

    if hasattr(value, "date"):
        value = value.date()

    return jdatetime.date.fromgregorian(
        date=value
    ).strftime("%Y/%m/%d")
