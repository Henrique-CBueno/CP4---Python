const listEl = document.getElementById("customers-list");
const formEl = document.getElementById("customer-form");
const errorEl = document.getElementById("customers-error");
const editingIdEl = document.getElementById("customer-editing-id");
const submitButtonEl = formEl.querySelector("button[type=submit]");

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
  editingIdEl.value = "";
  formEl.cpf.disabled = false;
  submitButtonEl.textContent = "Cadastrar";
}

async function loadCustomers() {
  clearError();
  try {
    const customers = await apiGet("/customers");
    renderCustomers(customers);
  } catch (err) {
    showError(err.message);
  }
}

function renderCustomers(customers) {
  listEl.innerHTML = "";
  for (const customer of customers) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${customer.id}</td>
      <td>${customer.name}</td>
      <td>${customer.email}</td>
      <td>${customer.cpf}</td>
      <td>
        <button type="button" data-action="edit" data-id="${customer.id}" data-name="${customer.name}" data-email="${customer.email}">editar</button>
        <button type="button" data-action="delete" data-id="${customer.id}">remover</button>
      </td>
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
      await apiDelete(`/customers/${id}`);
      await loadCustomers();
    } catch (err) {
      showError(err.message);
    }
  }

  if (button.dataset.action === "edit") {
    formEl.name.value = button.dataset.name;
    formEl.email.value = button.dataset.email;
    formEl.cpf.value = "";
    formEl.cpf.disabled = true;
    editingIdEl.value = id;
    submitButtonEl.textContent = "Salvar";
  }
});

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const editingId = editingIdEl.value;

  try {
    if (editingId) {
      await apiPut(`/customers/${editingId}`, {
        name: formEl.name.value,
        email: formEl.email.value,
      });
    } else {
      await apiPost("/customers", {
        name: formEl.name.value,
        email: formEl.email.value,
        cpf: formEl.cpf.value,
      });
    }
    resetForm();
    await loadCustomers();
  } catch (err) {
    showError(err.message);
  }
});

loadCustomers();
