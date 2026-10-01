from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (ContactForm, CustomerForm, CustomerSoftwareForm, PaymentForm,
                    RequestForm, TaskForm, TaskResultForm)
from .models import (Customer, CustomerStatus, Request, Software, Task, TaskStatus,
                     can_see_finance, is_manager)


def _visible_tasks(user):
    qs = Task.objects.open().select_related("customer", "assignee")
    return qs if is_manager(user) else qs.filter(assignee=user)


@login_required
def dashboard(request):
    today = timezone.localdate()
    mine = _visible_tasks(request.user)
    overdue = mine.filter(due_date__lt=today)
    due_today = mine.filter(due_date=today)
    tomorrow = mine.filter(due_date=today + timedelta(days=1))
    waiting = mine.filter(status=TaskStatus.WAITING_CUSTOMER)
    needs = mine.filter(status=TaskStatus.NEEDS_FOLLOWUP)
    ctx = {
        "customers_count": Customer.objects.count(),
        "total_open": mine.count(),
        "overdue": overdue, "due_today": due_today, "tomorrow": tomorrow,
        "waiting": waiting, "needs": needs,
        "manager": is_manager(request.user),
    }
    return render(request, "crm/dashboard.html", ctx)


@login_required
def task_list(request):
    qs = _visible_tasks(request.user)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    return render(request, "crm/task_list.html",
                  {"tasks": qs, "statuses": TaskStatus.choices, "current": status})


@login_required
def customer_list(request):
    qs = Customer.objects.all().annotate(
        open_tasks_count=Count("tasks", filter=~Q(tasks__status__in=Task.CLOSED), distinct=True),
        open_requests=Count("requests", distinct=True),
    )
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(company_name__icontains=q) |
                       Q(mobile__icontains=q) | Q(national_id__icontains=q) |
                       Q(landline__icontains=q) | Q(softwares__software__name__icontains=q)
                       ).distinct()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    software = request.GET.get("software")
    if software:
        qs = qs.filter(softwares__software_id=software).distinct()

    flt = request.GET.get("filter")
    if flt == "new":
        qs = qs.filter(status=CustomerStatus.NEW)
    elif flt == "no_followup":
        qs = qs.exclude(tasks__in=Task.objects.open())
    elif flt == "open_requests":
        qs = qs.filter(tasks__in=Task.objects.open()).distinct()
    elif flt == "waiting":
        qs = qs.filter(tasks__status=TaskStatus.WAITING_CUSTOMER).distinct()
    elif flt == "debtor" and can_see_finance(request.user):
        ids = [c.pk for c in Customer.objects.filter(total_amount__gt=0) if c.remaining > 0]
        qs = qs.filter(pk__in=ids)
    ctx = {"customers": qs, "q": q, "statuses": CustomerStatus.choices,
           "softwares": Software.objects.all(), "flt": flt, "status": status,
           "software": software, "finance": can_see_finance(request.user)}
    return render(request, "crm/customer_list.html", ctx)


@login_required
def customer_form(request, pk=None):
    customer = get_object_or_404(Customer, pk=pk) if pk else None
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.owner:
            obj.owner = request.user
        obj.save()
        messages.success(request, "اطلاعات مشتری ذخیره شد.")
        return redirect("crm:customer_detail", pk=obj.pk)
    return render(request, "crm/form.html", {"form": form,
                  "title": "ویرایش مشتری" if customer else "مشتری جدید"})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    finance = can_see_finance(request.user)
    ctx = {
        "c": customer, "finance": finance,
        "contacts": customer.contacts.all(),
        "softwares": customer.softwares.select_related("software"),
        "requests": customer.requests.prefetch_related("tasks__assignee"),
        "tasks": customer.tasks.select_related("assignee"),
        "activities": customer.activities.select_related("user"),
        "payments": customer.payments.all() if finance else [],
    }
    return render(request, "crm/customer_detail.html", ctx)


def _child_form(request, pk, form_class, title, finance_only=False):
    customer = get_object_or_404(Customer, pk=pk)
    if finance_only and not can_see_finance(request.user):
        raise PermissionDenied
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.customer = customer
        if hasattr(obj, "created_by"):
            obj.created_by = request.user
        obj.save()
        messages.success(request, "ثبت شد.")
        return redirect("crm:customer_detail", pk=customer.pk)
    return render(request, "crm/form.html", {"form": form, "title": f"{title} — {customer}"})


@login_required
def contact_add(request, pk):
    return _child_form(request, pk, ContactForm, "افزودن فرد تماس")


@login_required
def software_add(request, pk):
    return _child_form(request, pk, CustomerSoftwareForm, "افزودن نرم‌افزار")


@login_required
def payment_add(request, pk):
    return _child_form(request, pk, PaymentForm, "ثبت پرداخت", finance_only=True)


@login_required
def request_add(request, pk):
    return _child_form(request, pk, RequestForm, "ثبت درخواست / مشکل")


@login_required
def task_add(request, pk, request_pk=None):
    """ایجاد Task برای مشتری (و در صورت وجود، برای یک درخواست مشخص)."""
    customer = get_object_or_404(Customer, pk=pk)
    req = get_object_or_404(Request, pk=request_pk, customer=customer) if request_pk else None
    initial = {"title": req.subject, "assignee": request.user} if req else {"assignee": request.user}
    form = TaskForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.customer, task.request, task.created_by = customer, req, request.user
        task.save()
        messages.success(request, "کار ایجاد شد.")
        return redirect("crm:customer_detail", pk=customer.pk)
    return render(request, "crm/form.html", {"form": form, "title": f"کار جدید — {customer}"})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not is_manager(request.user) and task.assignee_id != request.user.id:
        raise PermissionDenied
    form = TaskResultForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نتیجه ثبت شد.")
        return redirect(request.GET.get("next") or "crm:dashboard")
    return render(request, "crm/form.html", {"form": form, "title": f"ثبت نتیجه — {task.title}"})
