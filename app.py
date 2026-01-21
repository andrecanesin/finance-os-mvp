import streamlit as st
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Importar módulos do CORE
import db
import dates
import ledger
import kpis
import planned
import reconciliation
import forecast

# Configuração da página
st.set_page_config(
    page_title="Finance-OS",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar o banco de dados
db.initialize_db()

# ============================================================================
# UTILITÁRIOS DE FORMATAÇÃO
# ============================================================================

def format_currency(value: float) -> str:
    """Formata um valor em Real brasileiro."""
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def format_date(date_str: str) -> str:
    """Converte data de YYYY-MM-DD para DD/MM/YYYY."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except:
        return date_str

def get_week_display(week_start: str) -> str:
    """Retorna a exibição da semana em formato legível."""
    week_end = dates.get_week_end(week_start)
    return f"{format_date(week_start)} → {format_date(week_end)} (Seg → Dom)"

def get_expense_status(weekly_expenses: float, weekly_cap: float) -> tuple[str, str]:
    """
    Retorna o status textual e a cor para o gasto semanal.
    
    Returns:
        Tupla (status_text, color_indicator)
    """
    if weekly_cap <= 0:
        return "Sem limite configurado", "⚠️"
    
    percentage = (weekly_expenses / weekly_cap) * 100
    
    if percentage <= 80:
        return "Dentro do planejado", "✅"
    elif percentage <= 100:
        return "Atenção ao limite", "⚠️"
    else:
        return "Limite excedido", "❌"

# ============================================================================
# NAVEGAÇÃO SIDEBAR
# ============================================================================

st.sidebar.title("Finance-OS")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Lançamentos", "Reconciliação", "Configurações"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("MVP - Gestão Financeira com Human-in-the-Loop")

# ============================================================================
# PÁGINA: DASHBOARD
# ============================================================================

if page == "Dashboard":
    st.title("📊 Dashboard")
    
    # Obter conta operacional
    query = "SELECT id FROM accounts WHERE role = 'operacional' AND active = 1"
    op_account_result = db.execute_query(query)
    
    if not op_account_result:
        st.warning("⚠️ Nenhuma conta operacional configurada. Acesse Configurações para configurar.")
    else:
        operational_account_id = op_account_result[0]['id']
        
        # Seção: Semana Atual
        st.subheader("📅 Semana Atual")
        today = datetime.now().strftime("%Y-%m-%d")
        week_start, week_end = dates.get_current_week_range(today)
        st.markdown(f"**{get_week_display(week_start)}**")
        
        # Seção: Despesas Variáveis da Semana
        st.subheader("💸 Despesas Variáveis")
        
        col1, col2, col3 = st.columns(3)
        
        weekly_expenses = kpis.get_current_week_variable_expenses(operational_account_id, today)
        
        # Obter teto semanal
        weekly_cap_query = "SELECT value FROM settings WHERE key = 'weekly_cap_amount'"
        weekly_cap_result = db.execute_query(weekly_cap_query)
        weekly_cap = float(weekly_cap_result[0]['value']) if weekly_cap_result else 0.0
        
        status_text, status_icon = get_expense_status(weekly_expenses, weekly_cap)
        
        with col1:
            st.metric("Gasto Semanal", format_currency(weekly_expenses))
        
        with col2:
            st.metric("Teto Semanal", format_currency(weekly_cap))
        
        with col3:
            percentage = (weekly_expenses / weekly_cap * 100) if weekly_cap > 0 else 0
            st.metric("Utilização", f"{percentage:.1f}%")
        
        st.markdown(f"**Status:** {status_icon} {status_text}")
        
        # Seção: Total de Caixa
        st.subheader("🏦 Total de Caixa")
        total_cash = kpis.get_total_cash()
        st.metric("Saldo Total", format_currency(total_cash))
        st.caption("Total computado com base nos lançamentos")
        
        # Seção: Aviso de Reconciliação
        st.subheader("🔄 Reconciliação")
        
        # Verificar se há reconciliação da semana atual
        query = "SELECT * FROM reconciliations WHERE week_start = ?"
        recon_result = db.execute_query(query, (week_start,))
        
        if not recon_result:
            st.info("ℹ️ Reconciliação da semana ainda não realizada. Acesse a aba 'Reconciliação' para revisar.")
        else:
            st.success("✅ Reconciliação da semana realizada.")

# ============================================================================
# PÁGINA: LANÇAMENTOS
# ============================================================================

elif page == "Lançamentos":
    st.title("📝 Lançamentos")
    
    tab1, tab2 = st.tabs(["Novo Lançamento", "Histórico"])
    
    # TAB 1: Novo Lançamento
    with tab1:
        st.subheader("Inserir Nova Transação")
        
        # Obter contas ativas
        accounts_query = "SELECT id, name FROM accounts WHERE active = 1 ORDER BY name"
        accounts_result = db.execute_query(accounts_query)
        accounts_dict = {acc['name']: acc['id'] for acc in accounts_result}
        
        if not accounts_dict:
            st.error("❌ Nenhuma conta ativa configurada.")
        else:
            # Obter categorias
            categories_query = "SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL ORDER BY category"
            categories_result = db.execute_query(categories_query)
            categories_list = [cat['category'] for cat in categories_result] if categories_result else []
            
            # Formulário
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_date = st.date_input("Data", value=datetime.now())
                transaction_type = st.selectbox("Tipo", ["Entrada", "Saída", "Transferência"])
            
            with col2:
                account_name = st.selectbox("Conta", list(accounts_dict.keys()))
                account_id = accounts_dict[account_name]
            
            # Campos específicos para transferência
            if transaction_type == "Transferência":
                col3, col4 = st.columns(2)
                with col3:
                    to_account_name = st.selectbox("Conta Destino", [acc for acc in accounts_dict.keys() if acc != account_name])
                    to_account_id = accounts_dict[to_account_name]
                with col4:
                    pass  # Espaço vazio para alinhamento
            
            col5, col6 = st.columns(2)
            
            with col5:
                category = st.selectbox("Categoria", categories_list + ["Outra"])
                if category == "Outra":
                    category = st.text_input("Digite a categoria")
            
            with col6:
                method = st.selectbox("Método", ["PIX", "Boleto", "Débito", "Cartão", "Outro"])
            
            description = st.text_area("Descrição", height=80)
            amount = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            
            # Botão de submissão
            if st.button("Registrar Lançamento", type="primary"):
                try:
                    transaction_date_str = transaction_date.strftime("%Y-%m-%d")
                    
                    if transaction_type == "Transferência":
                        ledger.add_transfer(
                            date=transaction_date_str,
                            from_account_id=account_id,
                            to_account_id=to_account_id,
                            amount=amount,
                            description=description,
                            method=method
                        )
                        st.success("✅ Transferência registrada com sucesso!")
                    else:
                        # Mapear tipo para transaction_type do banco
                        type_map = {"Entrada": "income", "Saída": "expense"}
                        
                        ledger.add_transaction(
                            date=transaction_date_str,
                            description=description,
                            amount=amount,
                            account_id=account_id,
                            category=category if category else None,
                            transaction_type=type_map[transaction_type],
                            method=method
                        )
                        st.success("✅ Lançamento registrado com sucesso!")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar: {str(e)}")
    
    # TAB 2: Histórico
    with tab2:
        st.subheader("Histórico de Transações")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_account = st.selectbox("Filtrar por Conta", ["Todas"] + list(accounts_dict.keys()), key="filter_account")
        
        with col2:
            filter_type = st.selectbox("Filtrar por Tipo", ["Todos", "Entrada", "Saída", "Transferência"], key="filter_type")
        
        with col3:
            date_range = st.date_input("Intervalo de Datas", value=(datetime.now() - timedelta(days=30), datetime.now()), key="date_range")
        
        # Construir query com filtros
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if filter_account != "Todas":
            query += " AND account_id = ?"
            params.append(accounts_dict[filter_account])
        
        if filter_type != "Todos":
            type_map = {"Entrada": "income", "Saída": "expense", "Transferência": "transfer"}
            query += " AND transaction_type = ?"
            params.append(type_map[filter_type])
        
        if len(date_range) == 2:
            query += " AND date BETWEEN ? AND ?"
            params.append(date_range[0].strftime("%Y-%m-%d"))
            params.append(date_range[1].strftime("%Y-%m-%d"))
        
        query += " ORDER BY date DESC, id DESC"
        
        transactions = db.execute_query(query, tuple(params))
        
        if transactions:
            # Preparar dados para exibição
            display_data = []
            for tx in transactions:
                type_display = {"income": "Entrada", "expense": "Saída", "transfer": "Transferência"}.get(tx['transaction_type'], tx['transaction_type'])
                display_data.append({
                    "Data": format_date(tx['date']),
                    "Tipo": type_display,
                    "Descrição": tx['description'],
                    "Categoria": tx['category'] or "-",
                    "Valor": format_currency(tx['amount']),
                    "Método": tx['method'] or "-"
                })
            
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma transação encontrada com os filtros aplicados.")

# ============================================================================
# PÁGINA: RECONCILIAÇÃO
# ============================================================================

elif page == "Reconciliação":
    st.title("🔄 Reconciliação")
    
    st.markdown("**Revise os saldos de suas contas com base nos extratos.**")
    
    # Seleção da semana
    today = datetime.now().strftime("%Y-%m-%d")
    week_start, week_end = dates.get_current_week_range(today)
    
    selected_week_start = st.date_input(
        "Selecione a semana (Segunda-feira)",
        value=datetime.strptime(week_start, "%Y-%m-%d"),
        key="recon_week"
    )
    selected_week_start_str = selected_week_start.strftime("%Y-%m-%d")
    
    # Obter contas ativas
    accounts_query = "SELECT id, name FROM accounts WHERE active = 1 ORDER BY name"
    accounts_result = db.execute_query(accounts_query)
    
    if not accounts_result:
        st.error("❌ Nenhuma conta ativa configurada.")
    else:
        st.subheader("Saldos por Conta")
        
        for account in accounts_result:
            account_id = account['id']
            account_name = account['name']
            
            # Calcular saldo computado
            computed_balance = ledger.get_account_balance(account_id)
            
            # Verificar se há reconciliação anterior
            query = "SELECT real_balance FROM reconciliations WHERE week_start = ? AND account_id = ?"
            recon_result = db.execute_query(query, (selected_week_start_str, account_id))
            previous_real_balance = recon_result[0]['real_balance'] if recon_result else None
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"{account_name} - Saldo Computado", format_currency(computed_balance))
            
            with col2:
                real_balance = st.number_input(
                    f"{account_name} - Saldo Real (Extrato)",
                    value=previous_real_balance if previous_real_balance else computed_balance,
                    step=0.01,
                    key=f"real_balance_{account_id}"
                )
            
            with col3:
                delta = real_balance - computed_balance
                delta_color = "green" if delta == 0 else "orange"
                st.metric(f"Delta", format_currency(delta))
            
            # Botão de reconciliação
            if st.button(f"Reconciliar {account_name}", key=f"recon_btn_{account_id}"):
                try:
                    reconciliation.reconcile_account(selected_week_start_str, account_id, real_balance)
                    st.success(f"✅ Reconciliação de {account_name} registrada com sucesso!")
                    st.info("ℹ️ Diferença registrada para análise. Nenhuma correção automática foi aplicada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao reconciliar: {str(e)}")

# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif page == "Configurações":
    st.title("⚙️ Configurações")
    
    tab1, tab2 = st.tabs(["Teto Semanal", "Conta Operacional"])
    
    # TAB 1: Teto Semanal
    with tab1:
        st.subheader("Teto Semanal")
        
        # Obter teto atual
        query = "SELECT value FROM settings WHERE key = 'weekly_cap_amount'"
        result = db.execute_query(query)
        current_cap = float(result[0]['value']) if result else 0.0
        
        new_cap = st.number_input(
            "Defina o teto semanal (R$)",
            min_value=0.0,
            value=current_cap,
            step=10.0
        )
        
        if st.button("Salvar Teto Semanal", type="primary"):
            try:
                # Atualizar ou inserir
                db.execute_query(
                    "DELETE FROM settings WHERE key = 'weekly_cap_amount'"
                )
                db.execute_insert(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    ("weekly_cap_amount", str(new_cap))
                )
                st.success("✅ Teto semanal atualizado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")
    
    # TAB 2: Conta Operacional
    with tab2:
        st.subheader("Conta Operacional")
        
        # Obter contas
        accounts_query = "SELECT id, name, role FROM accounts ORDER BY name"
        accounts_result = db.execute_query(accounts_query)
        
        if not accounts_result:
            st.error("❌ Nenhuma conta configurada.")
        else:
            # Encontrar conta operacional atual
            current_op_id = None
            for acc in accounts_result:
                if acc['role'] == 'operacional':
                    current_op_id = acc['id']
                    break
            
            account_names = [acc['name'] for acc in accounts_result]
            current_op_name = next((acc['name'] for acc in accounts_result if acc['id'] == current_op_id), None)
            
            selected_op_name = st.selectbox(
                "Selecione a conta operacional",
                account_names,
                index=account_names.index(current_op_name) if current_op_name else 0
            )
            
            if st.button("Definir Conta Operacional", type="primary"):
                try:
                    selected_op_id = next(acc['id'] for acc in accounts_result if acc['name'] == selected_op_name)
                    
                    # Desmarcar todas as contas operacionais
                    db.execute_query("UPDATE accounts SET role = 'cofre' WHERE role = 'operacional'")
                    
                    # Marcar a selecionada como operacional
                    db.execute_query("UPDATE accounts SET role = 'operacional' WHERE id = ?", (selected_op_id,))
                    
                    st.success("✅ Conta operacional atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar: {str(e)}")
        
        # Seção: Gerenciar Contas
        st.subheader("Gerenciar Contas")
        
        with st.expander("Criar Nova Conta"):
            new_account_name = st.text_input("Nome da Conta")
            new_account_type = st.selectbox("Tipo", ["PF", "PJ"])
            new_account_role = st.selectbox("Papel", ["Operacional", "Cofre"])
            
            if st.button("Criar Conta"):
                try:
                    role_map = {"Operacional": "operacional", "Cofre": "cofre"}
                    db.execute_insert(
                        "INSERT INTO accounts (name, type, role, active) VALUES (?, ?, ?, ?)",
                        (new_account_name, new_account_type, role_map[new_account_role], 1)
                    )
                    st.success("✅ Conta criada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao criar conta: {str(e)}")

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.caption("Finance-OS MVP | Gestão Financeira com Human-in-the-Loop | v1.0")
