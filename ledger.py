import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
try:
    from .db import execute_insert, execute_query, get_db_connection, execute_many_atomic
except ImportError:
    # Para execução direta do módulo (testes)
    import db
    execute_insert = db.execute_insert
    execute_query = db.execute_query
    get_db_connection = db.get_db_connection

DATE_FORMAT = "%Y-%m-%d"

def add_transaction(
    date: str,
    amount: float,
    transaction_type: str,
    account_id: int,
    category: Optional[str] = None,
    description: Optional[str] = None,
    method: Optional[str] = None
) -> int:
    """
    Adiciona uma nova transação ao ledger.
    
    Args:
        date: Data da transação (YYYY-MM-DD).
        amount: Valor da transação (sempre positivo).
        transaction_type: Tipo ('income', 'expense', 'transfer').
        account_id: ID da conta afetada.
        category: Categoria da transação (opcional).
        description: Descrição detalhada (opcional).
        method: Método de pagamento/recebimento (opcional).
        
    Returns:
        O ID da transação inserida.
    """
    query = """
        INSERT INTO transactions 
        (date, amount, transaction_type, account_id, category, description, method) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (date, amount, transaction_type, account_id, category, description, method)
    return execute_insert(query, params)

def list_transactions(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Lista transações com base em filtros.
    
    Args:
        filters: Dicionário de filtros (e.g., {'account_id': 1, 'transaction_type': 'expense'}).
        
    Returns:
        Lista de transações como dicionários.
    """
    base_query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    for key, value in filters.items():
        if value is not None:
            base_query += f" AND {key} = ?"
            params.append(value)
            
    base_query += " ORDER BY date DESC, id DESC"
    
    results = execute_query(base_query, tuple(params))
    return [dict(row) for row in results]

def get_account_balance(account_id: int, until_date: Optional[str] = None) -> float:
    """
    Calcula o saldo computado de uma conta até uma data específica.
    
    Args:
        account_id: ID da conta.
        until_date: Data limite (YYYY-MM-DD). Se None, usa a data atual.
        
    Returns:
        O saldo computado da conta.
    """
    
    # 1. Obter o saldo inicial da conta (assumindo que o saldo inicial é 0 para o MVP)
    # No modelo de dados atual, não temos um campo de saldo inicial na tabela accounts.
    # Para o MVP, vamos assumir que o saldo inicial é 0.
    # Em uma versão futura, o saldo inicial deve ser obtido da tabela accounts.
    initial_balance = 0.0
    
    # 2. Construir a query para somar as transações
    query = """
        SELECT 
            SUM(CASE 
                WHEN transaction_type = 'income' THEN amount 
                WHEN transaction_type = 'expense' THEN -amount 
                WHEN transaction_type = 'transfer' THEN 
                    CASE 
                        WHEN t1.account_id = ? THEN -amount -- Saída da conta
                        ELSE amount -- Entrada na conta (requer lógica de transferências mais complexa, mas para o MVP, assumimos que 'transfer' é a saída e a entrada é outra transação)
                    END
                ELSE 0 
            END) AS net_change
        FROM transactions t1
        WHERE t1.account_id = ?
    """
    params = [account_id, account_id]
    
    if until_date:
        query += " AND date <= ?"
        params.append(until_date)
        
    # NOTA SOBRE TRANSFERÊNCIAS:
    # O modelo de dados atual (transactions) não suporta transferências de forma nativa (uma transação afeta duas contas).
    # Para o MVP, a função add_transaction deve ser chamada DUAS VEZES para uma transferência:
    # 1. add_transaction(..., transaction_type='transfer', account_id=ORIGEM, amount=X)
    # 2. add_transaction(..., transaction_type='income', account_id=DESTINO, amount=X)
    # A lógica abaixo assume que 'transfer' é uma SAÍDA da conta, e a ENTRADA na outra conta é um 'income'.
    # Isso simplifica o cálculo do saldo por conta.
    
    # INVARIANTE DO CAIXA:
    # O saldo da conta é calculado como: income - expense.
    # Transferências alteram saldos individuais, mas NÃO devem alterar o total de caixa.
    # O total de caixa é a soma dos saldos de todas as contas.
    # A função get_account_balance já implementa essa lógica.
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    result = cursor.fetchone()
    conn.close()
    
    net_change = result['net_change'] if result and result['net_change'] is not None else 0.0
    
    return initial_balance + net_change

def add_transfer(
    date: str,
    from_account_id: int,
    to_account_id: int,
    amount: float,
    description: Optional[str] = None,
    method: Optional[str] = None
) -> None:
    """
    Cria uma transferência atômica entre duas contas.
    
    Regra: A transferência é composta por duas transações:
    1. expense na conta de origem (from_account_id)
    2. income na conta de destino (to_account_id)
    
    Esta abordagem garante que a transferência:
    - Altere saldos individuais (corretamente).
    - NÃO altere o total de caixa (income e expense se anulam no total).
    - Seja atômica (ou as duas transações são salvas, ou nenhuma é).
    
    Args:
        date: Data da transferência (YYYY-MM-DD).
        from_account_id: ID da conta de origem.
        to_account_id: ID da conta de destino.
        amount: Valor da transferência (sempre positivo).
        description: Descrição detalhada (opcional).
        method: Método da transferência (opcional).
    """
    
    transfer_description = f"Transferência para {to_account_id}: {description or ''}"
    
    # Transação de Saída (Expense)
    expense_query = """
        INSERT INTO transactions 
        (date, amount, transaction_type, account_id, category, description, method) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    expense_params = (date, amount, 'expense', from_account_id, 'Transferência', transfer_description, method)
    
    # Transação de Entrada (Income)
    income_query = """
        INSERT INTO transactions 
        (date, amount, transaction_type, account_id, category, description, method) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    income_params = (date, amount, 'income', to_account_id, 'Transferência', transfer_description, method)
    
    # Execução atômica
    execute_many_atomic([
        (expense_query, expense_params),
        (income_query, income_params)
    ])

# Exemplo de uso:
if __name__ == '__main__':
    # Importar db para garantir que o banco esteja inicializado
    import db
    initialize_db = db.initialize_db
    execute_query = db.execute_query
    execute_insert = db.execute_insert
    initialize_db()
    
    # Assumindo que a conta 1 (operacional PF) já existe do db.py
    ACCOUNT_ID = 1
    
    # 1. Adicionar transações
    print("Adicionando transações...")
    add_transaction("2026-01-19", 500.00, "income", ACCOUNT_ID, "Salário", "Salário da semana")
    add_transaction("2026-01-20", 50.00, "expense", ACCOUNT_ID, "Alimentação", "Almoço no restaurante", "cartao")
    add_transaction("2026-01-21", 100.00, "expense", ACCOUNT_ID, "Transporte", "Gasolina", "debito")
    
    # Adicionar transferência atômica
    COFRE_ACCOUNT_ID = execute_insert(
        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
        ("Conta Cofre", "PF", "cofre", 1)
    )
    add_transfer("2026-01-22", ACCOUNT_ID, COFRE_ACCOUNT_ID, 200.00, "Transferência para cofre", "PIX")
    
    # 2. Listar transações
    print("\nTransações de despesa:")
    expenses = list_transactions({'account_id': ACCOUNT_ID, 'transaction_type': 'expense'})
    for exp in expenses:
        print(f"  {exp['date']} - {exp['description']}: -{exp['amount']:.2f}")
        
    # 3. Calcular saldo
    balance_today = get_account_balance(ACCOUNT_ID)
    print(f"\nSaldo computado (até hoje): R$ {balance_today:.2f}") # Deve ser 500 - 50 - 100 - 200 = 150.00
    
    balance_until_20 = get_account_balance(ACCOUNT_ID, until_date="2026-01-20")
    print(f"Saldo computado (até 2026-01-20): R$ {balance_until_20:.2f}") # Deve ser 500 - 50 = 450.00
