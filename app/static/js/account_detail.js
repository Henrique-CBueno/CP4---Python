const accountId = document.body.dataset.accountId;
const infoEl = document.getElementById("account-info");
const errorEl = document.getElementById("account-detail-error");
const depositFormEl = document.getElementById("deposit-form");
const withdrawFormEl = document.getElementById("withdraw-form");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

async function loadAccount() {
  try {
    const account = await apiGet(`/accounts/${accountId}`);
    renderAccount(account);
  } catch (err) {
    showError(err.message);
  }
}

function renderAccount(account) {
  infoEl.innerHTML = `
    <p><strong>Cliente:</strong> #${account.customer_id}</p>
    <p><strong>Agência:</strong> ${account.agency}</p>
    <p><strong>Número:</strong> ${account.number}</p>
    <p><strong>Apelido:</strong> ${account.label ?? "-"}</p>
    <p><strong>Saldo:</strong> ${formatCents(account.balance_cents)}</p>
  `;
}

depositFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const amountCents = Math.round(Number(depositFormEl.amount.value) * 100);

  try {
    await apiPost(`/accounts/${accountId}/deposit`, { amount_cents: amountCents });
    depositFormEl.reset();
    await loadAccount();
  } catch (err) {
    showError(err.message);
  }
});

withdrawFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const amountCents = Math.round(Number(withdrawFormEl.amount.value) * 100);

  try {
    await apiPost(`/accounts/${accountId}/withdraw`, { amount_cents: amountCents });
    withdrawFormEl.reset();
    await loadAccount();
  } catch (err) {
    showError(err.message);
  }
});

loadAccount();
