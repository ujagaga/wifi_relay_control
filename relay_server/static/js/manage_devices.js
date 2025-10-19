document.addEventListener('DOMContentLoaded', function () {

  const fileInput = document.getElementById("firmware_file");
  const form = document.getElementById("firmware_form");

  if (fileInput && form) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) form.submit();
    });
  }

  const modal = document.getElementById('updateModal');
  const modalName = document.getElementById('modalFirmwareName');
  const modalInput = document.getElementById('modalFirmwareInput');

  window.openUpdateModal = function(firmwareName) {
    modalName.textContent = firmwareName;
    modalInput.value = firmwareName;
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    const firstCheckbox = modal.querySelector('input[type="checkbox"]');
    if (firstCheckbox) firstCheckbox.focus();
    else modal.querySelector('button[type="submit"]').focus();
    document.body.style.overflow = 'hidden';
  };

  window.closeUpdateModal = function() {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeUpdateModal();
  });

  modal.addEventListener('click', function(e) {
    if (e.target === modal) closeUpdateModal();
  });

  const startForm = document.getElementById('startUpdateForm');
  startForm.addEventListener('submit', function(e){
    const checked = startForm.querySelectorAll('input[type="checkbox"]:checked');
    if (checked.length === 0) {
      e.preventDefault();
      alert('Please select at least one device to update.');
    }
  });

  // Ping time formatting (same as in home)
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
