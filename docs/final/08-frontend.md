# 08 — Frontend

## Stack

Sem framework SPA (sem React/Vue/Angular). HTML servido por Jinja2
(`app/adapters/inbound/web/pages.py`) + CSS puro (`app/static/css/style.css`) + **JavaScript
vanilla** com `fetch()` consumindo os endpoints REST documentados em `06-api.md`. Nenhuma página usa
`<form action="...">` tradicional (submit HTML nativo) — todo envio de dado é interceptado em
JavaScript (`event.preventDefault()`) e enviado via `fetch()`.

## `api.js` — o único ponto de contato com a API

`app/static/js/api.js` centraliza toda a comunicação HTTP, reaproveitado por todas as outras
páginas:

```js
async function apiRequest(method, path, body) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error((data && data.detail) || "Erro inesperado");
  return data;
}

function apiGet(path)    { return apiRequest("GET", path); }
function apiPost(path, body) { return apiRequest("POST", path, body); }
function apiPut(path, body)  { return apiRequest("PUT", path, body); }
function apiDelete(path) { return apiRequest("DELETE", path); }

function formatCents(cents) {
  return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
```

Dois detalhes importantes:

- **Tratamento de erro uniforme:** qualquer resposta com status `>= 400` é convertida em uma
  `Error` JavaScript com a mensagem vinda de `{"detail": "..."}` do backend — cada página só
  precisa de um `try/catch` ao redor da chamada, sem duplicar a lógica de leitura de erro.
- **`formatCents()` é a única conversão de centavos para reais em todo o projeto.** A API sempre
  envia/recebe `*_cents` como inteiro (ver `04-modelo-de-dominio.md` e `05-banco-de-dados.md`); a
  formatação para `"R$ 10,50"` acontece exclusivamente aqui, no frontend — nunca em Python.

## `auth.js` — barra de usuário e gate de admin no cliente

Incluído em toda página protegida. Ao carregar, chama `GET /api/auth/me`; se a resposta falhar
(`401`, sem sessão), redireciona para `/login`. Se a sessão é válida, mostra o nome do usuário e, se
`role !== "ADMIN"`, esconde (`el.hidden = true`) todo elemento marcado com o atributo
`data-admin-only` no HTML. Liga também o botão de logout (`POST /api/auth/logout` → redireciona para
`/login`).

Importante: este *gate* no JavaScript é só uma conveniência de interface — **não é a autorização
real**. A autorização de verdade acontece no backend, em cada Controller (`ensure_admin`,
`ensure_self_or_admin`, `ensure_account_owner_or_admin`, ver `06-api.md`); esconder um botão no
frontend não impede uma chamada direta à API — é o backend, não o `data-admin-only`, que devolveria
`403` se alguém tentasse.

## Autenticação e gate de página

`/login` é a única página pública. Todas as demais são servidas por `pages.py`, que checa a sessão
no servidor via `_current_customer(request, db)` antes de renderizar o template — sem sessão válida,
`RedirectResponse("/login")`. A página `/customers` adicionalmente exige `role == "ADMIN"` no
próprio `pages.py` (não só no JavaScript), senão redireciona para `/accounts`.

## Páginas (6 no total)

### `/login` — Entrar
Formulário email/senha (`login.js`) → `POST /api/auth/login` → redireciona para `/`. Em caso de
erro, mostra `err.message` (vindo de `detail`) em `#login-error`.

### `/` — Dashboard
`dashboard.js` chama `GET /api/auth/me`, depois `GET /api/accounts` (já filtrado pelo backend), e —
só se admin — `GET /api/customers`. Mostra contagem de clientes (`data-admin-only`), contagem de
contas e soma de todos os saldos (`accounts.reduce(...)`, formatado com `formatCents()`).

### `/customers` — Clientes (admin)
`customers.js`: tabela com `GET /api/customers`; formulário único serve tanto para criar
(`POST /api/customers`) quanto para editar (`PUT /api/customers/{id}`) — ao clicar "editar", o campo
`cpf`, `password` e `role` são desabilitados no formulário (não editáveis por essa rota) e o botão
muda para "Salvar"; remoção via `DELETE /api/customers/{id}`. Cada linha tem um link
"contas" → `/accounts?customer_id={id}`.

### `/accounts` — Contas
`accounts.js`: se a URL tem `?customer_id=N` (vindo do link acima), lista via
`GET /customers/{N}/accounts`; senão, `GET /accounts` (admin vê todas, cliente só as suas, já
filtrado pelo backend). Formulário de criação/edição e botões de remover só aparecem para admin
(`isAdmin`, obtido de `GET /api/auth/me`) — reforço, no JS, do que o backend já impõe.

### `/accounts/{id}` — Detalhe da conta
Página central do frontend — reúne tudo sobre uma conta específica (`account_detail.js`):

- **Dados + saldo:** `GET /api/accounts/{id}`, saldo formatado com `formatCents()`.
- **Depósito / saque:** formulários com campo de valor em reais, convertidos para centavos no JS
  (`Math.round(Number(valor) * 100)`) antes de `POST /api/accounts/{id}/deposit` ou `/withdraw`;
  após sucesso, recarrega saldo e extrato sem recarregar a página inteira.
- **Chaves Pix da conta:** `GET /api/accounts/{id}/pix-keys`; formulário de criação
  (`account_id` fixo = id da página); quando o tipo selecionado é `RANDOM`, o valor é preenchido
  automaticamente com `crypto.randomUUID()` e o campo vira somente leitura.
- **Extrato:** `GET /api/accounts/{id}/transactions`; a direção (Entrada/Saída) é calculada no
  próprio JS comparando `destination_account_id` com o id da conta atual — **não vem pronta da API**.

### `/pix/transfer` — Transferência Pix
`pix_transfer.js`: `source_account_id` (select populado via `GET /api/accounts`), `pix_key_value`
(texto livre) e valor em reais (convertido para centavos) → `POST /api/pix/transfers`. Mensagens de
erro específicas por cenário (chave não encontrada, saldo insuficiente, mesma conta) vêm todas do
mesmo `detail` da resposta de erro, exibido em `#pix-transfer-error`. Sucesso mostra a transação
criada em `#pix-transfer-success`.

## Tabela — Página, Rota Web, Ações principais, Endpoints usados

| Página | Rota Web | Principais ações | Endpoints da API usados |
|---|---|---|---|
| Entrar | `GET /login` | login | `POST /api/auth/login` |
| Dashboard | `GET /` | ver contagens e saldo total | `GET /api/auth/me`, `GET /api/accounts`, `GET /api/customers` (admin) |
| Clientes | `GET /customers` | listar, criar, editar, remover cliente; ver contas de um cliente | `GET/POST/PUT/DELETE /api/customers`, `GET /api/customers/{id}/accounts` |
| Contas | `GET /accounts` | listar, criar, editar, remover conta | `GET/POST/PUT/DELETE /api/accounts`, `GET /api/customers/{id}/accounts`, `GET /api/customers` |
| Detalhe da conta | `GET /accounts/{id}` | ver saldo, depositar, sacar, gerenciar chaves Pix, ver extrato | `GET /api/accounts/{id}`, `/balance`, `/pix-keys`, `/transactions`; `POST /deposit`, `/withdraw`; `POST/PUT/DELETE /api/pix-keys` |
| Transferência Pix | `GET /pix/transfer` | transferir entre contas via chave Pix | `GET /api/accounts`, `POST /api/pix/transfers` |

(todas as páginas, exceto `/login`, também chamam `GET /api/auth/me` e `POST /api/auth/logout` via
`auth.js`, incluído em todas elas)

## Como isso satisfaz o requisito "o frontend deve consumir a API"

Não existe nenhum caminho, em nenhuma das 6 páginas, em que dados sejam lidos ou escritos sem passar
por `fetch()` contra `/api/...`. Os templates Jinja2 (`app/templates/*.html`) renderizam apenas a
casca estática da página (layout, formulários vazios, `<tbody>` vazios) — todo dado dinâmico
(listas, saldos, extratos) é buscado e inserido no DOM depois do carregamento, via JavaScript. A
única exceção é o *gate* de sessão da própria página HTML (`pages.py` decide se redireciona para
`/login` antes de servir o template), que é responsabilidade do servidor de páginas, não da API REST
— e mesmo essa checagem é duplicada no lado do cliente (via `GET /api/auth/me` em `auth.js`) para
manter a barra de navegação e os elementos `data-admin-only` consistentes com o usuário logado.

## Tratamento de erro (padrão em todas as páginas)

Toda chamada `fetch()` que falha (status `>= 400`) segue o mesmo padrão, repetido em cada arquivo
JS: captura a exceção lançada por `apiRequest()` e exibe `err.message` (o `detail` vindo da API) em
uma `<div class="alert alert-error">` específica da seção. Como `formEl.reset()`/`resetForm()` só é
chamado dentro do bloco `try` (depois de um sucesso), um erro nunca limpa o formulário — os valores
digitados permanecem, prontos para o usuário corrigir e reenviar, sem precisar recarregar a página.
Nenhuma página desabilita o botão de submit durante a chamada, então também não há um botão "preso"
para reabilitar depois de um erro.
