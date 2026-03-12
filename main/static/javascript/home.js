/* global module */

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

/*
   AUTH MODAL
*/
const authModal = document.getElementById("auth-modal");
const openAuthBtn = document.getElementById("open-auth-modal");
const closeAuthBtn = document.querySelector(".auth-modal__close");
const authBackdrop = document.querySelector(".auth-modal__backdrop");
const switchToRegister = document.getElementById("switch-to-register");
const authTitle = authModal ? authModal.querySelector(".auth-title") : null;
const authSub = authModal ? authModal.querySelector(".auth-sub") : null;
const authModeInput = document.getElementById("auth-mode");

// optional badge
const userBadge = document.getElementById("user-badge");

// eslint-disable-next-line no-unused-vars
function setLoggedIn(username) {
  if (userBadge) {
    userBadge.textContent = `Hi, ${username}`;
    userBadge.classList.add("is-logged-in");
  }

  if (openAuthBtn) {
    openAuthBtn.style.display = "none";
  }
}

if (openAuthBtn && authModal) {
  openAuthBtn.addEventListener("click", () => {
    authModal.classList.add("is-open");
  });
}

function closeAuth() {
  if (authModal) {
    authModal.classList.remove("is-open");
  }
}

if (closeAuthBtn) {
  closeAuthBtn.addEventListener("click", closeAuth);
}

if (authBackdrop) {
  authBackdrop.addEventListener("click", closeAuth);
}


/* ---- CSRF helper ---- */
function getCsrfTokenFromForm(formEl) {
  const tokenInput = formEl.querySelector('input[name="csrfmiddlewaretoken"]');
  return tokenInput ? tokenInput.value : "";
}

// submit handler – auth modal
const authForm = document.getElementById("auth-form");

if (authForm) {
  const submitBtn = authForm.querySelector(".auth-primary");

  authForm.addEventListener("submit", (e) => {
    e.preventDefault();

    if (!submitBtn) return;

    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Signing in…";
    submitBtn.classList.add("is-loading");
    submitBtn.disabled = true;

    const formData = new FormData(authForm);
    const mode = formData.get("mode");
    const csrfToken = getCsrfTokenFromForm(authForm);

    const headers = {
      "X-Requested-With": "XMLHttpRequest",
    };

    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    fetch(`/auth/${mode}/`, {
      method: "POST",
      body: formData,
      headers: headers,
      credentials: "same-origin",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          closeAuth();
          window.location.reload();
        } else {
          alert(data.error || "Could not complete request.");
          submitBtn.textContent = originalText;
          submitBtn.classList.remove("is-loading");
          submitBtn.disabled = false;
        }
      })
      .catch(() => {
        alert("Network error");
        submitBtn.textContent = originalText;
        submitBtn.classList.remove("is-loading");
        submitBtn.disabled = false;
      });
  });
}