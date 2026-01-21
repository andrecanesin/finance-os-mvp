import db
import ledger
import kpis
import planned
import reconciliation
import forecast
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"

def setup_initial_data():
    """Inicializa o banco de dados e popula com dados básicos para o exemplo."""
    print("--- 1. CONFIGURAÇÃO INICIAL DO BANCO ---")
    db.initialize_db()
    
    # Limpar dados para teste limpo
    conn = db.get_db_connection()
    conn.execute("DELETE FROM transactions")
    conn.execute("DELETE FROM accounts")
    conn.execute("DELETE FROM planned_fixed")
    conn.execute("DELETE FROM reconciliations")
    conn.commit()
    conn.close()
    
    # Criar Contas
    op_id = db.execute_insert(
        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
        ("Conta Operacional PF", "PF", "operacional", 1)
    )
    cofre_id = db.execute_insert(
        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
        ("Conta Cofre PJ", "PJ", "cofre", 1)
    )
    
    # Criar Fixos Planejados (para forecast)
    planned.db.execute_insert(
        "INSERT INTO planned_fixed (name, amount, frequency, due_day, account_id, category, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Aluguel", 1500.00, "monthly", 5, op_id, "Moradia", 1)
    )
    planned.db.execute_insert(
        "INSERT INTO planned_fixed (name, amount, frequency, due_day, account_id, category, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Mensalidade Academia", 100.00, "monthly", 20, op_id, "Saúde", 1)
    )
    
    # Adicionar transações para 4 semanas (para média de variáveis)
    today = datetime.now().date()
    for i in range(4):
        date_in_week = today - timedelta(weeks=i)
        week_start = forecast.dates.get_week_start(date_in_week.strftime(DATE_FORMAT))
        
        # Receita (Income)
        ledger.add_transaction(week_start, 2000.00, "income", op_id, "Salário", f"Salário Semanal {i+1}")
        
        # Despesa Variável (Expense) - R$ 150.00 por semana
        ledger.add_transaction(week_start, 150.00, "expense", op_id, "Alimentação", f"Despesa Variável {i+1}")
        
        # Transferência (para cofre)
        ledger.add_transaction(week_start, 500.00, "transfer", op_id, "Investimento", f"Transferência para Cofre {i+1}")
        ledger.add_transaction(week_start, 500.00, "income", cofre_id, "Investimento", f"Entrada no Cofre {i+1}")
        
    print(f"Contas criadas: Operacional ID {op_id}, Cofre ID {cofre_id}")
    print("Dados de 4 semanas e fixos planejados inseridos.")
    return op_id, cofre_id

def demonstrate_ledger_and_kpis(op_id):
    """Demonstra as funções de Ledger e KPIs."""
    print("\n--- 2. LEDGER E KPIS ---")
    
    # Saldo Atual
    current_balance = ledger.get_account_balance(op_id)
    total_cash = kpis.get_total_cash()
    print(f"Saldo Computado da Conta Operacional: R$ {current_balance:.2f}")
    print(f"Saldo Total de Caixa (Todas as Contas): R$ {total_cash:.2f}")
    
    # Despesas Variáveis da Semana Atual
    today = datetime.now().strftime(DATE_FORMAT)
    week_start = forecast.dates.get_week_start(today)
    weekly_expenses = kpis.get_weekly_variable_expenses(week_start, op_id)
    print(f"Despesas Variáveis na Semana ({week_start}): R$ {weekly_expenses:.2f}")
    
    # Transações
    transactions = ledger.list_transactions({'account_id': op_id, 'transaction_type': 'expense'})
    print(f"Total de Despesas na Conta Operacional: {len(transactions)} transações.")

def demonstrate_reconciliation(op_id):
    """Demonstra a função de Reconciliação (HITL)."""
    print("\n--- 3. RECONCILIAÇÃO (HITL) ---")
    
    # Simular que o saldo real é R$ 100.00 a mais que o computado
    computed_balance = ledger.get_account_balance(op_id)
    real_balance = computed_balance + 100.00
    
    today = datetime.now().strftime(DATE_FORMAT)
    week_start = reconciliation.dates.get_week_start(today)
    
    reconciliation_id = reconciliation.reconcile_account(week_start, op_id, real_balance)
    
    # Verificar o resultado
    query = "SELECT * FROM reconciliations WHERE week_start = ? AND account_id = ?"
    result = reconciliation.db.execute_query(query, (week_start, op_id))
    
    print(f"Reconciliação registrada para a semana {week_start} (ID: {reconciliation_id})")
    print(f"  Saldo Real Informado: R$ {result[0]['real_balance']:.2f}")
    print(f"  Saldo Computado: R$ {result[0]['computed_balance']:.2f}")
    print(f"  Delta (Real - Computado): R$ {result[0]['delta']:.2f}")

def demonstrate_forecast():
    """Demonstra a função de Forecast."""
    print("\n--- 4. FORECAST (30 DIAS) ---")
    
    forecast_data = forecast.forecast_cash_flow(days=30)
    
    print("Previsão de Fluxo de Caixa (30 dias):")
    print(f"  Saldo Atual: R$ {forecast_data['current_cash']:.2f}")
    print(f"  - Fixos Planejados: R$ {forecast_data['planned_fixed_expenses']:.2f}")
    print(f"  - Variáveis Projetadas: R$ {forecast_data['projected_variable_expenses']:.2f}")
    print(f"  = Saldo Previsto: R$ {forecast_data['forecasted_cash']:.2f}")

if __name__ == '__main__':
    op_id, cofre_id = setup_initial_data()
    demonstrate_ledger_and_kpis(op_id)
    demonstrate_reconciliation(op_id)
    demonstrate_forecast()
    
    print("\n--- FIM DO EXEMPLO ---")
    print("O CORE funcional está pronto para ser integrado a uma UI Streamlit.")
