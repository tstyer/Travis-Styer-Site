/* global module */

const nameSearch = document.getElementById("name-search");
const projects = document.querySelectorAll(".project-card");
const tags = document.querySelectorAll(".tag");

function toggleInfoParagraph() {
  const info = document.getElementById("temp-p");
  let visibleCount = 0;

  projects.forEach((p) => {
    if (p.style.display !== "none") {
      visibleCount++;
    }
  });

  if (!info) return;

  if (visibleCount > 0) {
    info.classList.add("hidden");
  } else {
    info.classList.remove("hidden");
  }
}

function filterProjects(nameSearchEl, projectEls) {
  const nameQuery = (nameSearchEl?.value || "").toLowerCase();
  const visibleProjects = [];

  projectEls.forEach((project) => {
    const name = (project.getAttribute("data-name") || "").toLowerCase();
    const match = name.includes(nameQuery);

    if (match) {
      project.style.display = "";
      visibleProjects.push(project);
    } else {
      project.style.display = "none";
      project.classList.remove("fade-in-up");
    }
  });

  const info = document.getElementById("temp-p");
  if (info) {
    if (visibleProjects.length > 0) {
      info.classList.add("hidden");
    } else {
      info.classList.remove("hidden");
    }
  }

  // staggered re-entry
  visibleProjects.forEach((project, index) => {
    project.classList.remove("fade-in-up");
    setTimeout(() => {
      project.classList.add("fade-in-up");
      project.style.animationDelay = `${index * 100}ms`;
    }, 0);
  });
}

function hideAll() {
  projects.forEach((p) => {
    p.style.display = "none";
    p.classList.remove("fade-in-up");
    p.style.animationDelay = "0ms";
  });
  toggleInfoParagraph();
}

function clearActiveTags() {
  document
    .querySelectorAll(".tag.active")
    .forEach((t) => t.classList.remove("active"));
}

function filterByTag(tag) {
  const t = (tag || "").toLowerCase();
  const visibleProjects = [];

  projects.forEach((project) => {
    const projectTags = (project.getAttribute("data-tags") || "").toLowerCase();
    const match = projectTags.includes(t);

    if (match) {
      project.style.display = "";
      visibleProjects.push(project);
    } else {
      project.style.display = "none";
      project.classList.remove("fade-in-up");
    }
  });

  const info = document.getElementById("temp-p");
  if (info) {
    if (visibleProjects.length > 0) {
      info.classList.add("hidden");
    } else {
      info.classList.remove("hidden");
    }
  }

  // staggered wave again
  visibleProjects.forEach((project, index) => {
    project.classList.remove("fade-in-up");
    setTimeout(() => {
      project.classList.add("fade-in-up");
      project.style.animationDelay = `${index * 150}ms`;
    }, 0);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  // start: all hidden
  hideAll();

  // search
  if (nameSearch) {
    nameSearch.addEventListener("input", () => {
      clearActiveTags();
      filterProjects(nameSearch, projects);
      if (!nameSearch.value.trim()) hideAll();
    });
  }

  // tag clicks
  if (tags.length) {
    tags.forEach((tagBtn) => {
      tagBtn.addEventListener("click", function () {
        clearActiveTags();
        this.classList.add("active");
        if (nameSearch) nameSearch.value = "";
        filterByTag(this.dataset.tag || "");
      });
    });
  }

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
   COMMENTS MODAL
*/
const modal = document.getElementById("comments-modal");
const modalBody = document.getElementById("comments-modal-body");

function openCommentsModal(projectId) {
  if (!modal) return;
  modal.classList.add("is-open");
  modalBody.innerHTML = "<p>Loading comments…</p>";

  fetch(`/project/${projectId}/comments/partial/`, {
    credentials: "same-origin",
  })
    .then((res) => res.text())
    .then((html) => {
      modalBody.innerHTML = html;
      wireCommentsModal(modalBody);
    })
    .catch(() => {
      modalBody.innerHTML = "<p>Couldn't load comments.</p>";
    });
}

function closeCommentsModal() {
  if (!modal) return;
  modal.classList.remove("is-open");
}

// attach to each comment button
document.querySelectorAll(".project-card .comment-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    const card = this.closest(".project-card");
    const projectId = card?.dataset?.projectId;
    if (projectId) {
      openCommentsModal(projectId);
    }
  });
});

const closeBtn = document.querySelector(".comments-modal__close");
if (closeBtn) {
  closeBtn.addEventListener("click", closeCommentsModal);
}

const commentsBackdrop = document.querySelector(".comments-modal__backdrop");
if (commentsBackdrop) {
  commentsBackdrop.addEventListener("click", closeCommentsModal);
}

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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
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
  if (authModal) authModal.classList.remove("is-open");
}

if (closeAuthBtn) closeAuthBtn.addEventListener("click", closeAuth);
if (authBackdrop) authBackdrop.addEventListener("click", closeAuth);

// toggle login/register text + hidden input
if (switchToRegister) {
  switchToRegister.addEventListener("click", () => {
    if (authModeInput.value === "login") {
      authModeInput.value = "register";
      if (authTitle) authTitle.textContent = "Create an account";
      if (authSub) authSub.textContent = "Register to leave comments.";
      switchToRegister.textContent = "I already have an account";
    } else {
      authModeInput.value = "login";
      if (authTitle) authTitle.textContent = "Welcome back";
      if (authSub) authSub.textContent = "Sign in to leave a comment.";
      switchToRegister.textContent = "Create an account";
    }
  });
}

/* ---- CSRF helper ---- */
function getCsrfTokenFromForm(formEl) {
  const tokenInput = formEl.querySelector('input[name="csrfmiddlewaretoken"]');
  return tokenInput ? tokenInput.value : "";
}

function wireCommentsModal(rootEl) {
  if (!rootEl) return;

  const commentForm = rootEl.querySelector(".comments-form");
  const textarea =
    commentForm &&
    (commentForm.querySelector("textarea") ||
      commentForm.querySelector("[name='content']"));
  const submitBtn =
    commentForm && commentForm.querySelector(".comments-btn-primary");

  // Create / update submit
  if (commentForm) {
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(commentForm);
      const action = commentForm.getAttribute("action");
      const csrfToken = getCsrfTokenFromForm(commentForm);

      const headers = { "X-Requested-With": "XMLHttpRequest" };
      if (csrfToken) headers["X-CSRFToken"] = csrfToken;

      fetch(action, {
        method: "POST",
        body: formData,
        headers: headers,
        credentials: "same-origin",
      })
        .then((res) => res.text())
        .then((html) => {
          modalBody.innerHTML = html;
          wireCommentsModal(modalBody); // re-wire new DOM
        })
        .catch(() => {
          alert("Could not post comment.");
        });
    });
  }

  // Delete
  rootEl.querySelectorAll(".comment-delete-form").forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!confirm("Delete this comment?")) return;

      const formData = new FormData(form);
      const action = form.getAttribute("action");
      const csrfToken = getCsrfTokenFromForm(form);

      const headers = { "X-Requested-With": "XMLHttpRequest" };
      if (csrfToken) headers["X-CSRFToken"] = csrfToken;

      fetch(action, {
        method: "POST",
        body: formData,
        headers: headers,
        credentials: "same-origin",
      })
        .then((res) => res.text())
        .then((html) => {
          modalBody.innerHTML = html;
          wireCommentsModal(modalBody); // re-wire after update
        })
        .catch(() => {
          alert("Could not delete comment.");
        });
    });
  });

  rootEl.querySelectorAll(".comment-edit-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      if (!commentForm || !textarea) return;

      const newContent = this.dataset.content || "";
      const updateUrl = this.dataset.updateUrl;

      textarea.value = newContent;

      if (updateUrl) {
        commentForm.setAttribute("action", updateUrl);
      }

      if (submitBtn) {
        submitBtn.textContent = "Update comment";
      }

      textarea.focus();
    });
  });
}

// submit handler (always) – auth modal
const authForm = document.getElementById("auth-form");
if (authForm) {
  const submitBtn = authForm.querySelector(".auth-primary");

  authForm.addEventListener("submit", (e) => {
    e.preventDefault();

    if (!submitBtn) return;

    // Start loading state
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Signing in…";
    submitBtn.classList.add("is-loading");
    submitBtn.disabled = true;

    const formData = new FormData(authForm);
    const mode = formData.get("mode"); // "login" or "register"
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
          window.location.reload(); // page will re-render with "Sign out"
        } else {
          alert(data.error || "Could not complete request.");
          // Reset button on error
          submitBtn.textContent = originalText;
          submitBtn.classList.remove("is-loading");
          submitBtn.disabled = false;
        }
      })
      .catch(() => {
        alert("Network error");
        // Reset on network failure
        submitBtn.textContent = originalText;
        submitBtn.classList.remove("is-loading");
        submitBtn.disabled = false;
      });
  });
}

// Export for tests
if (typeof module !== "undefined" && module.exports) {
  module.exports = { filterProjects, hideAll, filterByTag };
} else {
  window.filterProjects = filterProjects;
}
