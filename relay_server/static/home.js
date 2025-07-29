document.addEventListener('DOMContentLoaded', function () {
  const buttons = document.querySelectorAll('.big_btn');

  document.querySelectorAll('.ping_time').forEach(span => {
    const iso = span.dataset.iso;
    if (iso) {
      const localTime = new Date(iso).toLocaleString(); // formatted for user's locale
      span.textContent = `${localTime}`;
    }
  });

  function handleUnlock(button) {
    const row = button.closest('.row');
    const container = row.nextElementSibling;
    const id = button.dataset.id;
    const name = row.dataset.deviceName;

    container.innerHTML = '';

    const bar = document.createElement('div');
    bar.className = 'progress-bar';
    container.appendChild(bar);

    buttons.forEach(b => b.classList.add('disabled'));

    requestAnimationFrame(() => {
      bar.style.width = '100%';
    });

    const timestamp = Date.now();
    fetch(`/unlock?id=${id}&name=${encodeURIComponent(name)}&ts=${timestamp}`)
      .finally(() => {
        setTimeout(() => {
          container.innerHTML = '';
          buttons.forEach(b => b.classList.remove('disabled'));
        }, 1000);
      });
  }

  buttons.forEach(btn => {
    let pressTimer = null;
    let longPress = false;

    const startPress = (event) => {
    event.preventDefault(); // Prevent default behavior on touch
    longPress = false;
    pressTimer = setTimeout(() => {
      longPress = true;
      const row = btn.closest('.row');
      const id = btn.dataset.id;
      const name = row.dataset.deviceName;
      const url = `/?id=${id}&name=${encodeURIComponent(name)}`;
      window.open(url, '_blank');
    }, 1500);
    };

    const cancelPress = () => {
        clearTimeout(pressTimer);
    };

    // Mouse
    btn.addEventListener('mousedown', startPress);
    btn.addEventListener('mouseup', cancelPress);
    btn.addEventListener('mouseleave', cancelPress);

    // Touch
    btn.addEventListener('touchstart', startPress, { passive: false });
    btn.addEventListener('touchend', (e) => {
        cancelPress();
        if (!longPress) {
          handleUnlock(btn); // ✅ This was missing
        }
    });
    btn.addEventListener('touchcancel', cancelPress);

    // Desktop click
    btn.addEventListener('click', (e) => {
    if (!longPress) {
      handleUnlock(btn);
    }
    });
  });

  // Trigger from URL if present
  const params = new URLSearchParams(window.location.search);
  const autoId = params.get('id');
  const autoName = params.get('name');

  if (autoId && autoName) {
    const match = Array.from(buttons).find(btn => {
      const row = btn.closest('.row');
      return btn.dataset.id === autoId && row?.dataset.deviceName === autoName;
    });

    if (match) {
      handleUnlock(match);
    }
  }
});
