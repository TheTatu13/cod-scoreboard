"""Conexiunea la MySQL, configurată din variabile de mediu (vezi .env.example)."""

import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Deschide o conexiune nouă. Apelantul o închide cu `conn.close()`."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_HOST_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_ROOT_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cod_scoreboard"),
        charset="utf8mb4",
    )
