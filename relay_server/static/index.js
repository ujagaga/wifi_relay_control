document.addEventListener('DOMContentLoaded', function() {
  const buttons = document.querySelectorAll('.big_btn');

  buttons.forEach(btn => {
    btn.addEventListener('click', function() {
      const button = btn;
      const row = button.closest('.row');
      const container = row.nextElementSibling; // .progress-bar-container
      const id = button.dataset.id;
      const name = row.dataset.deviceName;

      // Clear any previous progress bars
      container.innerHTML = '';

      // Create new progress bar
      const bar = document.createElement('div');
      bar.className = 'progress-bar';
      container.appendChild(bar);

      // Disable all buttons
      buttons.forEach(b => b.classList.add('disabled'));

      // Animate it
      requestAnimationFrame(() => {
        bar.style.width = '100%';
      });

      // Fire request
      fetch(`/unlock?id=${id}&name=${encodeURIComponent(name)}`)
        .finally(() => {
          // Wait for the progress bar to finish (1 second)
          setTimeout(() => {
            container.innerHTML = ''; // remove bar

            // Re-enable all buttons
            buttons.forEach(b => b.classList.remove('disabled'));
          }, 1000);
        });
    });
  });
});
