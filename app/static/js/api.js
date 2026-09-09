const API_BASE = "/api";

async function apiRequest(method, path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json();

  if (!response.ok) {
    const message = (data && data.detail) || "Erro inesperado";
    throw new Error(message);
  }

  return data;
}

function apiGet(path) {
  return apiRequest("GET", path);
}

function apiPost(path, body) {
  return apiRequest("POST", path, body);
}

function apiPut(path, body) {
  return apiRequest("PUT", path, body);
}

function apiDelete(path) {
  return apiRequest("DELETE", path);
}

function formatCents(cents) {
  return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
