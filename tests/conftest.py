import mysql.connector
import pytest

from cod.db import get_connection


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
