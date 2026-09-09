from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")


def _create_account(client):
    customer = client.post(
        "/api/customers",
        json={
            "name": "Maria Silva",
            "email": "maria@example.com",
            "cpf": VALID_CPF,
            "password": "Password123",
        },
    ).json()
    return client.post(
        "/api/accounts", json={"customer_id": customer["id"], "agency": "0001", "number": "123456"}
    ).json()


def test_create_and_get_pix_key(client):
    account = _create_account(client)

    response = client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    )
    assert response.status_code == 201
    pix_key_id = response.json()["id"]

    response = client.get(f"/api/pix-keys/{pix_key_id}")
    assert response.status_code == 200


def test_create_pix_key_missing_account_returns_404(client):
    response = client.post(
        "/api/pix-keys", json={"account_id": 999, "type": "EMAIL", "value": "maria@example.com"}
    )
    assert response.status_code == 404


def test_create_pix_key_invalid_format_returns_422(client):
    account = _create_account(client)

    response = client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "not-an-email"},
    )
    assert response.status_code == 422


def test_create_pix_key_duplicate_returns_409(client):
    account = _create_account(client)
    client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    )

    response = client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    )
    assert response.status_code == 409


def test_update_pix_key_rejects_unknown_fields(client):
    account = _create_account(client)
    pix_key = client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    ).json()

    response = client.put(f"/api/pix-keys/{pix_key['id']}", json={"account_id": 999})
    assert response.status_code == 422


def test_delete_pix_key(client):
    account = _create_account(client)
    pix_key = client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    ).json()

    response = client.delete(f"/api/pix-keys/{pix_key['id']}")
    assert response.status_code == 204


def test_list_account_pix_keys(client):
    account = _create_account(client)
    client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    )

    response = client.get(f"/api/accounts/{account['id']}/pix-keys")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_account_with_pix_key_returns_409(client):
    account = _create_account(client)
    client.post(
        "/api/pix-keys",
        json={"account_id": account["id"], "type": "EMAIL", "value": "maria@example.com"},
    )

    response = client.delete(f"/api/accounts/{account['id']}")
    assert response.status_code == 409
