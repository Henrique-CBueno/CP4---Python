"""Script Playwright que simula uma interação completa com o Banco Digital
Acadêmico, pela interface web (não pela API direto): admin cadastra dois
clientes e abre uma conta para cada um, deposita na conta de um deles,
cadastra para o outro uma chave Pix do tipo RANDOM (valor gerado
automaticamente pelo navegador), o primeiro cliente loga e opera a própria
conta (depósito, saque, transferência Pix) e o extrato reflete tudo — com
verificações de autorização (cliente não vê o link "Clientes", só vê a
própria conta) no meio do caminho.

Sobe uma instância isolada da aplicação (banco SQLite temporário, porta
própria) para nunca tocar no bank.db real usado em desenvolvimento.

Uso:
    python -m scripts.e2e_demo             # headless
    python -m scripts.e2e_demo --headed    # abre o navegador visível
    python -m scripts.e2e_demo --keep-db   # mantém o banco temporário ao final

Requer os browsers do Playwright instalados uma vez: `playwright install chromium`.
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

from tests.helpers import generate_valid_cpf

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "playwright-artifacts"
PORT = 8055
BASE_URL = f"http://127.0.0.1:{PORT}"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

MARIA_CPF = generate_valid_cpf("111444777")
JOAO_CPF = generate_valid_cpf("222555888")


def step(message: str) -> None:
    print(f"\n=== {message} ===")


def format_cents_brl(cents: int) -> str:
    """Formata centavos como 'R$ X,XX' (sem separador de milhar — suficiente
    para os valores pequenos usados nesta simulação)."""
    return f"R$ {cents // 100},{cents % 100:02d}"


def wait_for_server(url: str, log_path: Path, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{url}/health", timeout=1)
            return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.3)
    raise RuntimeError(
        f"servidor não respondeu em {url} após {timeout}s. Log:\n{log_path.read_text()}"
    )


def start_server(db_path: Path, log_path: Path) -> subprocess.Popen:
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "APP_PORT": str(PORT),
        "APP_RELOAD": "false",
    }
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            [sys.executable, "-m", "app.main"],
            cwd=BASE_DIR,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    wait_for_server(BASE_URL, log_path)
    return process


def stop_server(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def login(page: Page, email: str, password: str) -> None:
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")


def logout(page: Page) -> None:
    page.click("#logout-button")
    page.wait_for_url(f"{BASE_URL}/login")


def create_customer(page: Page, name: str, email: str, cpf: str, password: str) -> str:
    page.goto(f"{BASE_URL}/customers")
    form = page.locator("#customer-form")
    form.locator('input[name="name"]').fill(name)
    form.locator('input[name="email"]').fill(email)
    form.locator('input[name="cpf"]').fill(cpf)
    form.locator('input[name="password"]').fill(password)
    form.locator('button[type="submit"]').click()

    row = page.locator(f'#customers-list tr:has(td:text-is("{email}"))')
    expect(row).to_be_visible()
    return row.locator("td").first.inner_text().strip()


def create_account(page: Page, customer_id: str, agency: str, number: str) -> str:
    page.goto(f"{BASE_URL}/accounts")
    form = page.locator("#account-form")
    form.locator('select[name="customer_id"]').select_option(customer_id)
    form.locator('input[name="agency"]').fill(agency)
    form.locator('input[name="number"]').fill(number)
    form.locator('button[type="submit"]').click()

    row = page.locator(f'#accounts-list tr:has(td:text-is("{number}"))')
    expect(row).to_be_visible()
    href = row.locator("a").first.get_attribute("href")
    assert href is not None
    return href.rsplit("/", 1)[-1]


def deposit(page: Page, account_id: str, amount_reais: str, expected_cents: int) -> None:
    page.goto(f"{BASE_URL}/accounts/{account_id}")
    page.locator("#deposit-form input[name='amount']").fill(amount_reais)
    page.locator("#deposit-form button[type='submit']").click()
    expect(page.locator("#account-info")).to_contain_text(format_cents_brl(expected_cents))


def withdraw(page: Page, account_id: str, amount_reais: str, expected_cents: int) -> None:
    page.goto(f"{BASE_URL}/accounts/{account_id}")
    page.locator("#withdraw-form input[name='amount']").fill(amount_reais)
    page.locator("#withdraw-form button[type='submit']").click()
    expect(page.locator("#account-info")).to_contain_text(format_cents_brl(expected_cents))


def register_random_pix_key(page: Page, account_id: str) -> str:
    page.goto(f"{BASE_URL}/accounts/{account_id}")
    form = page.locator("#pix-key-form")
    form.locator('select[name="type"]').select_option("RANDOM")
    value_input = form.locator('input[name="value"]')
    generated_value = value_input.input_value()
    assert generated_value, "o valor da chave RANDOM não foi gerado automaticamente"
    form.locator('button[type="submit"]').click()

    row = page.locator(f'#pix-keys-list tr:has(td:text-is("{generated_value}"))')
    expect(row).to_be_visible()
    return generated_value


def transfer_pix(page: Page, source_account_id: str, pix_key_value: str, amount_reais: str) -> None:
    page.goto(f"{BASE_URL}/pix/transfer")
    form = page.locator("#pix-transfer-form")
    form.locator('select[name="source_account_id"]').select_option(source_account_id)
    form.locator('input[name="pix_key_value"]').fill(pix_key_value)
    form.locator('input[name="amount"]').fill(amount_reais)
    form.locator('button[type="submit"]').click()
    expect(page.locator("#pix-transfer-success")).to_be_visible()


def snap(page: Page, name: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ARTIFACTS_DIR / name), full_page=True)


def run(headed: bool) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page()

        step("Login como admin")
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        snap(page, "01-admin-dashboard.png")

        step("Admin cadastra dois clientes")
        maria_id = create_customer(page, "Maria Silva", "maria@example.com", MARIA_CPF, "senha123")
        joao_id = create_customer(page, "João Pereira", "joao@example.com", JOAO_CPF, "senha123")

        step("Admin abre uma conta para cada cliente")
        maria_account_id = create_account(page, maria_id, "0001", "100001")
        joao_account_id = create_account(page, joao_id, "0001", "100002")

        step("Admin deposita R$ 200,00 na conta da Maria")
        deposit(page, maria_account_id, "200.00", 20000)

        step("Admin cadastra uma chave Pix RANDOM para o João (valor gerado automaticamente)")
        joao_pix_key = register_random_pix_key(page, joao_account_id)
        print(f"chave gerada: {joao_pix_key}")

        step("Admin desloga")
        logout(page)

        step("Maria loga na própria conta")
        login(page, "maria@example.com", "senha123")
        snap(page, "02-maria-dashboard.png")

        step('Maria não vê o link "Clientes" (admin-only) nem contas de outros clientes')
        expect(page.locator('a[href="/customers"]')).to_be_hidden()
        page.goto(f"{BASE_URL}/accounts")
        expect(page.locator("#accounts-list tr")).to_have_count(1)

        step("Maria deposita R$ 50,00 na própria conta")
        deposit(page, maria_account_id, "50.00", 25000)

        step("Maria saca R$ 30,00")
        withdraw(page, maria_account_id, "30.00", 22000)

        step("Maria transfere R$ 100,00 via Pix para o João")
        transfer_pix(page, maria_account_id, joao_pix_key, "100.00")
        snap(page, "03-pix-transfer-success.png")

        page.goto(f"{BASE_URL}/accounts/{maria_account_id}")
        expect(page.locator("#account-info")).to_contain_text(format_cents_brl(12000))

        step("Extrato da Maria mostra depósito, saque e transferência")
        statement_text = page.locator("#statement-list").inner_text()
        assert "DEPOSIT" in statement_text
        assert "WITHDRAW" in statement_text
        assert "PIX_TRANSFER" in statement_text

        step("Maria desloga")
        logout(page)

        step("Admin confirma que o João recebeu a transferência")
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        page.goto(f"{BASE_URL}/accounts/{joao_account_id}")
        expect(page.locator("#account-info")).to_contain_text(format_cents_brl(10000))
        snap(page, "04-joao-saldo-final.png")

        browser.close()

    print(f"\nScreenshots salvas em {ARTIFACTS_DIR}/")
    print("\nInteração completa simulada com sucesso — tudo bateu com o esperado.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="abre um navegador visível")
    parser.add_argument(
        "--keep-db", action="store_true", help="mantém o banco temporário em playwright-artifacts/"
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "e2e.db"
        log_path = Path(tmp_dir) / "server.log"

        step(f"Subindo instância isolada em {BASE_URL} (banco: {db_path})")
        server = start_server(db_path, log_path)
        try:
            run(headed=args.headed)
        finally:
            stop_server(server)
            if args.keep_db:
                ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
                kept_path = ARTIFACTS_DIR / "e2e.db"
                kept_path.write_bytes(db_path.read_bytes())
                print(f"\nBanco temporário mantido em {kept_path}")


if __name__ == "__main__":
    main()
