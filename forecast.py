from typing import Dict
from datetime import datetime, timedelta
# Tenta importar para testes diretos e para uso como módulo
try:
    from .db import execute_query
    from .ledger import get_total_cash
    from .planned import get_fixed_for_period, generate_fixed_events
    from .kpis import get_weekly_variable_expenses
    from .dates import get_week_start, get_week_end
except ImportError:
    import db
    import ledger
    import planned
    import kpis
    import dates
    execute_query = db.execute_query
    get_total_cash = kpis.get_total_cash
    get_fixed_for_period = planned.get_fixed_for_period
    generate_fixed_events = planned.generate_fixed_events
    get_weekly_variable_expenses = kpis.get_weekly_variable_expenses
    get_week_start = dates.get_week_start
    get_week_end = dates.get_week_end

DATE_FORMAT = "%Y-%m-%d"

def get_average_weekly_variable_expenses(num_weeks: int = 4) -> float:
    """
    Calcula a média semanal de despesas variáveis da conta operacional
    nas últimas 'num_weeks' semanas.
    
    Args:
        num_weeks: Número de semanas para calcular a média.
        
    Returns:
        A média semanal de despesas variáveis (valor positivo).
    """
    
    # 1. Encontrar a conta operacional
    query = "SELECT id FROM accounts WHERE role = 'operacional' AND active = 1"
    result = execute_query(query)
    if not result:
        return 0.0
    operational_account_id = result[0]['id']
    
    # 2. Iterar pelas últimas 'num_weeks'
    today = datetime.now().date()
    total_expenses = 0.0
    
    for i in range(num_weeks):
        # Encontrar a data de início da semana 'i' semanas atrás
        # Começa na semana atual (i=0) e vai para trás
        
        # Encontra uma data dentro da semana 'i' semanas atrás
        date_in_week = today - timedelta(weeks=i)
        week_start = get_week_start(date_in_week.strftime(DATE_FORMAT))
        
        # Calcula as despesas variáveis dessa semana
        weekly_expenses = get_weekly_variable_expenses(week_start, operational_account_id)
        total_expenses += weekly_expenses
        
    # 3. Calcular a média
    if num_weeks > 0:
        return total_expenses / num_weeks
    return 0.0

def forecast_cash_flow(days: int = 30) -> Dict[str, float]:
    """
    Calcula a previsão de fluxo de caixa para os próximos 'days' dias.
    
    Regra: Saldo Atual - Fixos Planejados - Média Semanal de Variáveis (últimas 4 semanas) * (dias / 7)
    
    Args:
        days: Número de dias para a previsão.
        
    Returns:
        Dicionário com o saldo atual e o saldo previsto.
    """
    
    # 1. Saldo Atual
    current_cash = get_total_cash()
    
    # 2. Fixos Planejados
    start_date = datetime.now().strftime(DATE_FORMAT)
    end_date = (datetime.now() + timedelta(days=days)).strftime(DATE_FORMAT)
    planned_fixed_expenses = get_fixed_for_period(start_date, end_date)
    
    # 3. Média Semanal de Variáveis
    avg_weekly_variable_expenses = get_average_weekly_variable_expenses(num_weeks=4)
    
    # 4. Projeção de Variáveis
    num_weeks_in_period = days / 7.0
    projected_variable_expenses = avg_weekly_variable_expenses * num_weeks_in_period
    
    # 5. Saldo Previsto
    forecasted_cash = current_cash - planned_fixed_expenses - projected_variable_expenses
    
    return {
        "current_cash": current_cash,
        "planned_fixed_expenses": planned_fixed_expenses,
        "projected_variable_expenses": projected_variable_expenses,
        "forecasted_cash": forecasted_cash
    }

# Exemplo de uso:
if __name__ == '__main__':
    # Importar db para garantir que o banco esteja inicializado e populado
    import db
    import ledger
    import planned
    import kpis
    db.initialize_db()
    
    # Garantir que a conta operacional exista
    query = "SELECT id FROM accounts WHERE role = 'operacional' AND active = 1"
    result = db.execute_query(query)
    if not result:
        OPERATIONAL_ACCOUNT_ID = db.execute_insert(
            "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
            ("Conta Operacional PF", "PF", "operacional", 1)
        )
    else:
        OPERATIONAL_ACCOUNT_ID = result[0]['id']
        
    # Garantir que existam dados de 4 semanas para a média
    # Simulação de 4 semanas de despesas variáveis de R$ 150.00
    today = datetime.now().date()
    for i in range(4):
        date_in_week = today - timedelta(weeks=i)
        week_start = get_week_start(date_in_week.strftime(DATE_FORMAT))
        
        # Adicionar uma despesa de R$ 150.00 em cada uma das 4 semanas
        ledger.add_transaction(week_start, 150.00, "expense", OPERATIONAL_ACCOUNT_ID, "Simulação", f"Despesa Semanal {i+1}")
        
    # Garantir que existam fixos planejados (do teste do planned.py)
    # Total fixo em 30 dias: R$ 1600.00 (Aluguel + Academia)
    
    # Garantir que o saldo atual seja conhecido (do teste do kpis.py)
    # Saldo total: R$ 800.00
    
    # 1. Testar get_average_weekly_variable_expenses
    avg_expenses = get_average_weekly_variable_expenses(num_weeks=4)
    print(f"Média semanal de despesas variáveis (últimas 4 semanas): R$ {avg_expenses:.2f}") # Esperado: 150.00
    
    # 2. Testar forecast_cash_flow (30 dias)
    forecast = forecast_cash_flow(days=30)
    
    # Cálculo esperado:
    # Saldo Atual: 800.00
    # Fixos (30 dias): 1600.00
    # Variáveis (30 dias): 150.00 * (30 / 7) = 642.86
    # Forecast: 800.00 - 1600.00 - 642.86 = -1442.86
    
    print("\nPrevisão de Fluxo de Caixa (30 dias):")
    print(f"  Saldo Atual: R$ {forecast['current_cash']:.2f}")
    print(f"  - Fixos Planejados: R$ {forecast['planned_fixed_expenses']:.2f}")
    print(f"  - Variáveis Projetadas: R$ {forecast['projected_variable_expenses']:.2f}")
    print(f"  = Saldo Previsto: R$ {forecast['forecasted_cash']:.2f}")
