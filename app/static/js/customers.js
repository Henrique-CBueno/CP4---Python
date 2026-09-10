const listEl = document.getElementById("customers-list");
const formEl = document.getElementById("customer-form");
const errorEl = document.getElementById("customers-error");
const editModalEl = document.getElementById("customer-edit-modal");
const editFormEl = document.getElementById("customer-edit-form");
const editIdEl = editFormEl.elements.id;

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
}

function closeEditModal() {
  editModalEl.close();
  editFormEl.reset();
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
      <td>${customer.role === "ADMIN" ? "Admin" : "Cliente"}</td>
      <td>
        <a href="/accounts?customer_id=${customer.id}">contas</a>
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
    editIdEl.value = id;
    editFormEl.name.value = button.dataset.name;
    editFormEl.email.value = button.dataset.email;
    editModalEl.showModal();
  }
});

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  try {
    await apiPost("/customers", {
      name: formEl.name.value,
      email: formEl.email.value,
      cpf: formEl.cpf.value,
      password: formEl.password.value,
      role: formEl.role.value,
    });
    resetForm();
    await loadCustomers();
  } catch (err) {
    showError(err.message);
  }
});

editFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  try {
    await apiPut(`/customers/${editIdEl.value}`, {
      name: editFormEl.name.value,
      email: editFormEl.email.value,
    });
    closeEditModal();
    await loadCustomers();
  } catch (err) {
    showError(err.message);
  }
});

editModalEl.addEventListener("click", (event) => {
  if (event.target === editModalEl || event.target.closest("[data-modal-cancel], .modal-close")) {
    closeEditModal();
  }
});

loadCustomers();
