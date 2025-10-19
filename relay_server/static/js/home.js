document.addEventListener('DOMContentLoaded', function () {
  const rows = document.querySelectorAll('.row');

  rows.forEach(row => {
    const deviceName = row.dataset.deviceName;
    const buttons = row.querySelectorAll('.big_btn');

    buttons.forEach(btn => {
      const btnId = btn.dataset.id;
      const timestamp = Date.now();
      const href = `/?name=${encodeURIComponent(deviceName)}&id=${btnId}&ts=${timestamp}`;
      btn.setAttribute('href', href);
    });
  });

  function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  const name = getQueryParam('name');
  const id = getQueryParam('id');

  if (name !== null && id !== null) {
    const matchingButton = document.querySelector(`.row[data-device-name="${name}"] .big_btn[data-id="${id}"]`);
    if (matchingButton) {
      matchingButton.classList.add('active');
      setTimeout(() => matchingButton.classList.remove('active'), 500);
    }

    fetch(`/unlock?id=${encodeURIComponent(id)}&name=${encodeURIComponent(name)}`)
      .then(response => {
        if (!response.ok) throw new Error("Network error");
        return response.text();
      })
      .then(result => console.log("Action completed:", result))
      .catch(error => console.error("Action failed:", error));
  }

  // Ping time formatting
  document.querySelectorAll('.ping_time').forEach(span => {
    const utcTime = span.dataset.iso;
    const date = new Date(utcTime);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    span.textContent = `${day}.${month}.${year} ${hour}:${minute}`;
  });
});
