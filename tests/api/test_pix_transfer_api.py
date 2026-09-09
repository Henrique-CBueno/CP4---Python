from tests.helpers import generate_valid_cpf


def _create_account(client, cpf, email, number):
    customer = client.post(
        "/api/customers", json={"name": "Cliente", "email": email, "cpf": cpf}
    ).json()
    return client.post(
        "/api/accounts", json={"customer_id": customer["id"], "agency": "0001", "number": number}
    ).json()


def test_transfer_success(client):
    source = _create_account(client, generate_valid_cpf("529982247"), "source@example.com", "111111")
    destination = _create_account(
        client, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    client.post(
        "/api/pix-keys",
        json={"account_id": destination["id"], "type": "EMAIL", "value": "destination@example.com"},
    )
    client.post(f"/api/accounts/{source['id']}/deposit", json={"amount_cents": 1000})

    response = client.post(
        "/api/pix/transfers",
        json={
            "source_account_id": source["id"],
            "pix_key_value": "destination@example.com",
            "amount_cents": 400,
        },
    )
    assert response.status_code == 201
    assert response.json()["type"] == "PIX_TRANSFER"

    source_balance = client.get(f"/api/accounts/{source['id']}/balance").json()
    destination_balance = client.get(f"/api/accounts/{destination['id']}/balance").json()
    assert source_balance["balance_cents"] == 600
    assert destination_balance["balance_cents"] == 400


def test_transfer_pix_key_not_found_returns_404(client):
    source = _create_account(client, generate_valid_cpf("529982247"), "source@example.com", "111111")
    client.post(f"/api/accounts/{source['id']}/deposit", json={"amount_cents": 1000})

    response = client.post(
        "/api/pix/transfers",
        json={
            "source_account_id": source["id"],
            "pix_key_value": "unknown@example.com",
            "amount_cents": 100,
        },
    )
    assert response.status_code == 404


def test_transfer_insufficient_balance_returns_400(client):
    source = _create_account(client, generate_valid_cpf("529982247"), "source@example.com", "111111")
    destination = _create_account(
        client, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    client.post(
        "/api/pix-keys",
        json={"account_id": destination["id"], "type": "EMAIL", "value": "destination@example.com"},
    )

    response = client.post(
        "/api/pix/transfers",
        json={
            "source_account_id": source["id"],
            "pix_key_value": "destination@example.com",
            "amount_cents": 100,
        },
    )
    assert response.status_code == 400


def test_transfer_to_same_account_returns_400(client):
    source = _create_account(client, generate_valid_cpf("529982247"), "source@example.com", "111111")
    client.post(
        "/api/pix-keys",
        json={"account_id": source["id"], "type": "EMAIL", "value": "source@example.com"},
    )
    client.post(f"/api/accounts/{source['id']}/deposit", json={"amount_cents": 1000})

    response = client.post(
        "/api/pix/transfers",
        json={
            "source_account_id": source["id"],
            "pix_key_value": "source@example.com",
            "amount_cents": 100,
        },
    )
    assert response.status_code == 400


def test_transfer_invalid_amount_returns_400(client):
    source = _create_account(client, generate_valid_cpf("529982247"), "source@example.com", "111111")

    response = client.post(
        "/api/pix/transfers",
        json={"source_account_id": source["id"], "pix_key_value": "x", "amount_cents": 0},
    )
    assert response.status_code == 400
