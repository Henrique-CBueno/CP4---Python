def test_dashboard_page_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_customers_page_returns_200(client):
    response = client.get("/customers")
    assert response.status_code == 200


def test_accounts_page_returns_200(client):
    response = client.get("/accounts")
    assert response.status_code == 200


def test_account_detail_page_returns_200(client):
    response = client.get("/accounts/1")
    assert response.status_code == 200


def test_pix_transfer_page_returns_200(client):
    response = client.get("/pix/transfer")
    assert response.status_code == 200
