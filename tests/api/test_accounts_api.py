from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")


def _create_customer(client, cpf=VALID_CPF):
    response = client.post(
        "/api/customers",
        json={
            "name": "Maria Silva",
            "email": "maria@example.com",
            "cpf": cpf,
            "password": "Password123",
        },
    )
    return response.json()


def _create_account(client, customer_id, agency="0001", number="123456"):
    return client.post(
        "/api/accounts", json={"customer_id": customer_id, "agency": agency, "number": number}
    )


def test_create_and_get_account(client):
    customer = _create_customer(client)

    response = _create_account(client, customer["id"])
    assert response.status_code == 201
    assert response.json()["balance_cents"] == 0
    account_id = response.json()["id"]

    response = client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 200


def test_create_account_missing_customer_returns_404(client):
    response = _create_account(client, customer_id=999)
    assert response.status_code == 404


def test_create_account_duplicate_number_returns_409(client):
    customer = _create_customer(client)
    _create_account(client, customer["id"], number="123456")

    response = _create_account(client, customer["id"], agency="0002", number="123456")
    assert response.status_code == 409


def test_update_account_rejects_balance_field(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.put(f"/api/accounts/{account['id']}", json={"balance_cents": 999999})
    assert response.status_code == 422


def test_update_account_agency_and_label(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.put(
        f"/api/accounts/{account['id']}", json={"agency": "0002", "label": "Conta principal"}
    )
    assert response.status_code == 200
    assert response.json()["label"] == "Conta principal"


def test_delete_account_without_dependencies(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.delete(f"/api/accounts/{account['id']}")
    assert response.status_code == 204


def test_list_customer_accounts(client):
    customer = _create_customer(client)
    _create_account(client, customer["id"])

    response = client.get(f"/api/customers/{customer['id']}/accounts")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_customer_with_accounts_returns_409(client):
    customer = _create_customer(client)
    _create_account(client, customer["id"])

    response = client.delete(f"/api/customers/{customer['id']}")
    assert response.status_code == 409


def test_get_account_balance(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.get(f"/api/accounts/{account['id']}/balance")
    assert response.status_code == 200
    assert response.json()["balance_cents"] == 0


def test_deposit_success(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.post(f"/api/accounts/{account['id']}/deposit", json={"amount_cents": 1000})
    assert response.status_code == 201
    assert response.json()["type"] == "DEPOSIT"

    balance = client.get(f"/api/accounts/{account['id']}/balance").json()
    assert balance["balance_cents"] == 1000


def test_deposit_invalid_amount_returns_400(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.post(f"/api/accounts/{account['id']}/deposit", json={"amount_cents": 0})
    assert response.status_code == 400


def test_withdraw_success(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()
    client.post(f"/api/accounts/{account['id']}/deposit", json={"amount_cents": 1000})

    response = client.post(f"/api/accounts/{account['id']}/withdraw", json={"amount_cents": 400})
    assert response.status_code == 201
    assert response.json()["type"] == "WITHDRAW"

    balance = client.get(f"/api/accounts/{account['id']}/balance").json()
    assert balance["balance_cents"] == 600


def test_withdraw_insufficient_balance_returns_400(client):
    customer = _create_customer(client)
    account = _create_account(client, customer["id"]).json()

    response = client.post(f"/api/accounts/{account['id']}/withdraw", json={"amount_cents": 100})
    assert response.status_code == 400
