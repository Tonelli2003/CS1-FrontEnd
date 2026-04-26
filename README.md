# Challenge Sprint 1 — Gestão de Ativos

Plataforma de gerenciamento de ativos industriais desenvolvida em **Python + Streamlit** como entregável do Challenge Sprint 1 da FIAP.

---

## Visão Geral da Arquitetura

A aplicação adota o padrão **multipáginas nativo do Streamlit** (`/pages`), onde cada arquivo na pasta `pages/` é automaticamente registrado como uma rota independente pelo runtime.

A persistência de dados é gerenciada pelo módulo `backend/mock_db.py`, que utiliza `st.session_state` como armazenamento em memória, simulando as operações de banco de dados (CRUD). Essa camada está **completamente desacoplada do frontend**: toda a lógica de negócio reside no backend e as páginas consomem exclusivamente as funções públicas exportadas (`init_db`, `get_equipamentos`, `adicionar_equipamento`), sem acessar `session_state` diretamente.

Esse desacoplamento garante que a substituição do mock por chamadas HTTP reais a um backend **FastAPI** não exige nenhuma alteração na camada de apresentação.

```
CS1_Frontend/
├── app.py                         # Ponto de entrada — shell global, sidebar e landing page
├── backend/
│   └── mock_db.py                 # Camada de persistência simulada (session_state)
├── pages/
│   ├── 1_📊_Dashboard_Ativos.py   # Inventário com KPIs, filtros e ficha técnica
│   ├── 2_➕_Novo_Cadastro.py      # Formulário de cadastro de novos ativos
│   └── 3_📈_Monitoramento.py      # Telemetria simulada com dados brutos de sensores
├── requirements.txt
└── README.md
```

---

## Ambiente e Execução

### 1. Pré-requisitos

- Python **3.11** ou superior
- `pip` atualizado

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar o ambiente virtual

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 4. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5. Executar a aplicação

```bash
python -m streamlit run app.py
```

A aplicação ficará disponível em `http://localhost:8501`.

---

## Dependências

| Pacote       | Versão mínima | Finalidade                                      |
|:-------------|:-------------:|:------------------------------------------------|
| `streamlit`  | 1.33.0        | Framework de interface web multipáginas         |
| `pandas`     | 2.2.0         | Manipulação de DataFrames e exportação CSV      |
| `numpy`      | 1.26.0        | Geração de sinais simulados de sensores (ADC)   |

---

## Páginas do Sistema

| Página                     | Descrição                                                                 |
|:---------------------------|:--------------------------------------------------------------------------|
| **Home** (`app.py`)        | Landing page com KPIs globais e status do sistema                        |
| **Dashboard de Ativos**    | Inventário completo com filtros, tabela interativa e ficha técnica        |
| **Novo Cadastro**          | Formulário validado para registro de novos equipamentos industriais       |
| **Monitoramento**          | Telemetria simulada com sinais ADC brutos, conversão e gráficos históricos |

---

## Equipe de Desenvolvimento

| Nome                                    |
|:----------------------------------------|
| Augusto Oliveira Codo de Sousa | RM562080  |
| Felipe de Oliveira Cabral | RM561720  |
| Gabriel Tonelli Avelino Dos Santos | RM564705  |
| Vinícius Adrian Siqueira de Oliveira | RM564962 |
| Sofia Bueris Netto de Souza | RM565818  |

---

*Challenge Sprint 1 · FIAP · 2026*
