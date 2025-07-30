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

  // Helper: Get query parameter from URL
  function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  // Trigger button action if name and id are present in URL
  const name = getQueryParam('name');
  const id = getQueryParam('id');

  if (name !== null && id !== null) {
    // Add visual feedback (optional)
    const matchingButton = document.querySelector(`.row[data-device-name="${name}"] .big_btn[data-id="${id}"]`);
    if (matchingButton) {
      matchingButton.classList.add('active'); // CSS can style this if needed
      setTimeout(() => matchingButton.classList.remove('active'), 500);
    }

    // Make the unlock request
    fetch(`/unlock?id=${encodeURIComponent(id)}&name=${encodeURIComponent(name)}`)
      .then(response => {
        if (!response.ok) throw new Error("Network error");
        return response.text();
      })
      .then(result => {
        console.log("Action completed:", result);
      })
      .catch(error => {
        console.error("Action failed:", error);
      });
  }
});
