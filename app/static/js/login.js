const formEl = document.getElementById("login-form");
const errorEl = document.getElementById("login-error");

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;

  try {
    await apiPost("/auth/login", {
      email: formEl.email.value,
      password: formEl.password.value,
    });
    window.location.href = "/";
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});
