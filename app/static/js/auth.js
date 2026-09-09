async function initAuthBar() {
  let me;
  try {
    me = await apiGet("/auth/me");
  } catch (err) {
    window.location.href = "/login";
    return;
  }

  const userEl = document.getElementById("current-user");
  if (userEl) {
    userEl.textContent = `${me.name} (${me.role === "ADMIN" ? "admin" : "cliente"})`;
  }

  if (me.role !== "ADMIN") {
    document.querySelectorAll("[data-admin-only]").forEach((el) => {
      el.hidden = true;
    });
  }

  const logoutButton = document.getElementById("logout-button");
  if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
      await apiPost("/auth/logout");
      window.location.href = "/login";
    });
  }
}

initAuthBar();
