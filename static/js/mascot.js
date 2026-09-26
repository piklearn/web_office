// ادمک همراه - چشم‌ها به سمت موس حرکت می‌کنند
document.addEventListener('DOMContentLoaded', () => {
  const pupils = document.querySelectorAll('.mascot-pupil');
  const head = document.querySelector('.mascot-head');
  if (!pupils.length) return;

  const maxOffset = 4.5; // حداکثر جابجایی مردمک داخل چشم (بر حسب واحد viewBox)

  function movePupils(clientX, clientY) {
    pupils.forEach((pupil) => {
      const eye = pupil.closest('.mascot-eye');
      const rect = eye.getBoundingClientRect();
      const eyeCenterX = rect.left + rect.width / 2;
      const eyeCenterY = rect.top + rect.height / 2;

      const dx = clientX - eyeCenterX;
      const dy = clientY - eyeCenterY;
      const angle = Math.atan2(dy, dx);
      const distance = Math.min(maxOffset, Math.hypot(dx, dy) / 18);

      const offsetX = Math.cos(angle) * distance;
      const offsetY = Math.sin(angle) * distance;

      pupil.setAttribute('transform', `translate(${offsetX.toFixed(2)}, ${offsetY.toFixed(2)})`);
    });

    // چرخش خیلی ملایم سر به سمت موس برای حس زنده‌بودن بیشتر
    if (head) {
      const headRect = head.getBoundingClientRect();
      const headCenterX = headRect.left + headRect.width / 2;
      const tilt = Math.max(-6, Math.min(6, (clientX - headCenterX) / 60));
      head.style.transform = `rotate(${tilt}deg)`;
    }
  }

  window.addEventListener('mousemove', (e) => {
    movePupils(e.clientX, e.clientY);
  });

  // برای دستگاه‌های لمسی: چشم‌ها به لمس واکنش نشان دهند
  window.addEventListener('touchmove', (e) => {
    if (e.touches && e.touches[0]) {
      movePupils(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: true });
});
