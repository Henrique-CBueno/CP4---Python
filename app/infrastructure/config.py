import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "bank.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Chave usada para assinar o cookie de sessão.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
