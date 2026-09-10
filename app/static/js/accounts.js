const listEl = document.getElementById("accounts-list");
const formEl = document.getElementById("account-form");
const errorEl = document.getElementById("accounts-error");
const editModalEl = document.getElementById("account-edit-modal");
const editFormEl = document.getElementById("account-edit-form");
const editIdEl = editFormEl.elements.id;

const params = new URLSearchParams(window.location.search);
const filterCustomerId = params.get("customer_id");
let isAdmin = false;

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function resetForm() {
  formEl.reset();
  if (filterCustomerId) {
    formEl.customer_id.value = filterCustomerId;
  }
}

function closeEditModal() {
  editModalEl.close();
  editFormEl.reset();
}

async function loadCustomersIntoSelect() {
  const select = formEl.customer_id;
  select.innerHTML = "";
  const customers = await apiGet("/customers");
  for (const customer of customers) {
    const option = document.createElement("option");
    option.value = customer.id;
    option.textContent = `${customer.name} (#${customer.id})`;
    select.appendChild(option);
  }
  if (filterCustomerId) {
    select.value = filterCustomerId;
  }
}

async function loadAccounts() {
  clearError();
  try {
    const accounts = filterCustomerId
      ? await apiGet(`/customers/${filterCustomerId}/accounts`)
      : await apiGet("/accounts");
    renderAccounts(accounts);
  } catch (err) {
    showError(err.message);
  }
}

function renderAccounts(accounts) {
  listEl.innerHTML = "";
  for (const account of accounts) {
    const row = document.createElement("tr");
    const actions = isAdmin
      ? `<button type="button" data-action="edit" data-id="${account.id}" data-agency="${account.agency}" data-label="${account.label ?? ""}">editar</button>
         <button type="button" data-action="delete" data-id="${account.id}">remover</button>`
      : "";
    row.innerHTML = `
      <td><a href="/accounts/${account.id}">${account.id}</a></td>
      <td>${account.customer_id}</td>
      <td>${account.agency}</td>
      <td>${account.number}</td>
      <td>${account.label ?? ""}</td>
      <td>${formatCents(account.balance_cents)}</td>
      <td>${actions}</td>
    `;
    listEl.appendChild(row);
  }
}

listEl.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const id = button.dataset.id;
  clearError();

  if (button.dataset.action === "delete") {
    try {
      await apiDelete(`/accounts/${id}`);
      await loadAccounts();
    } catch (err) {
      showError(err.message);
    }
  }

  if (button.dataset.action === "edit") {
    editIdEl.value = id;
    editFormEl.agency.value = button.dataset.agency;
    editFormEl.label.value = button.dataset.label;
    editModalEl.showModal();
  }
});

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  try {
    await apiPost("/accounts", {
      customer_id: Number(formEl.customer_id.value),
      agency: formEl.agency.value,
      number: formEl.number.value,
      label: formEl.label.value || null,
    });
    resetForm();
    await loadAccounts();
  } catch (err) {
    showError(err.message);
  }
});

editFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  try {
    await apiPut(`/accounts/${editIdEl.value}`, {
      agency: editFormEl.agency.value,
      label: editFormEl.label.value || null,
    });
    closeEditModal();
    await loadAccounts();
  } catch (err) {
    showError(err.message);
  }
});

editModalEl.addEventListener("click", (event) => {
  if (event.target === editModalEl || event.target.closest("[data-modal-cancel], .modal-close")) {
    closeEditModal();
  }
});

(async function init() {
  clearError();
  try {
    const me = await apiGet("/auth/me");
    isAdmin = me.role === "ADMIN";
    if (isAdmin) {
      await loadCustomersIntoSelect();
    }
    await loadAccounts();
  } catch (err) {
    showError(err.message);
  }
})();
