const formEl = document.getElementById("pix-transfer-form");
const errorEl = document.getElementById("pix-transfer-error");
const successEl = document.getElementById("pix-transfer-success");

function showError(message) {
  successEl.hidden = true;
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function showSuccess(transaction) {
  errorEl.hidden = true;
  successEl.textContent = `Transferência realizada: ${formatCents(transaction.amount_cents)} da conta #${transaction.source_account_id} para a conta #${transaction.destination_account_id}.`;
  successEl.hidden = false;
}

async function loadAccountsIntoSelect() {
  const select = formEl.source_account_id;
  select.innerHTML = "";
  const accounts = await apiGet("/accounts");
  for (const account of accounts) {
    const option = document.createElement("option");
    option.value = account.id;
    option.textContent = `Conta #${account.id} — ${account.number}`;
    select.appendChild(option);
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;
  successEl.hidden = true;

  const amountCents = Math.round(Number(formEl.amount.value) * 100);

  try {
    const transaction = await apiPost("/pix/transfers", {
      source_account_id: Number(formEl.source_account_id.value),
      pix_key_value: formEl.pix_key_value.value,
      amount_cents: amountCents,
    });
    formEl.reset();
    await loadAccountsIntoSelect();
    showSuccess(transaction);
  } catch (err) {
    showError(err.message);
  }
});

(async function init() {
  try {
    await loadAccountsIntoSelect();
  } catch (err) {
    showError(err.message);
  }
})();
