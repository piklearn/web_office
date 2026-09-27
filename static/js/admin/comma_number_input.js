// فرمت‌دهی لحظه‌ای اعداد با کاما (جداکننده هزارگان) در ورودی‌های عددی پنل ادمین
(function () {
  function formatWithCommas(rawValue) {
    const digitsOnly = rawValue.replace(/[^\d]/g, "");
    if (!digitsOnly) return "";
    // حذف صفرهای اضافه در ابتدا (به‌جز وقتی کل عدد صفر باشد)
    const trimmed = digitsOnly.replace(/^0+(?=\d)/, "");
    return trimmed.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function attachFormatting(input) {
    if (input.dataset.commaFormatted) return; // جلوگیری از اتصال تکراری
    input.dataset.commaFormatted = "true";

    // فرمت‌دهی مقدار اولیه (هنگام باز کردن فرم ویرایش)
    input.value = formatWithCommas(input.value || "");

    input.addEventListener("input", function () {
      const cursorFromEnd = input.value.length - (input.selectionStart || 0);
      input.value = formatWithCommas(input.value);
      const newPosition = Math.max(0, input.value.length - cursorFromEnd);
      input.setSelectionRange(newPosition, newPosition);
    });
  }

  function initAll() {
    document.querySelectorAll(".comma-number-input").forEach(attachFormatting);
  }

  document.addEventListener("DOMContentLoaded", initAll);

  // پشتیبانی از فرم‌های Inline پنل ادمین جنگو که به‌صورت پویا اضافه می‌شوند
  document.addEventListener("formset:added", initAll);
})();
