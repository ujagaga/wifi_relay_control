document.addEventListener('DOMContentLoaded', function () {

  // ---------- Image Modal ----------
  const imgModal = document.getElementById('imgModal');
  const modalImage = document.getElementById('modalImage');
  const imgClose = imgModal.querySelector('.close');

  document.querySelectorAll('.user_picture').forEach(img => {
    img.addEventListener('click', function() {
      modalImage.src = this.src;
      imgModal.style.display = 'flex';
    });
  });

  imgClose.addEventListener('click', () => {
    imgModal.style.display = 'none';
  });

  window.addEventListener('click', e => {
    if (e.target === imgModal) {
      imgModal.style.display = 'none';
    }
  });

  // ---------- Apartment Modal ----------
  const apartmentModal = document.getElementById('apartmentModal');
  const modalEmailInput = document.getElementById('modal-email');
  const modalApartmentInput = document.getElementById('modal-apartment');

  document.querySelectorAll('.edit-apartment-link').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const email = this.dataset.email;
      const apartment = this.dataset.apartment;
      modalEmailInput.value = email;
      modalApartmentInput.value = apartment;
      apartmentModal.style.display = 'flex';
    });
  });

  window.addEventListener('click', e => {
    if (e.target === apartmentModal) {
      apartmentModal.style.display = 'none';
    }
  });

});
