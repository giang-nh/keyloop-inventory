"""The migrations must build the same tables and indexes as the models describe."""

import sqlite3
from contextlib import closing

from alembic import command
from alembic.config import Config

import app.models  # noqa: F401
from app.db import Base


def _upgrade(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")


def test_migrations_create_every_table_and_index_in_the_models(tmp_path):
    db_file = tmp_path / "migrated.db"
    _upgrade(f"sqlite:///{db_file.as_posix()}")

    with closing(sqlite3.connect(db_file)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        indexes = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}

    expected_tables = set(Base.metadata.tables)
    expected_indexes = {ix.name for t in Base.metadata.tables.values() for ix in t.indexes}
    assert expected_tables <= tables
    assert expected_indexes <= indexes


def test_migrated_vin_is_not_unique(tmp_path):
    db_file = tmp_path / "migrated.db"
    _upgrade(f"sqlite:///{db_file.as_posix()}")

    with closing(sqlite3.connect(db_file)) as conn:
        conn.execute("INSERT INTO dealership (id, name, city) VALUES (1, 'D', 'C')")
        for vehicle_id in (1, 2):
            conn.execute(
                "INSERT INTO vehicle (id, vin, dealership_id, make, model, model_year, price)"
                " VALUES (?, 'SAMEVIN0000000001', 1, 'Kia', 'Seltos', 2024, 1)",
                (vehicle_id,),
            )
        count = conn.execute("SELECT count(*) FROM vehicle").fetchone()[0]

    assert count == 2
