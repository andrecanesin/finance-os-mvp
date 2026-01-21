# 3. Regras de Negócio Principais

As regras de negócio são o cerne do Finance-OS, implementando a filosofia de gestão e o modelo **Human-in-the-Loop (HITL)**.

## 3.1. Definição do Ciclo Semanal

O ciclo financeiro do sistema é estritamente definido para suportar o cálculo do Teto Semanal e o agendamento da Reconciliação.

> **Regra:** A semana financeira começa na **Segunda-feira** e termina no **Domingo**.

*   **Impacto:** Todos os cálculos de agregação de gastos para o **Teto Semanal** devem filtrar transações cuja data esteja dentro deste intervalo semanal (Segunda 00:00:00 até Domingo 23:59:59).
*   **Ação de Sistema:** O sistema deve notificar o usuário sobre a necessidade de reconciliação no final do dia de Domingo ou no início do dia de Segunda-feira.

## 3.2. Teto Semanal (Weekly Cap)

O Teto Semanal é uma ferramenta de controle de gastos proativo.

> **Regra:** O sistema deve monitorar e alertar o usuário sobre o progresso dos gastos da **Conta Operacional** em relação a um valor predefinido (`settings.weekly_cap_amount`) dentro do ciclo semanal (Segunda a Domingo).

*   **Implementação:** O valor do Teto Semanal é armazenado na tabela `settings`.
*   **Cálculo:** O sistema soma o valor (`amount`) de todas as transações de despesa (negativas) da **Conta Operacional** que ocorreram desde a última Segunda-feira.
*   **Alerta:** O sistema deve fornecer um *status* visual (e.g., na UI) indicando:
    *   Percentual do teto utilizado.
    *   Valor restante para a semana.
    *   Um alerta crítico quando o uso ultrapassar 80% ou 100% do teto.

## 3.3. Conta Operacional (Operational Account)

A Conta Operacional é o foco do controle de gastos e do Teto Semanal.

> **Regra:** Deve haver **apenas uma** conta marcada como `is_operational = TRUE` na tabela `accounts`.

*   **Propósito:** Esta conta é a principal fonte de despesas diárias e é a única sujeita à regra do **Teto Semanal**.
*   **Validação:** O sistema deve garantir a unicidade desta conta. Se o usuário tentar marcar uma segunda conta como operacional, a anterior deve ser desmarcada automaticamente, ou o sistema deve impedir a ação.
*   **Configuração:** O ID desta conta pode ser armazenado em `settings.operational_account_id` para acesso rápido, embora a coluna `accounts.is_operational` seja a fonte primária de verdade.

## 3.4. Reconciliação Semanal Humana (Human-in-the-Loop - HITL)

A reconciliação é o ponto de contato obrigatório do usuário com o sistema para garantir a qualidade dos dados.

> **Regra:** No final de cada ciclo semanal (Domingo), o usuário **deve** revisar e reconciliar todas as transações com `reconciliation_status = 'Pending'`.

*   **Fluxo de Status da Transação (`transactions.reconciliation_status`):**
    1.  **'Pending':** Transação recém-importada ou inserida manualmente, sem categoria atribuída (`category_id` é `NULL`).
    2.  **'Auto-Classified':** Transação à qual o sistema atribuiu uma categoria automaticamente (e.g., por regras de descrição), mas que ainda precisa de validação humana.
    3.  **'Reconciled':** Transação que foi revisada e confirmada pelo usuário (seja ela 'Pending' ou 'Auto-Classified' anteriormente). A data da reconciliação é registrada em `transactions.reconciliation_date`.
*   **Obrigatoriedade:** O sistema deve bloquear a visualização de relatórios e a inserção de novas transações (exceto as de importação bruta) até que o painel de reconciliação esteja vazio (ou seja, não haja transações 'Pending' ou 'Auto-Classified' da semana anterior).
*   **Critério de Reconciliação:** Uma transação é considerada reconciliada quando o usuário:
    *   Atribui ou confirma a `category_id`.
    *   Confirma a `amount` e a `date`.
    *   O sistema então atualiza o `reconciliation_status` para 'Reconciled' e preenche o `reconciliation_date`.
