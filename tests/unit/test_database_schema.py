from sqlalchemy import create_engine, inspect

from app.adapters.outbound.persistence import models  # noqa: F401
from app.infrastructure.db import Base


def test_create_all_creates_expected_tables(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")

    Base.metadata.create_all(engine)

    tables = set(inspect(engine).get_table_names())
    assert {"customers", "accounts", "pix_keys", "transactions"} <= tables
