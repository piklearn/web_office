from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import RepairCase
from .forms import TrackingForm, RepairCaseForm


def track_result(request):
    """نتیجه پیگیری سریع - بر اساس کد پیگیری یا شماره تماس جستجو می‌کند."""
    form = TrackingForm(request.GET or None)
    case = None
    searched = False

    if form.is_valid():
        searched = True
        query = form.cleaned_data["query"].strip()
        case = RepairCase.objects.filter(
            Q(tracking_code=query) | Q(phone=query)
        ).order_by("-received_at").first()

    return render(request, "support/track_result.html", {
        "form": form,
        "case": case,
        "searched": searched,
    })


@login_required
def register_case(request):
    """ثبت کیس جدید تعمیر توسط کارکنان دفتر."""
    if request.method == "POST":
        form = RepairCaseForm(request.POST)
        if form.is_valid():
            case = form.save()
            messages.success(request, f"کیس با موفقیت ثبت شد. کد پیگیری: {case.tracking_code}")
            return redirect("support:register")
    else:
        form = RepairCaseForm()

    return render(request, "support/register_case.html", {"form": form})
