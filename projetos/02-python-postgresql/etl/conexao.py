"""
BanVic 360 -- Projeto 2 -- Modulo de Conexao
Gerencia conexoes psycopg2 (transacoes) e SQLAlchemy (pandas I/O).
"""
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Busca .env subindo nos diretorios a partir deste arquivo
for _p in Path(__file__).resolve().parents:
    if (_p / ".env").exists():
        load_dotenv(_p / ".env")
        break

PG_CONN = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB", "banvic"),
    "user":     os.getenv("PG_USER", "banvic_user"),
    "password": os.getenv("PG_PASSWORD", "banvic_pass"),
}


def get_engine():
    u = PG_CONN
    url = (
        f"postgresql+psycopg2://{u['user']}:{u['password']}"
        f"@{u['host']}:{u['port']}/{u['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


@contextmanager
def get_conn():
    conn = psycopg2.connect(**PG_CONN, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def executar(sql: str, engine):
    with engine.begin() as conn:
        conn.execute(text(sql))


def truncar(tabela: str, engine, cascade: bool = False):
    suffix = " CASCADE" if cascade else ""
    executar(f"TRUNCATE {tabela}{suffix}", engine)
