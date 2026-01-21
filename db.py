import os
import sqlite3
from typing import List, Tuple

# Em Streamlit Cloud, /tmp é gravável. Para outros ambientes, você pode sobrescrever via env.
DATABASE_NAME = os.getenv("FINANCEOS_DB_PATH", "/tmp/finance_os.db")

def get_db_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

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
            account_id INTEGER NOT NULL,
            real_balance REAL NOT NULL,
            computed_balance REAL NOT NULL,
            delta REAL NOT NULL,
            notes TEXT,
            UNIQUE(week_start, account_id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
    """)

    conn.commit()
    conn.close()

def execute_query(query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """Função utilitária para executar consultas e retornar resultados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_insert(query: str, params: Tuple = ()) -> int:
    """Função utilitária para executar inserções e retornar o ID da última linha."""
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
    
    Args:
        queries_params: Lista de tuplas (query_string, parameters_tuple).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for query, params in queries_params:
            cursor.execute(query, params)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erro na transação atômica: {e}")
        raise
    finally:
        conn.close()

# Exemplo de uso:
if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    initialize_db()
    print(f"Banco de dados criado em: {DATABASE_NAME}")

    # Exemplo de inserção de conta
    account_id = execute_insert(
        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
        ("Conta Operacional PF", "PF", "operacional", 1)
    )
    print(f"Conta inserida com ID: {account_id}")

    # Exemplo de consulta
    accounts = execute_query("SELECT * FROM accounts")
    print("\nContas no banco:")
    for account in accounts:
        print(f"ID: {account['id']}, Nome: {account['name']}, Tipo: {account['type']}, Papel: {account['role']}")

    # Exemplo de inserção de transação
    transaction_id = execute_insert(
        "INSERT INTO transactions (date, amount, transaction_type, account_id, category, description, method) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("2026-01-20", 1500.00, "income", account_id, "Salário", "Pagamento Mensal", "PIX")
    )
    print(f"\nTransação inserida com ID: {transaction_id}")

    # Exemplo de inserção de fixo planejado
    planned_id = execute_insert(
        "INSERT INTO planned_fixed (name, amount, frequency, due_day, account_id, category, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Aluguel", 800.00, "monthly", 5, account_id, "Moradia", 1)
    )
    print(f"Fixo planejado inserido com ID: {planned_id}")

    # Exemplo de inserção de reconciliação
    reconciliation_id = execute_insert(
        "INSERT INTO reconciliations (week_start, account_id, real_balance, computed_balance, delta, notes) VALUES (?, ?, ?, ?, ?, ?)",
        ("2026-01-19", account_id, 1000.00, 950.00, 50.00, "Diferença de 50.00 a investigar.")
    )
    print(f"Reconciliação inserida com ID: {reconciliation_id}")
