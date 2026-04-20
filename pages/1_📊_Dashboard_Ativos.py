"""
pages/1_📊_Dashboard_Ativos.py
------------------------------
Tela de consulta e visão geral do inventário de ativos industriais.

Decisões de arquitetura:
    - get_equipamentos() retorna list[dict] — sem pandas.
    - Todos os filtros operam sobre lista_filtered via list comprehension,
      mantendo os tipos nativos Python (float/int) para KPIs e ficha técnica.
    - A exportação CSV é gerada com o módulo csv da stdlib, sem pandas.
    - st.stop() não é usado nesta página: mesmo sem ativos o dashboard
      deve exibir os KPIs zerados e o estado vazio da tabela.
"""

import csv
import io
import streamlit as st
from backend.mock_db import init_db, get_equipamentos
from utils import aplicar_design_fixo_sidebar

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard de Ativos | Challenge Sprint 1",
    page_icon="📊",
    layout="wide",
)

# CSS + sidebar centralizados — persiste em qualquer rerun desta página.
aplicar_design_fixo_sidebar()

# ── Inicialização do banco ────────────────────────────────────────────────────
init_db()

# ── CSS da página ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar mantém padrão corporativo do app.py */
    [data-testid="stSidebar"] { background-color: #0D3B8E; }
    [data-testid="stSidebar"] * { color: #E8F0FE !important; }
    [data-testid="stSidebar"] hr { border-color: #1A4FAD; }

    /* Cabeçalho da página */
    .page-header {
        background: linear-gradient(135deg, #0D3B8E 0%, #1560BD 60%, #2272D9 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 4px;
        position: relative;
        overflow: hidden;
    }
    .page-header::after {
        content: "📊";
        position: absolute;
        right: 32px; top: 50%;
        transform: translateY(-50%);
        font-size: 80px;
        opacity: 0.10;
    }
    .page-header h1 {
        color: #FFFFFF;
        font-size: 28px;
        font-weight: 800;
        margin: 0 0 6px 0;
    }
    .page-header p {
        color: #BBDEFB;
        font-size: 14px;
        margin: 0;
        max-width: 520px;
    }

    /* KPI Cards */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #DBEAFE;
        border-top: 4px solid #1560BD;
        border-radius: 10px;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(21,96,189,0.07);
    }
    [data-testid="stMetricLabel"] { color: #4A5568 !important; font-size: 12px !important; }
    [data-testid="stMetricValue"] { color: #0D3B8E !important; font-size: 28px !important; font-weight: 800 !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* Seção de Filtros */
    .filter-section {
        background: #FFFFFF;
        border: 1px solid #DBEAFE;
        border-radius: 10px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .filter-title {
        color: #0D3B8E;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Tabela */
    .table-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .table-title {
        color: #0D3B8E;
        font-size: 16px;
        font-weight: 700;
    }
    .tag-count {
        background: #EBF3FF;
        color: #1560BD;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Badge de status vazio */
    .empty-state {
        background: #F7FAFF;
        border: 1px dashed #93C5FD;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        color: #64748B;
    }

    /* Divider customizado */
    .section-divider {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 20px 0;
    }

    /* Ficha Técnica */
    .ficha-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
    }
    .ficha-badge {
        background: linear-gradient(135deg, #0D3B8E, #1560BD);
        color: #FFFFFF;
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .ficha-title {
        color: #0D3B8E;
        font-size: 16px;
        font-weight: 700;
    }
    .attr-label {
        color: #64748B;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 2px;
    }
    .attr-value {
        color: #0D3B8E;
        font-size: 20px;
        font-weight: 800;
    }
    .attr-card {
        background: #F7FAFF;
        border: 1px solid #DBEAFE;
        border-radius: 8px;
        padding: 14px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabeçalho da Página ───────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
        <h1>Dashboard de Ativos</h1>
        <p>
            Consulte os equipamentos registrados no sistema e acesse a ficha técnica detalhada.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Carrega os dados ──────────────────────────────────────────────────────────
# lista_full é a fonte de verdade imutável para esta renderização.
# Todos os filtros subsequentes operarão sobre lista_filtered (cópia),
# preservando os valores originais para os KPIs e para a ficha técnica.
lista_full: list[dict] = get_equipamentos()

# ── KPIs ─────────────────────────────────────────────────────────────────────
total_ativos = len(lista_full)

# set() elimina duplicatas; sorted() para ordenação estável nas opções de filtro.
fabricantes_set  = set(eq["Fabricante"] for eq in lista_full)
total_fab        = len(fabricantes_set)

pot_media = (
    sum(eq["Potência (kW)"] for eq in lista_full) / total_ativos
    if total_ativos > 0 else 0.0
)
pot_max = (
    max(eq["Potência (kW)"] for eq in lista_full)
    if total_ativos > 0 else 0.0
)

# Tensão mais comum: dict de frequências + max por valor
if total_ativos > 0:
    freq_tensao: dict = {}
    for eq in lista_full:
        v = eq["Tensão (V)"]
        freq_tensao[v] = freq_tensao.get(v, 0) + 1
    tensao_mais_comum = max(freq_tensao, key=lambda k: freq_tensao[k])
else:
    tensao_mais_comum = "—"

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)

col_k1.metric(
    label="⚙️ Total de Ativos",
    value=total_ativos,
    delta="↑ cadastrados" if total_ativos > 0 else None,
)
col_k2.metric(
    label="🏭 Fabricantes",
    value=total_fab,
    delta=f"{total_fab} distintos" if total_fab > 0 else None,
)
col_k3.metric(
    label="⚡ Potência Média",
    value=f"{pot_media:.1f} kW",
)
col_k4.metric(
    label="🔋 Maior Potência",
    value=f"{pot_max:.0f} kW",
)
col_k5.metric(
    label="🔌 Tensão Mais Comum",
    value=f"{tensao_mais_comum} V",
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Filtros Interativos ───────────────────────────────────────────────────────
st.markdown(
    "<div class='filter-title'>🔍 &nbsp; Filtros do Inventário</div>",
    unsafe_allow_html=True,
)

col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

with col_f1:
    fabricantes_disponiveis = sorted(fabricantes_set) if total_ativos > 0 else []
    fabricante_sel = st.multiselect(
        label="Fabricante",
        options=fabricantes_disponiveis,
        placeholder="Todos os fabricantes…",
        help="Selecione um ou mais fabricantes para filtrar.",
    )

with col_f2:
    if total_ativos > 0:
        pot_min_val = float(min(eq["Potência (kW)"] for eq in lista_full))
        pot_max_val = float(max(eq["Potência (kW)"] for eq in lista_full))
        if pot_min_val == pot_max_val:
            pot_max_val = pot_min_val + 1.0
        faixa_potencia = st.slider(
            label="Faixa de Potência (kW)",
            min_value=pot_min_val,
            max_value=pot_max_val,
            value=(pot_min_val, pot_max_val),
            step=0.5,
            help="Arraste para filtrar por faixa de potência nominal.",
        )
    else:
        faixa_potencia = (0.0, 0.0)
        st.slider("Faixa de Potência (kW)", 0.0, 1.0, (0.0, 1.0), disabled=True)

with col_f3:
    busca_tag = st.text_input(
        label="Buscar por TAG",
        placeholder="Ex: EQ-001",
        help="Filtragem parcial — case-insensitive.",
    )

# ── Aplicação dos Filtros ─────────────────────────────────────────────────────
# Os filtros são aplicados em cadeia sobre lista_filtered via list comprehension.
# A ordem importa: fabricante → potência → TAG. Filtros mais seletivos
# reduzem o conjunto antes da busca por string.
lista_filtered: list[dict] = list(lista_full)

if fabricante_sel:
    lista_filtered = [eq for eq in lista_filtered if eq["Fabricante"] in fabricante_sel]

if total_ativos > 0:
    lista_filtered = [
        eq for eq in lista_filtered
        if faixa_potencia[0] <= eq["Potência (kW)"] <= faixa_potencia[1]
    ]

if busca_tag.strip():
    termo = busca_tag.strip().lower()
    lista_filtered = [eq for eq in lista_filtered if termo in eq["TAG"].lower()]

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Tabela de Inventário ──────────────────────────────────────────────────────
col_th1, col_th2 = st.columns([6, 1])
with col_th1:
    st.markdown("<div class='table-title'>📋 Inventário de Equipamentos</div>", unsafe_allow_html=True)
with col_th2:
    st.markdown(
        f"<div class='tag-count' style='text-align:right'>{len(lista_filtered)} registro(s)</div>",
        unsafe_allow_html=True,
    )

if not lista_filtered:
    st.markdown(
        """
        <div class="empty-state">
            <div style="font-size:36px">🔍</div>
            <div style="font-weight:600; margin-top:8px">Nenhum ativo encontrado</div>
            <div style="font-size:13px; margin-top:4px">
                Ajuste os filtros acima ou cadastre novos equipamentos.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # lista_display formata os valores para exibição visual.
    # lista_filtered preserva os tipos originais para a ficha técnica abaixo.
    lista_display = [
        {
            "TAG":            eq["TAG"],
            "Modelo":         eq["Modelo"],
            "Fabricante":     eq["Fabricante"],
            "Potência (kW)":  f"{eq['Potência (kW)']:.1f} kW",
            "Tensão (V)":     f"{int(eq['Tensão (V)'])} V",
        }
        for eq in lista_filtered
    ]

    st.dataframe(
        lista_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "TAG": st.column_config.TextColumn(
                "TAG",
                help="Identificador único do ativo",
                width="small",
            ),
            "Modelo": st.column_config.TextColumn(
                "Modelo",
                help="Modelo do equipamento",
                width="large",
            ),
            "Fabricante": st.column_config.TextColumn(
                "Fabricante",
                width="medium",
            ),
            "Potência (kW)": st.column_config.TextColumn(
                "Potência",
                help="Potência nominal do equipamento",
                width="small",
            ),
            "Tensão (V)": st.column_config.TextColumn(
                "Tensão",
                help="Tensão de operação nominal",
                width="small",
            ),
        },
    )

    # ── Exportação rápida ────────────────────────────────────────────────────
    # CSV gerado com stdlib csv — sem dependência de pandas.
    st.markdown("<br>", unsafe_allow_html=True)
    col_exp1, col_exp2 = st.columns([5, 1])
    with col_exp2:
        _buf = io.StringIO()
        _writer = csv.DictWriter(_buf, fieldnames=["TAG", "Modelo", "Fabricante", "Potência (kW)", "Tensão (V)"])
        _writer.writeheader()
        _writer.writerows(lista_filtered)
        csv_bytes = _buf.getvalue().encode("utf-8")

        st.download_button(
            label="⬇️ Exportar CSV",
            data=csv_bytes,
            file_name="inventario_ativos.csv",
            mime="text/csv",
            use_container_width=True,
            help="Baixa o inventário filtrado como arquivo CSV.",
        )

    # ── Ficha Técnica Interativa ─────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='ficha-header'>
            <span class='ficha-badge'>🔎 CONSULTA RÁPIDA</span>
            <span class='ficha-title'>Ficha Técnica do Equipamento</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tags_disponiveis = [eq["TAG"] for eq in lista_filtered]
    tag_selecionada = st.selectbox(
        label="Selecione a TAG do equipamento para consultar a ficha técnica:",
        options=tags_disponiveis,
        index=0,
        placeholder="Escolha uma TAG…",
        help="Escolha a TAG para visualizar todos os atributos técnicos do equipamento.",
        key="selectbox_ficha_tecnica",
    )

    if tag_selecionada:
        # Localiza o registro original (com tipos numéricos preservados)
        registro = next(eq for eq in lista_filtered if eq["TAG"] == tag_selecionada)

        with st.expander(
            f"📋 Ficha Técnica Completa — {tag_selecionada}",
            expanded=True,
        ):
            # ── Linha 1: TAG + Modelo ────────────────────────────────────────
            col_f1, col_f2 = st.columns([1, 3])

            with col_f1:
                st.markdown(
                    f"""
                    <div class='attr-card'>
                        <div class='attr-label'>🏷️ TAG / Identificador</div>
                        <div class='attr-value'>{registro['TAG']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_f2:
                st.info(
                    f"**Modelo:** {registro['Modelo']}\n\n"
                    f"Equipamento identificado pela TAG **{registro['TAG']}**, "
                    f"fabricado por **{registro['Fabricante']}**."
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Linha 2: Fabricante | Potência | Tensão ──────────────────────
            col_a1, col_a2, col_a3 = st.columns(3)

            with col_a1:
                st.markdown(
                    f"""
                    <div class='attr-card'>
                        <div class='attr-label'>🏭 Fabricante</div>
                        <div class='attr-value'>{registro['Fabricante']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_a2:
                potencia_val = registro["Potência (kW)"]
                # Limiar de 50 kW — vide comentário em mock_db.py
                if potencia_val > 50:
                    st.warning(
                        f"**⚡ Potência Nominal:** `{potencia_val:.1f} kW`\n\n"
                        "ℹ️ Equipamento de **alta potência** — requer atenção especial "
                        "na instalação elétrica e gestão de demanda."
                    )
                else:
                    st.markdown(
                        f"""
                        <div class='attr-card'>
                            <div class='attr-label'>⚡ Potência Nominal</div>
                            <div class='attr-value'>{potencia_val:.1f} kW</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_a3:
                tensao_val = int(registro["Tensão (V)"])
                st.markdown(
                    f"""
                    <div class='attr-card'>
                        <div class='attr-label'>🔌 Tensão de Operação</div>
                        <div class='attr-value'>{tensao_val} V</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Métricas resumidas ───────────────────────────────────────────
            st.caption("📊 Resumo quantitativo do ativo selecionado:")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Potência", f"{potencia_val:.1f} kW")
            col_m2.metric("Tensão", f"{tensao_val} V")
            col_m3.metric("Fabricante", registro["Fabricante"])

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; color:#A0AEC0; font-size:11px;
                padding-top:16px; border-top:1px solid #E2E8F0; margin-top:24px;">
        Gestão de Ativos · Challenge Sprint 1 · Dados simulados via mock_db
    </div>
    """,
    unsafe_allow_html=True,
)
