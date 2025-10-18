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

    document.querySelectorAll('.ping_time').forEach(span => {
      const utcTime = span.dataset.iso;
      const date = new Date(utcTime);

      // Format parts
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
      const year = date.getFullYear();

      const hour = String(date.getHours()).padStart(2, '0'); // 24-hour format
      const minute = String(date.getMinutes()).padStart(2, '0');

      const formatted = `${day}.${month}.${year} ${hour}:${minute}`;
      span.textContent = formatted;
    });

    const fileInput = document.getElementById("firmware_file");
    const form = document.getElementById("firmware_form");

    if (fileInput && form) {
    fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                form.submit();
            }
        });
    }

    (function(){
  const modal = document.getElementById('updateModal');
  const modalName = document.getElementById('modalFirmwareName');
  const modalInput = document.getElementById('modalFirmwareInput');

  // Safely encode firmware name into element id: we rely on passing the exact filename into inputs/labels,
  // so we only need to set text values and hidden input values here.
  window.openUpdateModal = function(firmwareName) {
    modalName.textContent = firmwareName;
    modalInput.value = firmwareName;
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    // focus first checkbox or form submit for keyboard users
    const firstCheckbox = modal.querySelector('input[type="checkbox"]');
    if (firstCheckbox) firstCheckbox.focus();
    else modal.querySelector('button[type="submit"]').focus();
    // prevent body scroll
    document.body.style.overflow = 'hidden';
  };

  window.closeUpdateModal = function() {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  // close modal on Esc and on clicking outside modal-content
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closeUpdateModal();
    }
  });

  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeUpdateModal();
    }
  });

  // Ensure when form submits, checked devices are sent as devices[] or devices depending on your backend expectation.
  // Flask request.form.getlist('devices') will read multiple inputs named "devices".
  // No extra JS required here, but you can validate selection count before submit if desired.
  const form = document.getElementById('startUpdateForm');
  form.addEventListener('submit', function(e){
    const checked = form.querySelectorAll('input[type="checkbox"]:checked');
    if (checked.length === 0) {
      e.preventDefault();
      alert('Please select at least one device to update.');
    }
    // otherwise let the form submit normally
  });
})();

});
