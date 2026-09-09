"""Matriz de autorização: cliente comum só pode ver/operar as próprias contas;
admin (o `client` de teste já é logado como admin, ver conftest.py) pode tudo."""

from tests.helpers import generate_valid_cpf


def _create_customer(client, email, cpf, password="Password123"):
    return client.post(
        "/api/customers",
        json={"name": "Cliente", "email": email, "cpf": cpf, "password": password},
    ).json()


def _create_account(client, customer_id, number):
    return client.post(
        "/api/accounts", json={"customer_id": customer_id, "agency": "0001", "number": number}
    ).json()


def _login(client, email, password="Password123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200


def test_customer_cannot_list_all_customers(client):
    _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    _login(client, "a@example.com")

    response = client.get("/api/customers")
    assert response.status_code == 403


def test_customer_cannot_create_account(client):
    customer_a = _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    _login(client, "a@example.com")

    response = client.post(
        "/api/accounts",
        json={"customer_id": customer_a["id"], "agency": "0001", "number": "999999"},
    )
    assert response.status_code == 403


def test_customer_cannot_see_another_customers_account(client):
    _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    customer_b = _create_customer(client, "b@example.com", generate_valid_cpf("111444777"))
    account_b = _create_account(client, customer_b["id"], "222222")

    _login(client, "a@example.com")

    response = client.get(f"/api/accounts/{account_b['id']}")
    assert response.status_code == 403


def test_customer_can_see_own_account(client):
    customer_a = _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    account_a = _create_account(client, customer_a["id"], "111111")

    _login(client, "a@example.com")

    response = client.get(f"/api/accounts/{account_a['id']}")
    assert response.status_code == 200


def test_customer_can_deposit_in_own_account(client):
    customer_a = _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    account_a = _create_account(client, customer_a["id"], "111111")

    _login(client, "a@example.com")

    response = client.post(f"/api/accounts/{account_a['id']}/deposit", json={"amount_cents": 1000})
    assert response.status_code == 201


def test_admin_can_deposit_in_any_account(client):
    customer_a = _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    account_a = _create_account(client, customer_a["id"], "111111")
    # `client` continua logado como admin aqui (não fizemos login como customer_a).

    response = client.post(f"/api/accounts/{account_a['id']}/deposit", json={"amount_cents": 1000})
    assert response.status_code == 201


def test_customer_cannot_deposit_in_anothers_account(client):
    _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    customer_b = _create_customer(client, "b@example.com", generate_valid_cpf("111444777"))
    account_b = _create_account(client, customer_b["id"], "222222")

    _login(client, "a@example.com")

    response = client.post(f"/api/accounts/{account_b['id']}/deposit", json={"amount_cents": 1000})
    assert response.status_code == 403


def test_customer_sees_only_own_accounts_in_list(client):
    customer_a = _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    customer_b = _create_customer(client, "b@example.com", generate_valid_cpf("111444777"))
    _create_account(client, customer_a["id"], "111111")
    _create_account(client, customer_b["id"], "222222")

    _login(client, "a@example.com")

    response = client.get("/api/accounts")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 1
    assert accounts[0]["customer_id"] == customer_a["id"]


def test_customer_cannot_edit_or_delete_pix_key_of_another_account(client):
    _create_customer(client, "a@example.com", generate_valid_cpf("529982247"))
    customer_b = _create_customer(client, "b@example.com", generate_valid_cpf("111444777"))
    account_b = _create_account(client, customer_b["id"], "222222")
    pix_key = client.post(
        "/api/pix-keys",
        json={"account_id": account_b["id"], "type": "EMAIL", "value": "b@example.com"},
    ).json()

    _login(client, "a@example.com")

    response = client.put(f"/api/pix-keys/{pix_key['id']}", json={"value": "hacked@example.com"})
    assert response.status_code == 403

    response = client.delete(f"/api/pix-keys/{pix_key['id']}")
    assert response.status_code == 403


def test_accounts_endpoint_requires_authentication(anonymous_client):
    response = anonymous_client.get("/api/accounts")
    assert response.status_code == 401
