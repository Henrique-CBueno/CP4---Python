const accountId = document.body.dataset.accountId;
const infoEl = document.getElementById("account-info");
const errorEl = document.getElementById("account-detail-error");
const depositFormEl = document.getElementById("deposit-form");
const withdrawFormEl = document.getElementById("withdraw-form");
const pixKeyFormEl = document.getElementById("pix-key-form");
const pixKeyListEl = document.getElementById("pix-keys-list");
const pixKeyEditModalEl = document.getElementById("pix-key-edit-modal");
const pixKeyEditFormEl = document.getElementById("pix-key-edit-form");
const pixKeyEditIdEl = pixKeyEditFormEl.elements.id;
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

function setPixKeyValueReadOnly(form, readOnly) {
  form.value.readOnly = readOnly;
}

pixKeyFormEl.type.addEventListener("change", () => {
  if (pixKeyFormEl.type.value === "RANDOM") {
    pixKeyFormEl.value.value = crypto.randomUUID();
    setPixKeyValueReadOnly(pixKeyFormEl, true);
  } else {
    pixKeyFormEl.value.value = "";
    setPixKeyValueReadOnly(pixKeyFormEl, false);
  }
});

function resetPixKeyForm() {
  pixKeyFormEl.reset();
  setPixKeyValueReadOnly(pixKeyFormEl, false);
}

function closePixKeyEditModal() {
  pixKeyEditModalEl.close();
  pixKeyEditFormEl.reset();
  setPixKeyValueReadOnly(pixKeyEditFormEl, false);
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
    pixKeyEditIdEl.value = id;
    pixKeyEditFormEl.type.value = button.dataset.type;
    pixKeyEditFormEl.value.value = button.dataset.value;
    setPixKeyValueReadOnly(pixKeyEditFormEl, button.dataset.type === "RANDOM");
    pixKeyEditModalEl.showModal();
  }
});

pixKeyFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  try {
    await apiPost("/pix-keys", {
      account_id: Number(accountId),
      type: pixKeyFormEl.type.value,
      value: pixKeyFormEl.value.value,
    });
    resetPixKeyForm();
    await loadPixKeys();
  } catch (err) {
    showError(err.message);
  }
});

pixKeyEditFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  try {
    await apiPut(`/pix-keys/${pixKeyEditIdEl.value}`, {
      type: pixKeyEditFormEl.type.value,
      value: pixKeyEditFormEl.value.value,
    });
    closePixKeyEditModal();
    await loadPixKeys();
  } catch (err) {
    showError(err.message);
  }
});

pixKeyEditFormEl.type.addEventListener("change", () => {
  const isRandom = pixKeyEditFormEl.type.value === "RANDOM";
  if (isRandom) pixKeyEditFormEl.value.value = crypto.randomUUID();
  setPixKeyValueReadOnly(pixKeyEditFormEl, isRandom);
});

pixKeyEditModalEl.addEventListener("click", (event) => {
  if (
    event.target === pixKeyEditModalEl ||
    event.target.closest("[data-modal-cancel], .modal-close")
  ) {
    closePixKeyEditModal();
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
