document.addEventListener("DOMContentLoaded", () => {
  // NAV collapse
  const btn = document.querySelector(".nav-toggle");
  const menu = document.querySelector(".nav-menu");

  if (btn && menu) {
    btn.addEventListener("click", () => {
      menu.classList.toggle("is-open");
    });
  }

  // Toast messages
  const banners = document.querySelectorAll(".message-banner");

  banners.forEach((banner, index) => {
    setTimeout(() => {
      banner.classList.add("show");
    }, 100 * index);

    setTimeout(() => {
      banner.classList.remove("show");
      setTimeout(() => {
        if (banner.parentElement) {
          banner.parentElement.removeChild(banner);
        }
      }, 300);
    }, 4000 + 100 * index);
  });
});