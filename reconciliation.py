from typing import Dict, Any
from datetime import datetime
# Tenta importar para testes diretos e para uso como módulo
try:
    from db import execute_insert, execute_query
    from dates import get_week_start, get_week_end
    from ledger import get_account_balance
except ImportError:
    import db
    import dates
    import ledger
    execute_insert = db.execute_insert
    execute_query = db.execute_query
    get_week_start = dates.get_week_start
    get_account_balance = ledger.get_account_balance

DATE_FORMAT = "%Y-%m-%d"

def reconcile_account(week_start: str, account_id: int, real_balance: float) -> int:
    """
    Registra a reconciliação de uma conta para uma semana específica.
    
    Args:
        week_start: Data de início da semana (Segunda-feira, YYYY-MM-DD).
        account_id: ID da conta a ser reconciliada.
        real_balance: Saldo real (informado pelo usuário/extrato).
        
    Returns:
        O ID da reconciliação inserida.
    """
    
    # O delta é INFORMATIVO e NÃO gera correção automática.
    # O sistema deve funcionar mesmo com delta diferente de zero.
    # Este é o ponto de verdade HUMANO (HITL).
    
    # 1. Calcular o saldo computado do sistema até o final da semana
    # O saldo computado deve ser calculado até o Domingo (final da semana).
    # Como a reconciliação é feita no final da semana, calculamos o saldo
    # até o dia anterior ao início da próxima semana (ou seja, o Domingo).
    
    # Para simplificar o MVP, vamos calcular o saldo até o dia da reconciliação
    # que é o dia que o usuário está executando a função.
    # Em um sistema real, o saldo seria calculado até o final do período reconciliado.
    
    # Vamos usar a data de início da semana para calcular o saldo computado
    # até o dia anterior ao início da semana (para obter o saldo inicial da semana)
    # e depois somar as transações da semana.
    
    # Para o MVP, vamos simplificar e calcular o saldo computado até a data atual.
    # O usuário deve informar o saldo real na data em que a reconciliação é feita.
    
    # Saldo computado é o saldo da conta na data atual.
    computed_balance = get_account_balance(account_id)
    
    # 2. Calcular o delta
    delta = real_balance - computed_balance
    
    # 3. Salvar a reconciliação
    week_end = get_week_end(week_start) # Garante que o week_end seja consistente
    
    query = """
        INSERT INTO reconciliations 
        (week_start, week_end, account_id, real_balance, computed_balance, delta, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(week_start, account_id) DO UPDATE SET
            real_balance = excluded.real_balance,
            computed_balance = excluded.computed_balance,
            delta = excluded.delta,
            notes = excluded.notes
    """
    notes = f"Delta de R$ {delta:.2f} (Real - Computado). Reconciliação para o período {week_start} a {week_end}."
    params = (week_start, week_end, account_id, real_balance, computed_balance, delta, notes)
    
    return execute_insert(query, params)

# Exemplo de uso:
if __name__ == '__main__':
    # Importar db para garantir que o banco esteja inicializado e populado
    import db
    import ledger
    db.initialize_db()
    
    # Assumindo que a conta 1 (operacional PF) já existe do db.py
    ACCOUNT_ID = 1
    
    # 1. Obter o saldo computado atual (do teste do ledger.py)
    # Saldo computado atual: 600.00 (considerando todas as transações)
    computed_balance = ledger.get_account_balance(ACCOUNT_ID)
    print(f"Saldo computado atual: R$ {computed_balance:.2f}")
    
    # 2. Simular reconciliação para a semana de 2026-01-19
    week_start = get_week_start(datetime.now().strftime(DATE_FORMAT)) # Segunda-feira desta semana
    
    # Simular que o saldo real é R$ 650.00 (o sistema errou em R$ 50.00)
    REAL_BALANCE = 650.00
    
    reconciliation_id = reconcile_account(week_start, ACCOUNT_ID, REAL_BALANCE)
    
    # 3. Verificar o resultado
    query = "SELECT * FROM reconciliations WHERE week_start = ? AND account_id = ?"
    result = execute_query(query, (week_start, ACCOUNT_ID))
    
    print(f"\nReconciliação registrada (ID: {result[0]['id']}):")
    print(f"  Semana: {result[0]['week_start']}")
    print(f"  Saldo Real: R$ {result[0]['real_balance']:.2f}")
    print(f"  Saldo Computado: R$ {result[0]['computed_balance']:.2f}")
    print(f"  Delta: R$ {result[0]['delta']:.2f}") # Esperado: 650.00 - 600.00 = 50.00
    print(f"  Notas: {result[0]['notes']}")
