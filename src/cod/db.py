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


def get_pg_connection(schema: str = "raw"):
    """Conexiune la PostgreSQL (warehouse). `schema` devine search_path-ul sesiunii.

    Apelantul o închide cu `conn.close()`. Autocommit e oprit: fiecare unitate de lucru
    face explicit `conn.commit()`, ca o zi să fie încărcată complet sau deloc.
    """
    import psycopg

    conn = psycopg.connect(
        host=os.getenv("PG_HOST", "127.0.0.1"),
        port=int(os.getenv("PG_PORT", "5433")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DATABASE", "cod_warehouse"),
    )
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        cur.execute(f'SET search_path TO "{schema}"')
    conn.commit()
    return conn
