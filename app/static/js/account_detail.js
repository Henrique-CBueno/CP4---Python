const accountId = document.body.dataset.accountId;
const infoEl = document.getElementById("account-info");
const errorEl = document.getElementById("account-detail-error");
const depositFormEl = document.getElementById("deposit-form");
const withdrawFormEl = document.getElementById("withdraw-form");
const pixKeyFormEl = document.getElementById("pix-key-form");
const pixKeyListEl = document.getElementById("pix-keys-list");
const pixKeyEditingIdEl = document.getElementById("pix-key-editing-id");
const pixKeySubmitButtonEl = pixKeyFormEl.querySelector("button[type=submit]");
const statementListEl = document.getElementById("statement-list");

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
    await loadStatement();
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
    await loadStatement();
  } catch (err) {
    showError(err.message);
  }
});

function resetPixKeyForm() {
  pixKeyFormEl.reset();
  pixKeyEditingIdEl.value = "";
  pixKeySubmitButtonEl.textContent = "Cadastrar chave";
}

async function loadPixKeys() {
  try {
    const pixKeys = await apiGet(`/accounts/${accountId}/pix-keys`);
    renderPixKeys(pixKeys);
  } catch (err) {
    showError(err.message);
  }
}

function renderPixKeys(pixKeys) {
  pixKeyListEl.innerHTML = "";
  for (const pixKey of pixKeys) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${pixKey.id}</td>
      <td>${pixKey.type}</td>
      <td>${pixKey.value}</td>
      <td>
        <button type="button" data-action="edit" data-id="${pixKey.id}" data-type="${pixKey.type}" data-value="${pixKey.value}">editar</button>
        <button type="button" data-action="delete" data-id="${pixKey.id}">remover</button>
      </td>
    `;
    pixKeyListEl.appendChild(row);
  }
}

pixKeyListEl.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const id = button.dataset.id;
  clearError();

  if (button.dataset.action === "delete") {
    try {
      await apiDelete(`/pix-keys/${id}`);
      await loadPixKeys();
    } catch (err) {
      showError(err.message);
    }
  }

  if (button.dataset.action === "edit") {
    pixKeyFormEl.type.value = button.dataset.type;
    pixKeyFormEl.value.value = button.dataset.value;
    pixKeyEditingIdEl.value = id;
    pixKeySubmitButtonEl.textContent = "Salvar";
  }
});

pixKeyFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const editingId = pixKeyEditingIdEl.value;

  try {
    if (editingId) {
      await apiPut(`/pix-keys/${editingId}`, {
        type: pixKeyFormEl.type.value,
        value: pixKeyFormEl.value.value,
      });
    } else {
      await apiPost("/pix-keys", {
        account_id: Number(accountId),
        type: pixKeyFormEl.type.value,
        value: pixKeyFormEl.value.value,
      });
    }
    resetPixKeyForm();
    await loadPixKeys();
  } catch (err) {
    showError(err.message);
  }
});

async function loadStatement() {
  try {
    const transactions = await apiGet(`/accounts/${accountId}/transactions`);
    renderStatement(transactions);
  } catch (err) {
    showError(err.message);
  }
}

function renderStatement(transactions) {
  statementListEl.innerHTML = "";
  for (const transaction of transactions) {
    const isCredit = String(transaction.destination_account_id) === String(accountId);
    const direction = isCredit ? "Entrada" : "Saída";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(transaction.created_at).toLocaleString("pt-BR")}</td>
      <td>${transaction.type}</td>
      <td>${direction}</td>
      <td>${formatCents(transaction.amount_cents)}</td>
    `;
    statementListEl.appendChild(row);
  }
}

loadAccount();
loadPixKeys();
loadStatement();
