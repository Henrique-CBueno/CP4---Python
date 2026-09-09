import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "bank.db"
# Permite apontar para outro banco (ex.: um arquivo temporário usado por um
# script de demonstração/E2E) sem tocar no bank.db real do projeto.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Chave usada para assinar o cookie de sessão.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
