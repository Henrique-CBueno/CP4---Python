const accountId = document.body.dataset.accountId;
const infoEl = document.getElementById("account-info");
const errorEl = document.getElementById("account-detail-error");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
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

loadAccount();
