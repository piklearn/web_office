import jdatetime

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def to_jalali(value):
    if not value:
        return "—"

    # برای DateTimeField
    if hasattr(value, "hour"):
        value = timezone.localtime(value)

        jalali_date = jdatetime.date.fromgregorian(
            date=value.date()
        )

        return (
            f"{jalali_date.strftime('%Y/%m/%d')} - "
            f"{value.strftime('%H:%M')}"
        )

    # برای DateField
    return jdatetime.date.fromgregorian(
        date=value
    ).strftime("%Y/%m/%d")
