import json
from collections import Counter
from datetime import timedelta

import jdatetime
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .excel import (apply_import, build_full_workbook, build_raw_workbook,
                    build_template_workbook, parse_import_file)
from .forms import (ContactForm, CustomerForm, CustomerSoftwareForm, PaymentForm,
                    RequestForm, TaskForm, TaskResultForm)
from .models import (
    Customer, CustomerStatus, Payment, Request, Software, Task, TaskStatus,
    WorkGroup, can_see_finance, is_manager,
    can_create_task, can_edit_task, can_delete_task, can_update_status,
)

JALALI_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


# ───────────── ابزارهای کمکی ─────────────
def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _render_form(request, form, title, **extra):
    """در درخواست HTMX فقط محتوای مودال، در غیر این صورت صفحهٔ کامل فرم برگردانده می‌شود."""
    tpl = "crm/_modal_form.html" if _is_htmx(request) else "crm/form.html"
    return render(request, tpl, {"form": form, "title": title,
                                 "action": request.get_full_path(), **extra})


def _done(request, fallback):
    """بعد از ذخیرهٔ موفق: در مودال، صفحه رفرش می‌شود (تب فعلی در hash حفظ می‌شود)."""
    if _is_htmx(request):
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return fallback


def _safe_next(request, default="crm:dashboard"):
    nxt = request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(default)


def _visible_tasks(user):
    qs = Task.objects.open().select_related("customer", "assignee", "group")
    if is_manager(user):
        return qs
    return qs.filter(
        Q(assignee=user)
        | Q(created_by=user)
        | Q(group__members=user)
    ).distinct()


def _all_visible_tasks(user):
    qs = Task.objects.all()
    return qs if is_manager(user) else qs.filter(assignee=user)


def _with_remaining(qs):
    """مانده‌حساب هر مشتری را بدون تکثیر ردیف (Subquery) به queryset اضافه می‌کند."""
    money = DecimalField(max_digits=14, decimal_places=0)
    paid = (Payment.objects.filter(customer=OuterRef("pk")).order_by()
            .values("customer").annotate(s=Sum("amount")).values("s"))
    return qs.annotate(
        paid_sum=Coalesce(Subquery(paid, output_field=money), Value(0), output_field=money),
    ).annotate(remaining_sum=F("total_amount") - F("paid_sum"))


# ───────────── داشبورد و کارها ─────────────
@login_required
def dashboard(request):
    today = timezone.localdate()
    mine = _visible_tasks(request.user)
    overdue = mine.filter(due_date__lt=today)
    due_today = mine.filter(due_date=today)
    tomorrow = mine.filter(due_date=today + timedelta(days=1))
    waiting = mine.filter(status=TaskStatus.WAITING_CUSTOMER)
    needs = mine.filter(status=TaskStatus.NEEDS_FOLLOWUP)

    # ویجت «کار بعدی من»
    next_task = mine.filter(due_date__isnull=False).first()

    # نمودار ۱: وضعیت مشتریان
    labels = dict(CustomerStatus.choices)
    status_rows = Customer.objects.values("status").annotate(n=Count("pk")).order_by("-n")
    status_chart = {"labels": [labels.get(r["status"], r["status"]) for r in status_rows],
                    "values": [r["n"] for r in status_rows]}

    # نمودار ۲: کارهای انجام‌شده در ۷ روز اخیر
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    since = timezone.now() - timedelta(days=7)
    done_by_day = Counter(
        timezone.localtime(dt).date()
        for dt in _all_visible_tasks(request.user)
        .filter(status=TaskStatus.DONE, completed_at__gte=since)
        .values_list("completed_at", flat=True))
    done_chart = {
        "labels": [jdatetime.date.fromgregorian(date=d).strftime("%m/%d") for d in days],
        "values": [done_by_day.get(d, 0) for d in days]}

    sections = [
        {"title": " عقب‌افتاده", "cls": "text-red-600", "tasks": overdue},
        {"title": "امروز", "cls": "text-orange-500", "tasks": due_today},
        {"title": " فردا", "cls": "text-yellow-600", "tasks": tomorrow},
        {"title": " منتظر مشتری", "cls": "text-sky-600", "tasks": waiting},
        {"title": "نیاز به پیگیری", "cls": "text-red-500", "tasks": needs},
    ]
    ctx = {
        "customers_count": Customer.objects.count(),
        "total_open": mine.count(),
        "overdue_count": overdue.count(), "today_count": due_today.count(),
        "waiting_count": waiting.count(),
        "sections": sections, "next_task": next_task,
        "charts": {"status": status_chart, "done": done_chart},
        "manager": is_manager(request.user), "finance": can_see_finance(request.user),
    }
    return render(request, "crm/dashboard.html", ctx)


@login_required
def task_list(request):
    today = timezone.localdate()
    qs = _visible_tasks(request.user)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    due = request.GET.get("due")
    if due == "overdue":
        qs = qs.filter(due_date__lt=today)
    elif due == "today":
        qs = qs.filter(due_date=today)
    elif due == "week":
        qs = qs.filter(due_date__gte=today, due_date__lte=today + timedelta(days=7))
    return render(request, "crm/task_list.html",
                  {"tasks": qs, "statuses": TaskStatus.choices, "current": status,
                   "due": due, "manager": is_manager(request.user),
                   "finance": can_see_finance(request.user)})


@login_required
@require_POST
def task_status(request, pk):
    task = get_object_or_404(Task.objects.select_related("customer", "assignee", "group"), pk=pk)
    if not can_update_status(request.user, task):
        raise PermissionDenied
    new_status = request.POST.get("status")
    if new_status not in TaskStatus.values:
        return HttpResponseBadRequest("invalid status")
    task.status = new_status
    task.save()
    toast = json.dumps({"toast": f"وضعیت کار به «{task.get_status_display()}» تغییر کرد."})

    if request.POST.get("mode") == "row":
        if task.is_closed:      # کار بسته شد: از لیست کارهای باز حذف می‌شود
            resp = HttpResponse("")
        else:
            resp = render(request, "crm/_task_row.html",
                          {"t": task, "manager": is_manager(request.user)})
    else:                        # mode=keep: فقط نمایش پیام، چیدمان صفحه ثابت می‌ماند
        resp = HttpResponse(status=204)
    resp["HX-Trigger"] = toast
    return resp


# ───────────── مشتریان ─────────────
CUSTOMER_FILTERS = {"new": "مشتریان جدید", "open_requests": "دارای درخواست باز",
                    "no_followup": "بدون پیگیری", "waiting": "منتظر پاسخ", "debtor": "بدهکار"}
CUSTOMER_SORTS = {"newest": ("-created_at", "جدیدترین"), "name": ("full_name", "نام (الف تا ی)"),
                  "tasks": ("-open_tasks_count", "بیشترین کار باز"),
                  "debt": ("-remaining_sum", "بیشترین بدهی")}


@login_required
def customer_list(request):
    finance = can_see_finance(request.user)
    qs = Customer.objects.all().annotate(
        open_tasks_count=Count("tasks", filter=~Q(tasks__status__in=Task.CLOSED), distinct=True),
        open_requests=Count("requests", distinct=True),
    )
    if finance:
        qs = _with_remaining(qs)

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
    if flt == "debtor" and not finance:
        flt = None
    if flt == "new":
        qs = qs.filter(status=CustomerStatus.NEW)
    elif flt == "no_followup":
        qs = qs.exclude(tasks__in=Task.objects.open())
    elif flt == "open_requests":
        qs = qs.filter(tasks__in=Task.objects.open()).distinct()
    elif flt == "waiting":
        qs = qs.filter(tasks__status=TaskStatus.WAITING_CUSTOMER).distinct()
    elif flt == "debtor":
        qs = qs.filter(total_amount__gt=0, remaining_sum__gt=0)

    sort = request.GET.get("sort") if request.GET.get("sort") in CUSTOMER_SORTS else "newest"
    if sort == "debt" and not finance:
        sort = "newest"
    qs = qs.order_by(CUSTOMER_SORTS[sort][0], "-pk")

    # چیپ‌های فیلترهای فعال (هرکدام با لینک حذف)
    def without(*keys):
        params = request.GET.copy()
        for k in (*keys, "page"):
            params.pop(k, None)
        return "?" + params.urlencode()

    chips = []
    if q:
        chips.append({"label": f"جستجو: {q}", "url": without("q")})
    if status:
        chips.append({"label": dict(CustomerStatus.choices).get(status, status),
                      "url": without("status")})
    if software:
        name = Software.objects.filter(pk=software).values_list("name", flat=True).first() \
            if software.isdigit() else None
        if name:
            chips.append({"label": f"نرم‌افزار: {name}", "url": without("software")})
    if flt in CUSTOMER_FILTERS:
        chips.append({"label": CUSTOMER_FILTERS[flt], "url": without("filter")})

    params = request.GET.copy()
    params.pop("page", None)
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    sorts = [(k, v[1]) for k, v in CUSTOMER_SORTS.items() if k != "debt" or finance]
    ctx = {"page_obj": page_obj, "customers": page_obj.object_list, "q": q,
           "statuses": CustomerStatus.choices, "softwares": Software.objects.all(),
           "flt": flt, "status": status, "software": software, "finance": finance,
           "sorts": sorts, "sort": sort, "chips": chips, "base_qs": params.urlencode(),
           "filters": [(k, v) for k, v in CUSTOMER_FILTERS.items() if k != "debtor" or finance]}
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
        if "save_add_task" in request.POST:
            return redirect("crm:task_add", pk=obj.pk)
        return redirect("crm:customer_detail", pk=obj.pk)
    return render(request, "crm/form.html", {
        "form": form, "title": "ویرایش مشتری" if customer else "مشتری جدید",
        "extra_button": None if customer else "ذخیره و ثبت کار جدید"})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    finance = can_see_finance(request.user)
    payments = list(customer.payments.all()) if finance else []
    total = int(customer.total_amount)
    paid = int(sum(p.amount for p in payments))
    requests_ = list(customer.requests.prefetch_related("tasks__assignee"))
    standalone = list(customer.tasks.filter(request__isnull=True).select_related("assignee"))
    contacts = list(customer.contacts.all())
    softwares = list(customer.softwares.select_related("software"))
    ctx = {
        "c": customer, "finance": finance,
        "contacts": contacts, "softwares": softwares,
        "requests": requests_, "standalone_tasks": standalone,
        "open_tasks_count": sum(1 for r in requests_ for t in r.tasks.all() if not t.is_closed)
                            + sum(1 for t in standalone if not t.is_closed),
        "activities": list(customer.activities.select_related("user")),
        "payments": payments,
        "total": total, "paid": paid, "remaining": total - paid,
        "paid_pct": min(100, round(paid * 100 / total)) if total > 0 else 0,
    }
    return render(request, "crm/customer_detail.html", ctx)


# ───────────── فرم‌های فرزند (مودال یا صفحهٔ کامل) ─────────────
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
        return _done(request, redirect("crm:customer_detail", pk=customer.pk))
    return _render_form(request, form, f"{title} — {customer}")


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
    if not can_create_task(request.user):
        raise PermissionDenied
    customer = get_object_or_404(Customer, pk=pk)
    req = get_object_or_404(Request, pk=request_pk, customer=customer) if request_pk else None
    initial = {"title": req.subject, "assignee": request.user} if req else {"assignee": request.user}
    form = TaskForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.customer, task.request, task.created_by = customer, req, request.user
        task.save()
        form.save_m2m()  # لازم نیست مگر M2M روی فرم باشد
        messages.success(request, "کار ایجاد شد.")
        return _done(request, redirect("crm:customer_detail", pk=customer.pk))
    return _render_form(request, form, f"کار جدید — {customer}")

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_update_status(request.user, task):
        raise PermissionDenied
    form = TaskResultForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نتیجه ثبت شد.")
        return _done(request, _safe_next(request))
    return _render_form(request, form, f"ثبت نتیجه — {task.title}")

@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_delete_task(request.user, task):
        raise PermissionDenied
    customer_pk = task.customer_id
    task.delete()
    messages.success(request, "کار حذف شد.")
    if _is_htmx(request):
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return redirect("crm:customer_detail", pk=customer_pk)

@login_required
@require_POST
def task_claim(request, pk):
    task = get_object_or_404(Task, pk=pk, assignee__isnull=True)
    if not is_manager(request.user):
        if not task.group_id or not task.group.members.filter(pk=request.user.pk).exists():
            raise PermissionDenied
    task.assignee = request.user
    task.save(update_fields=["assignee"])
    messages.success(request, "کار به شما سپرده شد.")
    if _is_htmx(request):
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return redirect(request.GET.get("next") or "crm:dashboard")
# ───────────── گزارش‌ها ─────────────
@login_required
def reports(request):
    """گزارش ساده فروش، بدهکاران، تبدیل نرم‌افزارها و عملکرد کارکنان."""
    if not can_see_finance(request.user):
        raise PermissionDenied
    today = timezone.localdate()
    jt = jdatetime.date.fromgregorian(date=today)

    # ۱۲ ماه شمسی اخیر
    months, (y, m) = [], (jt.year, jt.month)
    for _ in range(12):
        months.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    months.reverse()
    start = jdatetime.date(months[0][0], months[0][1], 1).togregorian()
    sums = Counter()
    for d, amount in Payment.objects.filter(date__gte=start).values_list("date", "amount"):
        j = jdatetime.date.fromgregorian(date=d)
        sums[(j.year, j.month)] += int(amount)
    top = max(sums.values(), default=0)
    monthly = [{"label": f"{JALALI_MONTHS[m - 1]} {y}", "sum": sums.get((y, m), 0),
                "pct": round(sums.get((y, m), 0) * 100 / top) if top else 0}
               for y, m in months]

    debtors = list(_with_remaining(Customer.objects.filter(total_amount__gt=0))
                   .filter(remaining_sum__gt=0).order_by("-remaining_sum")[:50])
    debt_total = sum(int(c.remaining_sum) for c in debtors)

    conversion = []
    for s in Software.objects.annotate(
            total=Count("customersoftware"),
            bought=Count("customersoftware", filter=Q(customersoftware__is_purchased=True))):
        conversion.append({"name": s.name, "total": s.total, "bought": s.bought,
                           "rate": round(s.bought * 100 / s.total) if s.total else 0})
    conversion.sort(key=lambda r: -r["total"])

    staff = []
    if is_manager(request.user):
        since = timezone.now() - timedelta(days=30)
        open_q = ~Q(crm_tasks__status__in=Task.CLOSED)
        staff = (get_user_model().objects.filter(crm_tasks__isnull=False).annotate(
            done=Count("crm_tasks", filter=Q(crm_tasks__status=TaskStatus.DONE,
                                             crm_tasks__completed_at__gte=since)),
            open=Count("crm_tasks", filter=open_q),
            overdue=Count("crm_tasks", filter=open_q & Q(crm_tasks__due_date__lt=today)),
        ).order_by("-done"))

    return render(request, "crm/reports.html", {
        "monthly": monthly, "year_total": sum(r["sum"] for r in monthly),
        "debtors": debtors, "debt_total": debt_total,
        "conversion": conversion, "staff": staff, "manager": is_manager(request.user)})

@login_required
def software_edit(request, pk, spk):
    customer = get_object_or_404(Customer, pk=pk)
    obj = get_object_or_404(CustomerSoftware, pk=spk, customer=customer)
    form = CustomerSoftwareForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نرم‌افزار به‌روز شد.")
        return _done(request, redirect("crm:customer_detail", pk=customer.pk))
    return _render_form(request, form, f"ویرایش نرم‌افزار — {customer}")


@login_required
@require_POST
def software_delete(request, pk, spk):
    customer = get_object_or_404(Customer, pk=pk)
    obj = get_object_or_404(CustomerSoftware, pk=spk, customer=customer)
    name = str(obj.software)
    obj.delete()
    messages.success(request, f"نرم‌افزار «{name}» حذف شد.")
    if _is_htmx(request):
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return redirect("crm:customer_detail", pk=customer.pk)


# ───────────── ورود / خروج داده (اکسل) ─────────────
def _xlsx_response(workbook, filename):
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(resp)
    return resp


@login_required
def customer_export(request):
    """خروجی اکسل: kind=raw (برای هرکسی که حق ایجاد مشتری دارد) یا kind=full (فقط مالی/مدیر)."""
    kind = request.GET.get("kind", "raw")
    today = timezone.localdate()
    if kind == "full":
        if not can_see_finance(request.user):
            raise PermissionDenied
        wb = build_full_workbook()
        filename = f"مشتریان-کامل-{today}.xlsx"
    else:
        wb = build_raw_workbook()
        filename = f"مشتریان-خام-{today}.xlsx"
    return _xlsx_response(wb, filename)


@login_required
def customer_import_template(request):
    """دانلود قالب خام برای ورود اطلاعات (هدر + یک ردیف نمونه، بدون داده واقعی)."""
    wb = build_template_workbook()
    return _xlsx_response(wb, "قالب-ورود-مشتریان.xlsx")


@login_required
def customer_import(request):
    """ورود مشتریان از اکسل: آپلود → پیش‌نمایش (جدید/تکراری/خطا) → تأیید نهایی و ذخیره."""
    if not can_see_finance(request.user):
        raise PermissionDenied

    preview_rows, parse_error, result = None, None, None
    duplicate_action = request.POST.get("duplicate_action", "skip")

    if request.method == "POST":
        if "confirm" in request.POST:
            try:
                rows = json.loads(request.POST.get("rows_json", "[]"))
            except json.JSONDecodeError:
                rows = []
            created, updated, skipped = apply_import(rows, duplicate_action, request.user)
            result = {"created": created, "updated": updated, "skipped": skipped}
            messages.success(
                request,
                f"ورود اطلاعات انجام شد: {created} مشتری جدید، {updated} به‌روزرسانی، {skipped} رد شد.",
            )
        elif request.FILES.get("file"):
            preview_rows, parse_error = parse_import_file(request.FILES["file"])

    counts = None
    if preview_rows is not None:
        counts = {
            "new": sum(1 for r in preview_rows if r["kind"] == "new"),
            "duplicate": sum(1 for r in preview_rows if r["kind"] == "duplicate"),
            "error": sum(1 for r in preview_rows if r["kind"] == "error"),
        }

    return render(request, "crm/customer_import.html", {
        "preview_rows": preview_rows, "parse_error": parse_error, "counts": counts,
        "rows_json": json.dumps(preview_rows) if preview_rows is not None else "",
        "duplicate_action": duplicate_action, "result": result,
        "finance": can_see_finance(request.user), "manager": is_manager(request.user),
    })