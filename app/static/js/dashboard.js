const errorEl = document.getElementById("dashboard-error");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

async function loadDashboard() {
  try {
    const me = await apiGet("/auth/me");
    const accounts = await apiGet("/accounts");

    if (me.role === "ADMIN") {
      const customers = await apiGet("/customers");
      document.getElementById("customers-count").textContent = customers.length;
    }

    document.getElementById("accounts-count").textContent = accounts.length;

    const totalCents = accounts.reduce((sum, account) => sum + account.balance_cents, 0);
    document.getElementById("total-balance").textContent = formatCents(totalCents);
  } catch (err) {
    showError(err.message);
  }
}

loadDashboard();
