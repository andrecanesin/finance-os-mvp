import os
import sqlite3
from typing import List, Tuple

# Em Streamlit Cloud, /tmp é gravável. Para outros ambientes, você pode sobrescrever via env.
DATABASE_NAME = os.getenv("FINANCEOS_DB_PATH", "/tmp/finance_os.db")


def get_db_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn


def initialize_db() -> None:
    """Cria as tabelas do schema se elas não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de Contas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('PF', 'PJ')),
            role TEXT NOT NULL CHECK(role IN ('operacional', 'cofre')),
            active BOOLEAN NOT NULL DEFAULT 1
        );
    """)

    # Tabela de Transações
    # amount é sempre positivo. transaction_type define se é entrada ou saída.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, -- YYYY-MM-DD
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income', 'expense', 'transfer')),
            account_id INTEGER NOT NULL,
            category TEXT,
            description TEXT,
            method TEXT, -- PIX | boleto | debito | cartao | outro
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
    """)

    # Tabela de Planejamento Fixo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planned_fixed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK(frequency IN ('monthly')),
            due_day INTEGER NOT NULL, -- 1-31
            account_id INTEGER NOT NULL,
            category TEXT,
            active BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
    """)

    # Tabela de Reconciliações (HITL)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL, -- YYYY-MM-DD (Segunda-feira)
            week_end TEXT NOT NULL,   -- YYYY-MM-DD (Domingo)
            account_id INTEGER NOT NULL,
            real_balance REAL NOT NULL,
            computed_balance REAL NOT NULL,
            delta REAL NOT NULL,
            notes TEXT,
            UNIQUE(week_start, account_id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
    """)

    # Tabela de Configurações (chave-valor)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # Defaults (não sobrescreve se já existir)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('weekly_budget', '450');")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('operational_account_id', '');")

    
    conn.commit()
    conn.close()


def execute_query(query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """Executa SELECT e retorna resultados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


def execute_insert(query: str, params: Tuple = ()) -> int:
    """Executa INSERT/UPDATE/DELETE e retorna o lastrowid (quando aplicável)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_row_id = cursor.lastrowid
    conn.close()
    return last_row_id


def execute_many_atomic(queries_params: List[Tuple[str, Tuple]]) -> None:
    """
    Executa múltiplas queries em uma única transação (atômica).
    Se qualquer query falhar, todas são revertidas (rollback).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for query, params in queries_params:
            cursor.execute(query, params)
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()
