# 🏭 Gestão de Ativos Industriais

### Challenge Sprint 1 & 2 — FIAP · 2026

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Sprint 2](https://img.shields.io/badge/Sprint_2-Passing-22c55e?style=flat-square)
![Zero Deps](https://img.shields.io/badge/Data_Processing-Zero_Dependencies-0D3B8E?style=flat-square)
![License](https://img.shields.io/badge/License-Academic-64748B?style=flat-square)

> Plataforma de gerenciamento e monitoramento de ativos industriais desenvolvida em **Python + Streamlit** como entregável das Sprints 1 e 2 do Challenge FIAP. A aplicação opera com **zero dependências externas para processamento de dados**, utilizando exclusivamente os built-ins e estruturas nativas do Python.

---

## Índice

- [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Ambiente e Execução](#ambiente-e-execução)
- [Dependências](#dependências)
- [Páginas e Funcionalidades](#páginas-e-funcionalidades)
- [Equipe de Desenvolvimento](#equipe-de-desenvolvimento)

---

## Visão Geral da Arquitetura

A aplicação adota o padrão **multipáginas nativo do Streamlit** (`/pages`), onde cada arquivo na pasta `pages/` é automaticamente registrado como uma rota independente pelo runtime.

### Camada de Persistência — `backend/mock_db.py`

A persistência de dados é gerenciada pelo módulo `backend/mock_db.py`, que utiliza `st.session_state` como armazenamento em memória, simulando operações de banco de dados (CRUD). Essa camada está **completamente desacoplada do frontend**: toda a lógica de negócio reside no backend, e as páginas consomem exclusivamente as funções públicas exportadas — `init_db`, `get_equipamentos`, `adicionar_equipamento`, `obter_telemetria_historica`, `obter_ultimas_duas_leituras` e `avaliar_saude` — sem acessar `session_state` diretamente.

Esse desacoplamento garante que a substituição do mock por chamadas HTTP reais a um backend **FastAPI** não exigirá nenhuma alteração na camada de apresentação.

### Camada de UI Global — `utils.py`

O módulo `utils.py` é o **núcleo de design da aplicação**. Ele centraliza:

- **Injeção de CSS Global (Dark Tech):** toda a folha de estilos corporativa — paleta azul `#0D3B8E`, tipografia, cards, badges e animações — é injetada por `aplicar_design_fixo_sidebar()`. Essa abordagem elimina a duplicação de estilos entre páginas e garante coerência visual total.
- **Persistência de Layout entre Rotas:** o Streamlit reexecuta o script completo de cada página a cada rerun. `utils.py` reconstrói a sidebar (card de identidade, badges de status do sistema e links de navegação) em cada ciclo, evitando o "piscar" de componentes nativos durante a navegação.
- **Cross-Page State:** o estado global é preservado via `st.session_state`, garantindo que filtros, seleções e dados de sessão sobrevivam à troca de rotas sem exigir recarregamento da base de dados mockada.

---

## Estrutura do Projeto

```
CS1-FrontEnd-master/
├── app.py                         # Ponto de entrada — shell global, sidebar e landing page
├── utils.py                       # CSS global (Dark Tech), sidebar persistente e Cross-Page State
├── backend/
│   ├── __init__.py
│   └── mock_db.py                 # Persistência simulada: CRUD + telemetria + avaliação de saúde
├── frontend/
│   └── __init__.py                # Reservado para componentes de UI reutilizáveis
├── pages/
│   ├── 1_📊_Dashboard_Ativos.py   # Inventário com KPIs, filtros por planta e status de saúde
│   ├── 2_➕_Novo_Cadastro.py      # Formulário validado de cadastro de ativos
│   └── 3_📈_Monitoramento.py      # Telemetria em tempo real, séries históricas e alertas críticos
├── .streamlit/
│   └── config.toml                # Configurações do servidor e tema Streamlit
├── requirements.txt
└── README.md
```

---

## Ambiente e Execução

### Pré-requisitos

- Python **3.11** ou superior
- `pip` atualizado

### 1. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 2. Ativar o ambiente virtual

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação

```bash
python -m streamlit run app.py
```

A aplicação ficará disponível em [`http://localhost:8501`](http://localhost:8501).

---

## Dependências

| Pacote | Versão mínima | Finalidade |
|:---|:---:|:---|
| `streamlit` | 1.33.0 | Framework de interface web multipáginas |

> **⚠️ Decisão Técnica — Zero-Dependency para Processamento de Dados**
>
> O projeto foi **intencionalmente refatorado** para operar sem `pandas` e sem `numpy`.
> Toda manipulação de dados utiliza **exclusivamente built-ins e estruturas nativas do Python**
> (`list`, `dict`, `set`, `math`, `random`, `csv`, `io`, `datetime`).
>
> **Motivação:** ambientes Windows corporativos frequentemente impõem políticas restritivas
> de execução de DLLs (compiladas em C/Fortran) que bloqueiam a inicialização de
> extensões nativas como `numpy.core`, `pandas._libs` e similares. A remoção dessas
> dependências garante **100% de compatibilidade** com ambientes controlados, execução
> sem privilégios de administrador e instalação via `pip` sem necessidade de compiladores
> externos (MSVC, MinGW). O `st.dataframe()` e o `st.line_chart()` aceitam `list[dict]`
> diretamente, tornando o pandas dispensável para fins de visualização.

---

## Páginas e Funcionalidades

### Sprint 1

| Página | Funcionalidades |
|:---|:---|
| **Home** (`app.py`) | Landing page com KPIs globais, status do sistema e navegação centralizada |
| **Novo Cadastro** | Formulário com validação de campos para registro de novos equipamentos industriais |

### Sprint 2

| Página | Funcionalidades CS2 |
|:---|:---|
| **Dashboard de Ativos** | Métricas de inventário por **Planta/Área** (Norte, Sul, Leste) com contagem dinâmica · Filtro `selectbox` por planta em cadeia com filtros existentes (fabricante, potência, TAG) · Coluna **Status de Saúde** na tabela com ícones semânticos **🟢 Saudável / 🟡 Alerta / 🔴 Crítico** calculados via `avaliar_saude()` a partir da última leitura de telemetria · Exportação CSV atualizada com colunas `Planta` e `Saúde` |
| **Monitoramento** | **Cabeçalho Operacional:** imagem da placa do motor (`st.image`) + card de status colorido por criticidade · **Métricas de Tempo Real:** `st.metric` para Temperatura, Vibração e Corrente com **delta** em relação à hora anterior (via `obter_ultimas_duas_leituras()`) e `delta_color="inverse"` para alertas visuais · **Séries Temporais:** três `st.line_chart` independentes (Temperatura · Vibração · Corrente) gerados a partir do histórico de 10h sem numpy · **Sistema de Notificação Ativa:** `st.toast` disparado automaticamente ao renderizar quando o status do ativo for Crítico |

---

## Arquitetura de Avaliação de Saúde

A função `avaliar_saude(temperatura, vibracao)` classifica o estado operacional com base em limites normativos:

| Status | Temperatura | Vibração | Referência |
|:---|:---|:---|:---|
| 🟢 Saudável | ≤ 65 °C | ≤ 3.5 mm/s | Operação nominal |
| 🟡 Alerta | 65 – 80 °C | 3.5 – 5.0 mm/s | IEC 60034-14 |
| 🔴 Crítico | > 80 °C | > 5.0 mm/s | ISO 10816-3 |

---

## Equipe de Desenvolvimento

| Nome | RM |
|:---|:---|
| Augusto Oliveira Codo de Sousa | RM562080 |
| Felipe de Oliveira Cabral | RM561720 |
| Gabriel Tonelli Avelino Dos Santos | RM564705 |
| Vinícius Adrian Siqueira de Oliveira | RM564962 |
| Sofia Bueris Netto de Souza | RM565818 |

---

*Challenge Sprint 1 & 2 · FIAP · 2026 · Stack: Python 3.11+ · Streamlit 1.33+ · Zero-Dependency Data Processing*
