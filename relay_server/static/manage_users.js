document.addEventListener('DOMContentLoaded', function () {

  // Add user image preview
  const modal = document.getElementById("imgModal");
  const modalImg = document.getElementById("modalImage");
  const closeBtn = modal.querySelector(".close");

  document.querySelectorAll("img.user_picture").forEach(img => {
  if (img.src && img.src.trim() !== "") {
      img.addEventListener("click", () => {
        modalImg.src = img.src;
        modal.style.display = "flex";
        console.log("Test");
      });
    }
  });

  closeBtn.onclick = () => {
    modal.style.display = "none";
  };

  window.onclick = event => {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  };
});
