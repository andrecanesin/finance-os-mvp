# 2. Modelo de Dados SQLite

O modelo de dados é projetado para ser simples e eficiente, utilizando o SQLite como *backend* de persistência. Ele suporta a distinção entre finanças Pessoais (PF) e de Pessoa Jurídica (PJ), além de incorporar os campos necessários para o processo de **Human-in-the-Loop (HITL)**.

## 2.1. Definição das Tabelas

### Tabela `accounts` (Contas Bancárias/Carteiras)

Armazena todas as contas financeiras gerenciadas pelo sistema.

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Identificador único da conta. |
| `name` | `TEXT` | `NOT NULL` | Nome da conta (e.g., "Conta Corrente PF", "Conta PJ Principal"). |
| `type` | `TEXT` | `NOT NULL` | Tipo da conta (e.g., 'Checking', 'Savings', 'Cash'). |
| `initial_balance` | `REAL` | `NOT NULL` | Saldo inicial da conta. |
| `is_operational` | `BOOLEAN` | `NOT NULL` | **Regra de Negócio:** Indica se esta é a **Conta Operacional** (apenas uma deve ser `TRUE`). |
| `is_pf` | `BOOLEAN` | `NOT NULL` | Indica se a conta é de Pessoa Física. |
| `is_pj` | `BOOLEAN` | `NOT NULL` | Indica se a conta é de Pessoa Jurídica. |

### Tabela `categories` (Categorias de Transação)

Armazena as categorias de despesas e receitas.

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Identificador único da categoria. |
| `name` | `TEXT` | `NOT NULL` | Nome da categoria (e.g., "Alimentação", "Salário", "Marketing"). |
| `transaction_type` | `TEXT` | `NOT NULL` | Tipo de transação associada ('Income', 'Expense', 'Transfer'). |
| `is_pf` | `BOOLEAN` | `NOT NULL` | Categoria aplicável a PF. |
| `is_pj` | `BOOLEAN` | `NOT NULL` | Categoria aplicável a PJ. |

### Tabela `transactions` (Transações Financeiras)

A tabela central do sistema, contendo todos os registros de movimentação.

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

### Tabela `settings` (Configurações Globais)

Armazena pares chave-valor para configurações do sistema.

| Campo | Tipo SQLite | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `key` | `TEXT` | `PRIMARY KEY` | Chave da configuração (e.g., 'weekly_cap_amount', 'operational_account_id'). |
| `value` | `TEXT` | `NOT NULL` | Valor da configuração. |

## 2.2. Relacionamentos

*   `transactions.account_id` **(N:1)** `accounts.id`
*   `transactions.category_id` **(N:1)** `categories.id`

O `settings.value` pode armazenar o `id` da **Conta Operacional** e o valor do **Teto Semanal**. Por exemplo:
*   `key='weekly_cap_amount'`, `value='1500.00'`
*   `key='operational_account_id'`, `value='1'` (referenciando `accounts.id`)

Este modelo de dados é a base para a implementação das regras de negócio no próximo passo.
