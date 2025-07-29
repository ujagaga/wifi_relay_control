document.addEventListener('DOMContentLoaded', function () {
  const buttons = document.querySelectorAll('.big_btn');

  document.querySelectorAll('.ping_time').forEach(span => {
    const iso = span.dataset.iso;
    if (iso) {
      const localTime = new Date(iso).toLocaleString();
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

      const startPress = () => {
        longPress = false;
        pressTimer = setTimeout(() => {
          longPress = true;
          const row = btn.closest('.row');
          const id = btn.dataset.id;
          const name = row.dataset.deviceName;
          const url = `/?id=${id}&name=${encodeURIComponent(name)}`;
          window.open(url, '_blank');
        }, 800);
      };

      const cancelPress = () => {
        clearTimeout(pressTimer);
      };

      btn.addEventListener('pointerdown', startPress, { passive: false });
        btn.addEventListener('pointerup', () => {
          cancelPress();
          if (!longPress) {
            handleUnlock(btn);
          }
        }, { passive: false });
        btn.addEventListener('pointerleave', cancelPress, { passive: false });
        btn.addEventListener('pointercancel', cancelPress, { passive: false });

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

  // Modal for apartment number edit
  document.querySelectorAll('.edit-apartment-link').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const email = this.dataset.email;
      const apartment = this.dataset.apartment;

      document.getElementById('modal-email').value = email;
      document.getElementById('modal-apartment').value = apartment;
      document.getElementById('apartmentModal').style.display = 'block';
    });
  });

  document.querySelector('.modal .close').addEventListener('click', function () {
    document.getElementById('apartmentModal').style.display = 'none';
  });

  window.addEventListener('click', function (event) {
    const modal = document.getElementById('apartmentModal');
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});
