/**
 * لیبل شناور — اطمینان از حالت پر/فوکوس حتی وقتی :placeholder-shown کار نکند
 */
(function () {
  function mark(el) {
    if (!el) return;
    var filled = (el.value || "").toString().trim().length > 0;
    el.classList.toggle("is-filled", filled);
    var wrap = el.closest(".float-field");
    if (wrap) wrap.classList.toggle("is-active", filled || document.activeElement === el);
  }

  function bind(el) {
    if (!el || el.dataset.floatBound) return;
    el.dataset.floatBound = "1";
    // اگر placeholder خالی است، یک فاصله بگذار تا :placeholder-shown کار کند
    if (!el.getAttribute("placeholder") && el.tagName !== "SELECT") {
      el.setAttribute("placeholder", " ");
    }
    mark(el);
    el.addEventListener("focus", function () {
      var w = el.closest(".float-field");
      if (w) w.classList.add("is-active");
    });
    el.addEventListener("blur", function () { mark(el); });
    el.addEventListener("input", function () { mark(el); });
    el.addEventListener("change", function () { mark(el); });
  }

  function init(root) {
    root = root || document;
    root.querySelectorAll(".float-field input, .float-field textarea, .float-field select").forEach(bind);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { init(); });
  } else {
    init();
  }

  // بعد از HTMX
  document.body.addEventListener("htmx:afterSwap", function (e) {
    init(e.target);
  });
  document.body.addEventListener("htmx:afterSettle", function (e) {
    init(e.target);
  });

  window.initFloatLabels = init;
})();
