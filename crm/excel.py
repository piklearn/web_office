"""
ورود/خروج داده‌ی مشتریان با اکسل.

سه قابلیت:
- خروجی «خام»: فقط ستون‌های قابل ورود دوباره (همان ساختار قالب ورودی)
- خروجی «کامل»: برای بایگانی/مدیر، شامل نرم‌افزارها، جمع پرداخت، مانده و ...
- ورود از اکسل: آپلود، پیش‌نمایش (جدید/تکراری/خطا)، سپس تأیید نهایی و ذخیره
"""
from decimal import Decimal, InvalidOperation

import jdatetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .models import Customer, CustomerStatus, PaymentStatus

# ---------------------------------------------------------------------------
# ستون‌های «خام» - همان ساختار برای خروجی خام و قالب ورودی استفاده می‌شود
# ---------------------------------------------------------------------------
RAW_COLUMNS = [
    "نام و نام خانوادگی", "نام شرکت", "کد ملی", "موبایل", "تلفن ثابت",
    "آدرس", "نوع فعالیت", "وضعیت", "توضیحات", "مبلغ کل", "وضعیت پرداخت",
]

SAMPLE_ROW = [
    "علی رضایی", "شرکت نمونه", "0012345678", "09120000000", "02112345678",
    "تهران، خیابان نمونه", "خدمات IT", "جدید", "یک مشتری نمونه برای راهنما",
    "12500000", "پرداخت نشده",
]

_STATUS_LABEL_TO_VALUE = {label: value for value, label in CustomerStatus.choices}
_PAYSTATUS_LABEL_TO_VALUE = {label: value for value, label in PaymentStatus.choices}


def _style_header(ws, n_cols):
    ws.sheet_view.rightToLeft = True
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        ws.column_dimensions[get_column_letter(col)].width = 20


def _to_excel_amount(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# خروجی خام
# ---------------------------------------------------------------------------
def build_raw_workbook(customers=None):
    """خروجی خام: فقط ستون‌های قابل ورود دوباره، بدون ID داخلی و بدون Timeline/پرداخت‌های جزئی."""
    wb = Workbook()
    ws = wb.active
    ws.title = "مشتریان (خام)"
    ws.append(RAW_COLUMNS)
    _style_header(ws, len(RAW_COLUMNS))

    qs = customers if customers is not None else Customer.objects.all().order_by("full_name")
    for c in qs:
        ws.append([
            c.full_name, c.company_name, c.national_id, c.mobile, c.landline,
            c.address, c.activity_type, c.get_status_display(), c.description,
            _to_excel_amount(c.total_amount), c.get_payment_status_display(),
        ])
    return wb


def build_template_workbook():
    """قالب ورودی: فقط هدر + یک ردیف نمونه (بدون داده واقعی)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "قالب ورود مشتریان"
    ws.append(RAW_COLUMNS)
    _style_header(ws, len(RAW_COLUMNS))
    ws.append(SAMPLE_ROW)
    return wb


# ---------------------------------------------------------------------------
# خروجی کامل
# ---------------------------------------------------------------------------
FULL_COLUMNS = RAW_COLUMNS + [
    "کارمند مسئول", "نرم‌افزارها", "تعداد کار باز", "تعداد درخواست",
    "جمع پرداخت", "مانده", "تاریخ ثبت",
]


def build_full_workbook():
    """خروجی کامل: همهٔ چیزهای مفید برای بایگانی/مدیر."""
    wb = Workbook()
    ws = wb.active
    ws.title = "مشتریان (کامل)"
    ws.append(FULL_COLUMNS)
    _style_header(ws, len(FULL_COLUMNS))

    qs = (Customer.objects.all().select_related("owner")
          .prefetch_related("softwares__software", "tasks", "requests", "payments")
          .order_by("full_name"))
    for c in qs:
        softwares = "|".join(cs.software.name for cs in c.softwares.all())
        open_tasks = sum(1 for t in c.tasks.all() if not t.is_closed)
        paid = sum(p.amount for p in c.payments.all())
        jalali_created = jdatetime.date.fromgregorian(date=c.created_at.date()).strftime("%Y/%m/%d")
        ws.append([
            c.full_name, c.company_name, c.national_id, c.mobile, c.landline,
            c.address, c.activity_type, c.get_status_display(), c.description,
            _to_excel_amount(c.total_amount), c.get_payment_status_display(),
            str(c.owner) if c.owner else "", softwares, open_tasks, c.requests.count(),
            _to_excel_amount(paid), _to_excel_amount(c.total_amount - paid), jalali_created,
        ])
    return wb


# ---------------------------------------------------------------------------
# ورود از اکسل
# ---------------------------------------------------------------------------
def _clean_amount(raw):
    if raw in (None, ""):
        return 0, None
    if isinstance(raw, (int, float)):
        return int(raw), None
    text = str(raw).replace(",", "").replace("،", "").strip()
    if not text:
        return 0, None
    try:
        return int(Decimal(text)), None
    except (InvalidOperation, ValueError):
        return None, f"مبلغ کل نامعتبر: «{raw}»"


def parse_import_file(uploaded_file):
    """
    فایل آپلودشده را می‌خواند و برای هر ردیف یکی از این برچسب‌ها را می‌زند:
    new / duplicate / error
    خروجی: (rows, error_count) — rows لیستی از دیکشنری‌های قابل سریالایز به JSON است.
    """
    try:
        wb = load_workbook(uploaded_file, data_only=True)
    except Exception:
        return [], "فایل اکسل خوانا نیست. لطفاً از فرمت .xlsx استفاده کنید."

    ws = wb.active
    rows_iter = ws.iter_rows(min_row=2, values_only=True)

    # برای جلوگیری از تکراری‌شدن داخل همان فایل
    seen_mobiles, seen_national_ids = {}, {}
    existing_by_mobile = {c.mobile: c.pk for c in Customer.objects.exclude(mobile="")}
    existing_by_national_id = {c.national_id: c.pk for c in Customer.objects.exclude(national_id="")}

    results = []
    for idx, row in enumerate(rows_iter, start=2):
        if row is None or all(cell in (None, "") for cell in row):
            continue  # ردیف کاملاً خالی را نادیده بگیر

        row = list(row) + [None] * (len(RAW_COLUMNS) - len(row))
        (full_name, company_name, national_id, mobile, landline, address,
         activity_type, status_label, description, total_amount, payment_status_label) = row[:11]

        full_name = (str(full_name).strip() if full_name else "")
        mobile = (str(mobile).strip() if mobile else "")
        national_id = (str(national_id).strip() if national_id else "")

        error = None
        if not full_name:
            error = "نام و نام خانوادگی الزامی است."

        status_value = CustomerStatus.NEW
        if status_label and not error:
            status_value = _STATUS_LABEL_TO_VALUE.get(str(status_label).strip())
            if status_value is None:
                error = f"وضعیت نامعتبر: «{status_label}»"

        payment_status_value = PaymentStatus.UNPAID
        if payment_status_label and not error:
            payment_status_value = _PAYSTATUS_LABEL_TO_VALUE.get(str(payment_status_label).strip())
            if payment_status_value is None:
                error = f"وضعیت پرداخت نامعتبر: «{payment_status_label}»"

        amount_value, amount_error = (0, None) if error else _clean_amount(total_amount)
        if amount_error:
            error = amount_error

        match_pk = None
        if not error:
            if mobile and mobile in existing_by_mobile:
                match_pk = existing_by_mobile[mobile]
            elif national_id and national_id in existing_by_national_id:
                match_pk = existing_by_national_id[national_id]
            elif mobile and mobile in seen_mobiles:
                match_pk = seen_mobiles[mobile]
            elif national_id and national_id in seen_national_ids:
                match_pk = seen_national_ids[national_id]

        status_kind = "error" if error else ("duplicate" if match_pk else "new")
        if status_kind == "new":
            if mobile:
                seen_mobiles[mobile] = "pending"
            if national_id:
                seen_national_ids[national_id] = "pending"

        results.append({
            "row": idx, "kind": status_kind, "error": error, "match_pk": match_pk,
            "full_name": full_name, "company_name": company_name or "",
            "national_id": national_id, "mobile": mobile, "landline": landline or "",
            "address": address or "", "activity_type": activity_type or "",
            "status": status_value, "description": description or "",
            "total_amount": amount_value, "payment_status": payment_status_value,
        })

    return results, None


def apply_import(rows, duplicate_action, owner):
    """پس از تأیید نهایی: ردیف‌های new را می‌سازد و duplicate را طبق انتخاب کاربر رد/به‌روزرسانی می‌کند."""
    created, updated, skipped = 0, 0, 0
    for r in rows:
        if r["kind"] == "error":
            continue
        fields = dict(
            full_name=r["full_name"], company_name=r["company_name"],
            national_id=r["national_id"], mobile=r["mobile"], landline=r["landline"],
            address=r["address"], activity_type=r["activity_type"], status=r["status"],
            description=r["description"], total_amount=r["total_amount"],
            payment_status=r["payment_status"],
        )
        if r["kind"] == "new":
            Customer.objects.create(owner=owner, **fields)
            created += 1
        elif r["kind"] == "duplicate":
            if duplicate_action == "update" and r["match_pk"]:
                Customer.objects.filter(pk=r["match_pk"]).update(**fields)
                updated += 1
            else:
                skipped += 1
    return created, updated, skipped
