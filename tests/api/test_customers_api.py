from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")
OTHER_VALID_CPF = generate_valid_cpf("111444777")


def _create_customer(client, name="Maria Silva", email="maria@example.com", cpf=VALID_CPF):
    return client.post("/api/customers", json={"name": name, "email": email, "cpf": cpf})


def test_create_and_get_customer(client):
    response = _create_customer(client)
    assert response.status_code == 201
    customer_id = response.json()["id"]

    response = client.get(f"/api/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "maria@example.com"


def test_list_customers(client):
    _create_customer(client)

    response = client.get("/api/customers")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_customer_duplicate_email_returns_409(client):
    _create_customer(client, email="dup@example.com", cpf=VALID_CPF)

    response = _create_customer(client, email="dup@example.com", cpf=OTHER_VALID_CPF)
    assert response.status_code == 409


def test_create_customer_invalid_cpf_returns_422(client):
    response = _create_customer(client, cpf="12345678900")
    assert response.status_code == 422


def test_update_customer(client):
    created = _create_customer(client).json()

    response = client.put(f"/api/customers/{created['id']}", json={"name": "Maria S."})
    assert response.status_code == 200
    assert response.json()["name"] == "Maria S."


def test_update_customer_rejects_unknown_fields(client):
    created = _create_customer(client).json()

    response = client.put(f"/api/customers/{created['id']}", json={"cpf": "00000000000"})
    assert response.status_code == 422


def test_delete_customer(client):
    created = _create_customer(client).json()

    response = client.delete(f"/api/customers/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/customers/{created['id']}")
    assert response.status_code == 404


def test_get_missing_customer_returns_404(client):
    response = client.get("/api/customers/999")
    assert response.status_code == 404
