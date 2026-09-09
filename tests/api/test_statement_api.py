from tests.helpers import generate_valid_cpf


def _create_account(client, cpf, email, number):
    customer = client.post(
        "/api/customers", json={"name": "Cliente", "email": email, "cpf": cpf, "password": "Password123"}
    ).json()
    return client.post(
        "/api/accounts", json={"customer_id": customer["id"], "agency": "0001", "number": number}
    ).json()


def test_statement_lists_deposit_and_withdraw(client):
    account = _create_account(client, generate_valid_cpf("529982247"), "maria@example.com", "111111")
    client.post(f"/api/accounts/{account['id']}/deposit", json={"amount_cents": 1000})
    client.post(f"/api/accounts/{account['id']}/withdraw", json={"amount_cents": 300})

    response = client.get(f"/api/accounts/{account['id']}/transactions")
    assert response.status_code == 200
    types = [t["type"] for t in response.json()]
    assert types.count("DEPOSIT") == 1
    assert types.count("WITHDRAW") == 1


def test_statement_of_missing_account_returns_404(client):
    response = client.get("/api/accounts/999/transactions")
    assert response.status_code == 404
