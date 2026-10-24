from cod import db


def test_db_module_exposes_get_connection():
    assert callable(db.get_connection)
