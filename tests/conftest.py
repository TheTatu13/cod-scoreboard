import json
import os
from dataclasses import dataclass
from uuid import uuid4

import mysql.connector
import pytest

from cod.db import get_connection, get_pg_connection


@pytest.fixture
def db():
    """Conexiune la baza locală. Dacă MySQL nu rulează, testele care o cer sunt sărite."""
    try:
        conn = get_connection()
    except mysql.connector.Error as exc:
        pytest.skip(f"MySQL indisponibil: {exc}")
    try:
        yield conn
    finally:
        conn.close()


@dataclass
class PgTest:
    conn: object
    schema: str


@pytest.fixture
def pg():
    """PostgreSQL cu o schemă temporară, proprie fiecărui test; o șterge la final.

    Testele nu ating schema `raw` adevărată. Fără PostgreSQL pornit, testele sunt sărite.
    """
    import psycopg

    schema = f"raw_test_{os.getpid()}_{uuid4().hex[:8]}"
    try:
        conn = get_pg_connection(schema)
    except psycopg.Error as exc:
        pytest.skip(f"PostgreSQL indisponibil: {exc}")
    from cod.ingest import loaders

    loaders.ensure_schema(conn)
    try:
        yield PgTest(conn, schema)
    finally:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        conn.commit()
        conn.close()


@pytest.fixture(scope="session")
def feed(tmp_path_factory):
    """Feed-ul JSON cu defecte (seed 42), generat o dată pe sesiune din datele din MySQL."""
    try:
        conn = get_connection()
    except mysql.connector.Error as exc:
        pytest.skip(f"MySQL indisponibil: {exc}")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM kill_table")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    if n == 0:
        pytest.skip("Baza e goală: rulează `python -m cod.generator --seed 42 --reset`")
    from cod.generator import events

    out = tmp_path_factory.mktemp("feed") / "events"
    events.main(["--seed", "42", "--out", str(out)])
    manifest = json.loads((out / "_manifest.json").read_text(encoding="utf-8"))
    return out, manifest
