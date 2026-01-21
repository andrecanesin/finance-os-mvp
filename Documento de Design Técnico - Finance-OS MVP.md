# Documento de Design Técnico - Finance-OS MVP

**Autor:** Manus AI (Arquiteto de Software Sênior)
**Data:** 21 de Janeiro de 2026
**Objetivo:** Detalhar a arquitetura, o modelo de dados, as regras de negócio e as assinaturas de funções Python para o MVP do sistema de gestão financeira pessoal/PJ Finance-OS, com foco no método Human-in-the-Loop (HITL).

---

## 1. Arquitetura Geral do Sistema Finance-OS

O Finance-OS é concebido como um **MVP (Produto Mínimo Viável)** com uma arquitetura monolítica, focada na simplicidade, rapidez de desenvolvimento e na facilidade de integração do componente **Human-in-the-Loop (HITL)**. A escolha por uma arquitetura monolítica inicial com Python (e Streamlit para a UI futura) e SQLite garante um *setup* mínimo e alta portabilidade.

### 1.1. Componentes Chave

A arquitetura é dividida em três camadas principais, seguindo o padrão de três camadas (apresentação, lógica de negócio e dados), com um módulo central de *Core Logic* que implementa o HITL.

| Camada | Componente | Descrição |
| :--- | :--- | :--- |
| **Apresentação (UI)** | Interface (Streamlit/Web) | Camada de interação com o usuário para entrada de dados, visualização de relatórios e, crucialmente, a **Reconciliação Semanal Humana**. |
| **Lógica de Negócio** | Core Logic (Python) | Contém as regras de negócio, como o cálculo do Teto Semanal, a gestão da Conta Operacional e a lógica de classificação de transações. Este é o coração do sistema. |
| **Dados** | Repositório (SQLite) | Banco de dados leve e sem servidor, ideal para um MVP de gestão financeira pessoal/pequena empresa. Armazena transações, categorias, contas e configurações. |

### 1.2. O Modelo Human-in-the-Loop (HITL)

O princípio central do Finance-OS é que a **inteligência humana** é o validador final e o principal motor de aprendizado do sistema. O HITL é implementado através de um ciclo semanal obrigatório:

1.  **Classificação Automática (Sugestão):** O sistema tenta classificar novas transações com base em regras predefinidas ou aprendizado histórico.
2.  **Reconciliação Semanal (Validação Humana):** Ao final de cada semana (Domingo), o sistema exige que o usuário revise e confirme (ou corrija) todas as transações não classificadas ou classificadas com baixa confiança.
3.  **Aprendizado:** As correções e confirmações do usuário são usadas para refinar as regras internas e o modelo de classificação (se houver um futuro módulo de ML), garantindo que o sistema se torne mais preciso ao longo do tempo.

---

## 2. Modelo de Dados SQLite

O modelo de dados é projetado para ser simples e eficiente, utilizando o SQLite como *backend* de persistência. Ele suporta a distinção entre finanças Pessoais (PF) e de Pessoa Jurídica (PJ), além de incorporar os campos necessários para o processo de **Human-in-the-Loop (HITL)**.

### 2.1. Tabela `accounts` (Contas Bancárias/Carteiras)

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Identificador único da conta. |
| `name` | `TEXT` | `NOT NULL` | Nome da conta (e.g., "Conta Corrente PF", "Conta PJ Principal"). |
| `type` | `TEXT` | `NOT NULL` | Tipo da conta (e.g., 'Checking', 'Savings', 'Cash'). |
| `initial_balance` | `REAL` | `NOT NULL` | Saldo inicial da conta. |
| `is_operational` | `BOOLEAN` | `NOT NULL` | **Regra de Negócio:** Indica se esta é a **Conta Operacional** (apenas uma deve ser `TRUE`). |
| `is_pf` | `BOOLEAN` | `NOT NULL` | Indica se a conta é de Pessoa Física. |
| `is_pj` | `BOOLEAN` | `NOT NULL` | Indica se a conta é de Pessoa Jurídica. |

### 2.2. Tabela `categories` (Categorias de Transação)

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Identificador único da categoria. |
| `name` | `TEXT` | `NOT NULL` | Nome da categoria (e.g., "Alimentação", "Salário", "Marketing"). |
| `transaction_type` | `TEXT` | `NOT NULL` | Tipo de transação associada ('Income', 'Expense', 'Transfer'). |
| `is_pf` | `BOOLEAN` | `NOT NULL` | Categoria aplicável a PF. |
| `is_pj` | `BOOLEAN` | `NOT NULL` | Categoria aplicável a PJ. |

### 2.3. Tabela `transactions` (Transações Financeiras)

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Identificador único da transação. |
| `date` | `TEXT` | `NOT NULL` | Data da transação (formato ISO YYYY-MM-DD). |
| `description` | `TEXT` | `NOT NULL` | Descrição original da transação (e.g., extrato bancário). |
| `amount` | `REAL` | `NOT NULL` | Valor da transação (positivo para receita, negativo para despesa). |
| `account_id` | `INTEGER` | `NOT NULL`, `FOREIGN KEY` | Conta de origem/destino da transação. |
| `category_id` | `INTEGER` | `FOREIGN KEY` | Categoria atribuída à transação. Pode ser `NULL` se não classificada. |
| `is_pf` | `BOOLEAN` | `NOT NULL` | Marca se a transação é PF. |
| `is_pj` | `BOOLEAN` | `NOT NULL` | Marca se a transação é PJ. |
| `reconciliation_status` | `TEXT` | `NOT NULL` | **Regra HITL:** Status da reconciliação ('Pending', 'Auto-Classified', 'Reconciled'). |
| `reconciliation_date` | `TEXT` | `NULLABLE` | Data em que a transação foi humanamente reconciliada. |

### 2.4. Tabela `settings` (Configurações Globais)

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `key` | `TEXT` | `PRIMARY KEY` | Chave da configuração (e.g., 'weekly_cap_amount', 'operational_account_id'). |
| `value` | `TEXT` | `NOT NULL` | Valor da configuração. |

---

## 3. Regras de Negócio Principais

### 3.1. Ciclo Semanal

> **Regra:** A semana financeira começa na **Segunda-feira** e termina no **Domingo**.

*   **Impacto:** Todos os cálculos de agregação de gastos para o **Teto Semanal** devem filtrar transações cuja data esteja dentro deste intervalo semanal (Segunda 00:00:00 até Domingo 23:59:59).

### 3.2. Teto Semanal (Weekly Cap)

> **Regra:** O sistema deve monitorar e alertar o usuário sobre o progresso dos gastos da **Conta Operacional** em relação a um valor predefinido (`settings.weekly_cap_amount`) dentro do ciclo semanal (Segunda a Domingo).

*   **Foco:** Apenas despesas da **Conta Operacional** são consideradas.

### 3.3. Conta Operacional (Operational Account)

> **Regra:** Deve haver **apenas uma** conta marcada como `is_operational = TRUE` na tabela `accounts`.

*   **Propósito:** Esta conta é a principal fonte de despesas diárias e é a única sujeita à regra do **Teto Semanal**.

### 3.4. Reconciliação Semanal Humana (Human-in-the-Loop - HITL)

> **Regra:** No final de cada ciclo semanal (Domingo), o usuário **deve** revisar e reconciliar todas as transações com `reconciliation_status = 'Pending'` ou `'Auto-Classified'`.

*   **Obrigatoriedade:** O sistema deve bloquear a visualização de relatórios e a inserção de novas transações (exceto as de importação bruta) até que o painel de reconciliação esteja vazio.
*   **Status da Transação:**
    *   **'Pending':** Transação sem categoria.
    *   **'Auto-Classified':** Transação com categoria sugerida pelo sistema.
    *   **'Reconciled':** Transação validada pelo usuário, com `category_id` e `reconciliation_date` preenchidos.

---

## 4. Especificação das Assinaturas de Funções Python Centrais

As funções centrais (Core Logic) formam a API interna do sistema.

### 4.1. Funções de Transação e Persistência

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `add_transaction` | `def add_transaction(date: str, description: str, amount: float, account_id: int, is_pf: bool, is_pj: bool) -> int:` | Insere uma nova transação com status 'Pending'. |
| `import_transactions_from_csv` | `def import_transactions_from_csv(file_path: str, account_id: int) -> int:` | Processa um arquivo CSV de extrato e insere as transações. |
| `get_transactions_by_status` | `def get_transactions_by_status(status: str, account_id: int = None) -> list[dict]:` | Recupera transações por status de reconciliação. |
| `update_transaction_category` | `def update_transaction_category(transaction_id: int, category_id: int) -> bool:` | Atualiza a categoria de uma transação. |

### 4.2. Funções de Regras de Negócio e HITL

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `get_operational_account_id` | `def get_operational_account_id() -> int:` | Retorna o ID da conta operacional. |
| `get_weekly_cap_amount` | `def get_weekly_cap_amount() -> float:` | Retorna o valor do teto semanal. |
| `get_current_week_spending` | `def get_current_week_spending() -> dict:` | Retorna o gasto atual da semana na Conta Operacional e o percentual do teto. |
| `reconcile_transaction` | `def reconcile_transaction(transaction_id: int, category_id: int) -> bool:` | Função central do HITL: atualiza categoria, status para 'Reconciled' e registra a data. |
| `get_pending_reconciliation_count` | `def get_pending_reconciliation_count() -> int:` | Retorna o número de transações que exigem reconciliação humana. |

### 4.3. Funções de Configuração

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `set_operational_account` | `def set_operational_account(account_id: int) -> bool:` | Define a conta operacional, garantindo a unicidade. |
| `set_weekly_cap_amount` | `def set_weekly_cap_amount(amount: float) -> bool:` | Define o valor do teto semanal. |
| `create_category` | `def create_category(name: str, transaction_type: str, is_pf: bool, is_pj: bool) -> int:` | Cria uma nova categoria de transação. |
