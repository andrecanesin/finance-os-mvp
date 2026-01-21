from typing import List, Dict, Any
from datetime import datetime, timedelta
# Tenta importar para testes diretos e para uso como módulo
try:
    from .db import execute_query
except ImportError:
    import db
    execute_query = db.execute_query

DATE_FORMAT = "%Y-%m-%d"

def list_active_fixed() -> List[Dict[str, Any]]:
    """
    Lista todos os itens de despesas fixas planejadas que estão ativos.
    
    Returns:
        Lista de itens fixos planejados como dicionários.
    """
    query = "SELECT * FROM planned_fixed WHERE active = 1"
    results = execute_query(query)
    return [dict(row) for row in results]

def generate_fixed_events(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Converte registros de planned_fixed em eventos reais com datas concretas
    dentro de um período.
    
    Args:
        start_date: Data de início do período (YYYY-MM-DD).
        end_date: Data de fim do período (YYYY-MM-DD).
        
    Returns:
        Lista de eventos fixos com a data de vencimento real.
    """
    fixed_items = list_active_fixed()
    fixed_events = []
    
    start_obj = datetime.strptime(start_date, DATE_FORMAT).date()
    end_obj = datetime.strptime(end_date, DATE_FORMAT).date()
    
    # Iterar sobre o período mês a mês
    current_date = start_obj
    while current_date <= end_obj:
        for item in fixed_items:
            due_day = item['due_day']
            
            # Tenta criar a data de vencimento no mês atual
            try:
                due_date = current_date.replace(day=due_day)
            except ValueError:
                # Lida com meses que não têm o dia (ex: Fevereiro 30)
                # Neste caso, o vencimento é no último dia do mês
                due_date = current_date.replace(day=1) + timedelta(days=32)
                due_date = due_date.replace(day=1) - timedelta(days=1)
            
            # Verifica se a data de vencimento está dentro do período desejado
            if start_obj <= due_date <= end_obj:
                event = item.copy()
                event['due_date'] = due_date.strftime(DATE_FORMAT)
                fixed_events.append(event)
                
        # Avança para o próximo mês
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
            
    return fixed_events

def get_fixed_for_period(start_date: str, end_date: str) -> float:
    """
    Calcula o total de despesas fixas planejadas que vencem dentro de um período.
    
    Args:
        start_date: Data de início do período (YYYY-MM-DD).
        end_date: Data de fim do período (YYYY-MM-DD).
        
    Returns:
        O total de despesas fixas planejadas no período.
    """
    
    # Para o MVP, assumimos frequência 'monthly' e o due_day é o dia de vencimento.
    # O cálculo é feito iterando sobre os dias do período e verificando se o due_day
    # de algum item fixo cai nesse dia.
    
    fixed_items = list_active_fixed()
    total_fixed = 0.0
    
    start_obj = datetime.strptime(start_date, DATE_FORMAT).date()
    end_obj = datetime.strptime(end_date, DATE_FORMAT).date()
    
    # Usar a nova função generate_fixed_events para obter os eventos reais
    fixed_events = generate_fixed_events(start_date, end_date)
    
    # Somar os valores dos eventos
    total_fixed = sum(event['amount'] for event in fixed_events)
    
    return total_fixed

# Exemplo de uso:
if __name__ == '__main__':
    # Importar db para garantir que o banco esteja inicializado e populado
    import db
    db.initialize_db()
    
    # Assumindo que a conta 1 (operacional PF) já existe do db.py
    ACCOUNT_ID = 1
    
    # Limpar fixos anteriores para teste limpo
    conn = db.get_db_connection()
    conn.execute("DELETE FROM planned_fixed")
    conn.commit()
    conn.close()
    
    # Inserir fixos planejados
    db.execute_insert(
        "INSERT INTO planned_fixed (name, amount, frequency, due_day, account_id, category, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Aluguel", 1500.00, "monthly", 5, ACCOUNT_ID, "Moradia", 1)
    )
    db.execute_insert(
        "INSERT INTO planned_fixed (name, amount, frequency, due_day, account_id, category, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Mensalidade Academia", 100.00, "monthly", 20, ACCOUNT_ID, "Saúde", 1)
    )
    
    # 1. Testar list_active_fixed
    active_fixed = list_active_fixed()
    print("Itens fixos ativos:")
    for item in active_fixed:
        print(f"  {item['name']} - R$ {item['amount']:.2f} (Dia {item['due_day']})")
        
    # 2. Testar get_fixed_for_period
    # Período de 1 mês (Janeiro)
    start_date_jan = "2026-01-01"
    end_date_jan = "2026-01-31"
    fixed_jan = get_fixed_for_period(start_date_jan, end_date_jan)
    print(f"\nTotal fixo planejado em Janeiro (2026-01-01 a 2026-01-31): R$ {fixed_jan:.2f}") # Esperado: 1500 + 100 = 1600.00
    
    # Período de 2 meses (Janeiro e Fevereiro)
    start_date_jan = "2026-01-01"
    end_date_feb = "2026-02-28"
    fixed_jan_feb = get_fixed_for_period(start_date_jan, end_date_feb)
    print(f"Total fixo planejado em Jan/Fev (2026-01-01 a 2026-02-28): R$ {fixed_jan_feb:.2f}") # Esperado: 1600 * 2 = 3200.00
