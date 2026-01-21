# 4. Especificação das Assinaturas de Funções Python Centrais

As funções centrais (Core Logic) serão implementadas em Python e devem interagir com o banco de dados SQLite. A clareza das assinaturas (função, parâmetros e retorno) é crucial para a modularidade do sistema.

## 4.1. Funções de Transação e Persistência

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `add_transaction` | `def add_transaction(date: str, description: str, amount: float, account_id: int, is_pf: bool, is_pj: bool) -> int:` | Insere uma nova transação no banco de dados com status 'Pending'. Retorna o ID da nova transação. |
| `import_transactions_from_csv` | `def import_transactions_from_csv(file_path: str, account_id: int) -> int:` | Processa um arquivo CSV de extrato, insere as transações e retorna o número de transações importadas. |
| `get_transactions_by_status` | `def get_transactions_by_status(status: str, account_id: int = None) -> list[dict]:` | Recupera uma lista de transações com um determinado `reconciliation_status`. |
| `update_transaction_category` | `def update_transaction_category(transaction_id: int, category_id: int) -> bool:` | Atualiza a categoria de uma transação. Usada na classificação automática e na reconciliação. |

## 4.2. Funções de Regras de Negócio e HITL

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `get_operational_account_id` | `def get_operational_account_id() -> int:` | Retorna o ID da conta operacional configurada. |
| `get_weekly_cap_amount` | `def get_weekly_cap_amount() -> float:` | Retorna o valor do teto semanal configurado. |
| `calculate_weekly_spending` | `def calculate_weekly_spending(account_id: int, start_date: str, end_date: str) -> float:` | Calcula o total de despesas (valores negativos) para a conta e período especificados. |
| `get_current_week_spending` | `def get_current_week_spending() -> dict:` | Retorna um dicionário com o gasto atual da semana (Segunda a Domingo) na Conta Operacional e o percentual do teto utilizado. |
| `reconcile_transaction` | `def reconcile_transaction(transaction_id: int, category_id: int) -> bool:` | Função central do HITL. Atualiza a categoria, define o `reconciliation_status` para 'Reconciled' e registra a data atual. |
| `get_pending_reconciliation_count` | `def get_pending_reconciliation_count() -> int:` | Retorna o número total de transações com status 'Pending' ou 'Auto-Classified' que exigem atenção humana. |

## 4.3. Funções de Configuração

| Função | Assinatura (Python Type Hinting) | Descrição |
| :--- | :--- | :--- |
| `set_operational_account` | `def set_operational_account(account_id: int) -> bool:` | Define a conta operacional, garantindo que apenas uma esteja ativa. |
| `set_weekly_cap_amount` | `def set_weekly_cap_amount(amount: float) -> bool:` | Define o valor do teto semanal. |
| `create_category` | `def create_category(name: str, transaction_type: str, is_pf: bool, is_pj: bool) -> int:` | Cria uma nova categoria de transação. |

Essas assinaturas formam a API interna do sistema, permitindo que a camada de UI (futuramente Streamlit) interaja com a lógica de negócio e o banco de dados de forma limpa e desacoplada. O uso de *type hinting* em Python (`str`, `int`, `float`, `bool`, `list[dict]`) garante a clareza e a facilidade de manutenção do código.
