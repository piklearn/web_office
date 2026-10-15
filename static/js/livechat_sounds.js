/**
 * صداهای چت آنلاین
 * - open: وقتی ویجت/پنل باز می‌شود
 * - send: ارسال پیام
 * - receive: دریافت پیام جدید
 */
(function (global) {
  var BASE = "/static/sounds/";
  var cache = {};
  var lastMsgCount = 0;
  var unlocked = false;

  function getAudio(name) {
    if (!cache[name]) {
      var a = new Audio(BASE + name + ".mp3");
      a.preload = "auto";
      a.volume = name === "send" ? 0.45 : 0.55;
      cache[name] = a;
    }
    return cache[name];
  }

  function play(name) {
    try {
      var a = getAudio(name);
      a.currentTime = 0;
      var p = a.play();
      if (p && p.catch) p.catch(function () {});
    } catch (e) {}
  }

  // مرورگرها تا قبل از تعامل کاربر صدا را بلاک می‌کنند
  function unlock() {
    if (unlocked) return;
    unlocked = true;
    ["ping", "send", "receive"].forEach(function (n) {
      try {
        var a = getAudio(n);
        a.muted = true;
        a.play().then(function () {
          a.pause();
          a.currentTime = 0;
          a.muted = false;
        }).catch(function () { a.muted = false; });
      } catch (e) {}
    });
  }

  document.addEventListener("click", unlock, { once: true, capture: true });
  document.addEventListener("touchstart", unlock, { once: true, capture: true });

  global.LiveChatSound = {
    open: function () { play("ping"); },
    send: function () { play("send"); },
    receive: function () { play("receive"); },
    /** بعد از رندر پیام‌ها — اگر تعداد بیشتر شد، receive پخش شود */
    checkNewMessages: function (container) {
      if (!container) return;
      var n = container.querySelectorAll(":scope > div").length;
      if (lastMsgCount > 0 && n > lastMsgCount) {
        play("receive");
      }
      lastMsgCount = n;
    },
    resetCount: function (container) {
      if (!container) { lastMsgCount = 0; return; }
      lastMsgCount = container.querySelectorAll(":scope > div").length;
    },
  };
})(window);
