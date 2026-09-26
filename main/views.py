from django.shortcuts import render
from support.forms import TrackingForm


def home(request):
    """صفحه اصلی سایت شامل معرفی، پشتیبانی فوری و فرم پیگیری سریع."""
    context = {
        "tracking_form": TrackingForm(),
    }
    return render(request, "main/home.html", context)
