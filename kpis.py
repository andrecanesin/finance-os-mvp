from typing import Dict
from datetime import datetime
from dates import get_week_end, get_current_week_range
from ledger import get_account_balance

# Tenta importar para testes diretos e para uso como módulo
try:
    from db import execute_query
    from dates import get_week_end, get_current_week_range
    from ledger import get_account_balance
except ImportError:
    import db
    import dates
    import ledger
    execute_query = db.execute_query
    get_week_end = dates.get_week_end
    get_current_week_range = dates.get_current_week_range
    get_account_balance = ledger.get_account_balance


def get_weekly_variable_expenses(week_start: str, operational_account_id: int) -> float:
    """
    Calcula o total de despesas variáveis (expense, excluindo transferências)
    da conta operacional para a semana definida.
    
    Args:
        week_start: Data de início da semana (Segunda-feira, YYYY-MM-DD).
        operational_account_id: ID da conta operacional.
        
    Returns:
        O total de despesas variáveis na semana (valor positivo).
    """
    week_end = get_week_end(week_start)
    
    # Regra: somar somente 'expense', conta operacional, datas dentro da semana.
    # Transferências são excluídas pelo filtro 'expense'.
    query = """
        SELECT SUM(amount) AS total_expenses
        FROM transactions
        WHERE transaction_type = 'expense'
          AND account_id = ?
          AND date BETWEEN ? AND ?
    """
    params = (operational_account_id, week_start, week_end)
    
    result = execute_query(query, params)
    
    # O resultado é uma lista de tuplas/linhas. Pegamos o primeiro elemento (total_expenses)
    total = result[0]['total_expenses'] if result and result[0]['total_expenses'] is not None else 0.0
    
    return total

def get_current_week_variable_expenses(operational_account_id: int, today: str = None) -> float:
    """
    Calcula o total de despesas variáveis da conta operacional para a semana atual.
    
    Args:
        operational_account_id: ID da conta operacional.
        today: Data de referência (YYYY-MM-DD). Se None, usa a data atual do sistema.
        
    Returns:
        O total de despesas variáveis na semana atual (valor positivo).
    """
    week_start, _ = get_current_week_range(today)
    
    # Regra: A UI futura não deve recalcular semana.
    # Reutiliza a função principal de cálculo semanal
    return get_weekly_variable_expenses(week_start, operational_account_id)

def get_total_cash() -> float:
    """
    Soma os saldos computados de todas as contas ativas.
    
    INVARIANTE DO CAIXA:
    O total de caixa NÃO deve ser alterado por transferências,
    pois estas são tratadas como expense (saída) e income (entrada)
    que se anulam no total.
    
    Returns:
        O saldo total de caixa (cash) do sistema.
    """
    # 1. Obter IDs de todas as contas ativas
    query = "SELECT id FROM accounts WHERE active = 1"
    active_accounts = execute_query(query)
    
    total_cash = 0.0
    
    # 2. Iterar e somar os saldos
    for account in active_accounts:
        account_id = account['id']
        balance = get_account_balance(account_id)
        total_cash += balance
        
    return total_cash

# Exemplo de uso:
if __name__ == '__main__':
    # Importar db para garantir que o banco esteja inicializado e populado
    import db
    import ledger
    db.initialize_db()
    
    # Assumindo que a conta 1 (operacional PF) já existe do db.py
    OPERATIONAL_ACCOUNT_ID = 1
    
    # Adicionar uma segunda conta (cofre)
    COFRE_ACCOUNT_ID = db.execute_insert(
        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
        ("Conta Cofre", "PF", "cofre", 1)
    )
    
    # Adicionar transações para a semana 2026-01-19 a 2026-01-25
    # Limpar transações anteriores para teste limpo
    conn = db.get_db_connection()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    
    # Transações na conta operacional
    ledger.add_transaction("2026-01-19", 1000.00, "income", OPERATIONAL_ACCOUNT_ID, "Salário", "Salário da semana")
    ledger.add_transaction("2026-01-20", 50.00, "expense", OPERATIONAL_ACCOUNT_ID, "Alimentação", "Almoço", "cartao")
    ledger.add_transaction("2026-01-21", 100.00, "expense", OPERATIONAL_ACCOUNT_ID, "Transporte", "Gasolina", "debito")
    
    # Usar a nova função atômica de transferência
    ledger.add_transfer("2026-01-22", OPERATIONAL_ACCOUNT_ID, COFRE_ACCOUNT_ID, 200.00, "Transferência para cofre", "PIX")
    
    # Transação fora da semana (para teste de filtro)
    ledger.add_transaction("2026-01-26", 50.00, "expense", OPERATIONAL_ACCOUNT_ID, "Alimentação", "Almoço na próxima semana", "cartao")
    
    # 1. Testar get_weekly_variable_expenses
    week_start = "2026-01-19"
    weekly_expenses = get_weekly_variable_expenses(week_start, OPERATIONAL_ACCOUNT_ID)
    print(f"Despesas variáveis na semana ({week_start}): R$ {weekly_expenses:.2f}") # Esperado: 50.00 + 100.00 = 150.00
    
    # 2. Testar get_current_week_variable_expenses
    current_weekly_expenses = get_current_week_variable_expenses(OPERATIONAL_ACCOUNT_ID, today="2026-01-21")
    print(f"Despesas variáveis na semana atual (2026-01-21): R$ {current_weekly_expenses:.2f}") # Esperado: 150.00
    
    # 3. Testar get_total_cash (Invariante)
    total_cash = get_total_cash()
    # Saldo Operacional: 1000 (income) - 50 (expense) - 100 (expense) - 200 (expense da transfer) - 50 (expense próxima semana) = 600.00
    # Saldo Cofre: 200 (income da transfer) = 200.00
    # Total: 600.00 + 200.00 = 800.00
    print(f"Saldo total de caixa (Cash - Invariante): R$ {total_cash:.2f}")
