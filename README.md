# 🏭 Gestão de Ativos Industriais

### Challenge Sprint 1, 2 & 3 — FIAP · 2026

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.20%2B-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![Sprint 3](https://img.shields.io/badge/Sprint_3-Passing-22c55e?style=flat-square)
![License](https://img.shields.io/badge/License-Academic-64748B?style=flat-square)

> Plataforma de gerenciamento e monitoramento de ativos industriais desenvolvida em **Python + Streamlit** como entregável das Sprints 1, 2 e 3 do Challenge FIAP. A aplicação opera com **zero dependências externas para processamento de dados**, utilizando exclusivamente os built-ins e estruturas nativas do Python. Visualizações interativas são geradas com **Plotly**.

---

## Índice

- [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Ambiente e Execução](#ambiente-e-execução)
- [Dependências](#dependências)
- [Páginas e Funcionalidades](#páginas-e-funcionalidades)
- [Arquitetura de Avaliação de Saúde](#arquitetura-de-avaliação-de-saúde)
- [Design System](#design-system)
- [Equipe de Desenvolvimento](#equipe-de-desenvolvimento)

---

## Visão Geral da Arquitetura

A aplicação adota o padrão **multipáginas nativo do Streamlit** (`/pages`), onde cada arquivo na pasta `pages/` é automaticamente registrado como uma rota independente pelo runtime.

### Camada de Persistência — `backend/mock_db.py`

A persistência de dados é gerenciada pelo módulo `backend/mock_db.py`, que utiliza `st.session_state` como armazenamento em memória, simulando operações de banco de dados (CRUD). Essa camada está **completamente desacoplada do frontend**: toda a lógica de negócio reside no backend, e as páginas consomem exclusivamente as funções públicas exportadas.

**Sprint 2 — Performance:** `obter_telemetria_historica()` decorada com `@st.cache_data`, eliminando reprocessamento desnecessário a cada rerun.

**Sprint 3 — Inteligência Operacional:** novas funções públicas para o painel de alertas:
- `gerar_alertas()` — retorna alertas ativos (Crítico e Alerta), críticos primeiro.
- `obter_historico_eventos()` — log cronológico de eventos operacionais.
- `gerar_resumo_nlp()` — resumo textual do estado do ativo (simulado; estrutura preparada para substituição por endpoint NLP/LLM real sem alterar o frontend).
- `simular_novo_alerta()` — injeta alerta crítico simulado (usado pelo botão/timer da UI).
- `reconhecer_alerta()` — marca alerta como reconhecido pela equipe de manutenção.

Esse desacoplamento garante que a substituição do mock por chamadas HTTP reais a um backend **FastAPI** não exigirá nenhuma alteração na camada de apresentação.

### Camada de UI Global — `utils.py` (Design System)

O módulo `utils.py` é o **núcleo de design da aplicação**. Ele centraliza:

- **Paleta única (`_Palette`):** todos os valores hex do sistema vivem em `PALETTE`. Nenhuma página hard-code cor.
- **Componentes reutilizáveis Sprint 1 & 2:**
  - `kpi_card()` — cartão de KPI com barra lateral colorida por criticidade.
  - `status_card()` — variante para exibir resultado de `avaliar_saude()` com cor semântica.
  - `section_header()` — cabeçalho de seção com barra vertical.
- **Componentes novos Sprint 3:**
  - `alert_card()` — card de alerta com resumo NLP, métricas e botão de reconhecimento.
  - `recommendation_card()` — card de recomendação de manutenção por urgência.
  - `event_row()` — linha do log de histórico de eventos com cor semântica.
- **Injeção de CSS Global (Dark Tech):** toda a folha de estilos corporativa gerada a partir de `PALETTE`.
- **Persistência de Layout entre Rotas:** sidebar reconstruída em cada ciclo.

### Visualizações Interativas — Plotly

A tela de Monitoramento usa **Plotly** (`plotly.graph_objects`) para séries temporais com duplo eixo Y, hover unificado e linhas de limite normativo.

---

## Estrutura do Projeto

```
CS-FrontEnd-Sprint3/
├── app.py                            # Ponto de entrada — shell global, sidebar e landing page
├── utils.py                          # Design system: PALETTE, componentes, CSS global
├── backend/
│   ├── __init__.py
│   └── mock_db.py                    # Persistência simulada: CRUD + telemetria + alertas + NLP
├── frontend/
│   └── __init__.py                   # Reservado para componentes de UI reutilizáveis
├── pages/
│   ├── 0_🚨_Painel_Alertas.py        # [SPRINT 3] Painel de alertas, NLP, recomendações, timer
│   ├── 1_Dashboard_Ativos.py         # Inventário com KPIs, filtros por planta e status de saúde
│   ├── 2_Novo_Cadastro.py            # Formulário validado de cadastro de ativos
│   └── 3_Monitoramento.py            # Telemetria em tempo real, Plotly, alertas críticos
├── .streamlit/
│   └── config.toml                   # Configurações do servidor e tema Streamlit
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
| `plotly` | 5.20.0 | Gráficos interativos: duplo eixo Y, hover, linhas de limite |

> **⚠️ Decisão Técnica — Zero-Dependency para Processamento de Dados**
>
> O projeto foi **intencionalmente refatorado** para operar sem `pandas` e sem `numpy`.
> Toda manipulação de dados utiliza **exclusivamente built-ins e estruturas nativas do Python**
> (`list`, `dict`, `set`, `math`, `random`, `csv`, `io`, `datetime`).
> O `plotly` é utilizado exclusivamente para **renderização visual**.

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
| **Dashboard de Ativos** | Métricas de inventário por **Planta/Área** · Filtro `selectbox` por planta · Coluna **Status de Saúde** 🟢🟡🔴 · Exportação CSV |
| **Monitoramento** | KPI Cards com barra lateral colorida · Gráficos Plotly com duplo eixo Y e hover unificado · `@st.cache_data` · `st.toast` para status Crítico |

### Sprint 3

| Página | Funcionalidades CS3 |
|:---|:---|
| **🚨 Painel de Alertas** | KPIs de resumo (total / críticos / em alerta / reconhecidos) · Cards de alerta com **resumo NLP simulado** · Filtro por status · Botão de reconhecimento · **Tab de Recomendações** com cards de ação por urgência · **Tab de Histórico** com log tabular de eventos · **Botão "Atualizar agora"** que injeta alerta crítico simulado + `st.toast` · **Timer automático** configurável (15s / 30s / 60s) |

---

## Arquitetura de Avaliação de Saúde

A função `avaliar_saude(temperatura, vibracao)` classifica o estado operacional com base em limites normativos:

| Status | Temperatura | Vibração | Referência |
|:---|:---|:---|:---|
| 🟢 Saudável | ≤ 75 °C | ≤ 4.5 mm/s | Operação nominal |
| 🟡 Alerta | 75 – 85 °C | 4.5 – 5.5 mm/s | IEC 60034-14 |
| 🔴 Crítico | > 85 °C | > 5.5 mm/s | ISO 10816-3 |

---

## Design System

Todas as cores do sistema são definidas em `PALETTE` (`utils.py`) — única fonte de verdade.

| Papel | Cor | Hex | Uso |
|:---|:---|:---|:---|
| Crítico | 🔴 | `#EF4444` | Temperatura > 85°C · Vibração > 5.5 mm/s |
| Alerta | 🟡 | `#F59E0B` | Temperatura > 75°C · Vibração > 4.5 mm/s |
| Saudável | 🟢 | `#34D399` | Operação nominal |
| Brand Primary | 🔵 | `#1560BD` | Botões, cards, barra da sidebar |
| Background | ⬛ | `#0F0F11` | Fundo principal (Dark Tech) |

Componentes reutilizáveis exportados por `utils.py`:

```python
# Sprint 1 & 2
from utils import kpi_card, status_card, section_header, PALETTE

# Sprint 3 (adicionais)
from utils import alert_card, recommendation_card, event_row
```

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

*Challenge Sprint 1, 2 & 3 · FIAP · 2026 · Stack: Python 3.11+ · Streamlit 1.33+ · Plotly 5.20+ · Zero-Dependency Data Processing*
