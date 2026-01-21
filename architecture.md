# 1. Arquitetura Geral do Sistema Finance-OS

O Finance-OS é concebido como um **MVP (Produto Mínimo Viável)** com uma arquitetura monolítica, focada na simplicidade, rapidez de desenvolvimento e na facilidade de integração do componente **Human-in-the-Loop (HITL)**. A escolha por uma arquitetura monolítica inicial com Python (e potencialmente Streamlit para a UI, embora não seja o foco agora) e SQLite garante um *setup* mínimo e alta portabilidade.

## 1.1. Componentes Chave

A arquitetura é dividida em três camadas principais, seguindo o padrão de três camadas (apresentação, lógica de negócio e dados), com um módulo central de *Core Logic* que implementa o HITL.

| Camada | Componente | Descrição |
| :--- | :--- | :--- |
| **Apresentação (UI)** | Interface (Streamlit/Web) | Camada de interação com o usuário para entrada de dados, visualização de relatórios e, crucialmente, a **Reconciliação Semanal Humana**. |
| **Lógica de Negócio** | Core Logic (Python) | Contém as regras de negócio, como o cálculo do Teto Semanal, a gestão da Conta Operacional e a lógica de classificação de transações. Este é o coração do sistema. |
| **Dados** | Repositório (SQLite) | Banco de dados leve e sem servidor, ideal para um MVP de gestão financeira pessoal/pequena empresa. Armazena transações, categorias, contas e configurações. |

## 1.2. O Modelo Human-in-the-Loop (HITL)

O princípio central do Finance-OS é que a **inteligência humana** é o validador final e o principal motor de aprendizado do sistema. O HITL é implementado através de um ciclo semanal obrigatório:

1.  **Classificação Automática (Sugestão):** O sistema tenta classificar novas transações com base em regras predefinidas ou aprendizado histórico.
2.  **Reconciliação Semanal (Validação Humana):** Ao final de cada semana (Domingo), o sistema exige que o usuário revise e confirme (ou corrija) todas as transações não classificadas ou classificadas com baixa confiança.
3.  **Aprendizado:** As correções e confirmações do usuário são usadas para refinar as regras internas e o modelo de classificação (se houver um futuro módulo de ML), garantindo que o sistema se torne mais preciso ao longo do tempo.

Este modelo garante que a qualidade dos dados seja sempre alta, uma vez que o erro humano é mitigado pela revisão semanal e o erro do sistema é corrigido e serve como *feedback* imediato.

## 1.3. Fluxo de Dados Simplificado

1.  **Entrada de Dados:** O usuário insere transações manualmente ou via importação (e.g., CSV).
2.  **Processamento:** A **Core Logic** aplica a regra da **Conta Operacional** e tenta a **Classificação Automática**.
3.  **Regra do Teto Semanal:** A **Core Logic** monitora os gastos da semana (Segunda a Domingo) em relação ao **Teto Semanal** configurado.
4.  **Reconciliação:** A UI apresenta o painel de **Reconciliação Semanal** (HITL) para o usuário.
5.  **Persistência:** Todas as alterações e novas transações são salvas no **Repositório SQLite**.

Esta arquitetura é simples, mas robusta o suficiente para suportar as regras de negócio complexas e o ciclo HITL exigido.
