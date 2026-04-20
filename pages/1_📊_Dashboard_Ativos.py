"""
pages/1_📊_Dashboard_Ativos.py
------------------------------
Tela de consulta e visão geral do inventário de ativos industriais.

Decisões de arquitetura:
    - Todos os filtros operam sobre df_full via cópia defensiva (df_filtered),
      garantindo que o DataFrame original no session_state nunca seja mutado
      por operações de slicing encadeadas.
    - A ficha técnica consome df_filtered (não df_display) para preservar
      os tipos numéricos originais nos cálculos e comparações de negócio.
    - st.stop() não é usado nesta página porque mesmo sem ativos o
      dashboard deve exibir os KPIs zerados e o estado vazio da tabela.
"""

import streamlit as st
import pandas as pd
from backend.mock_db import init_db, get_equipamentos
from utils import aplicar_estilo_ui

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard de Ativos | Challenge Sprint 1",
    page_icon="📊",
    layout="wide",
)

# CSS global centralizado — garante persistência em qualquer rerun desta página.
aplicar_estilo_ui()

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
# df_full é a fonte de verdade imutável para esta renderização.
# Todos os filtros subsequentes operarão sobre df_filtered (cópia),
# preservando os valores originais para os KPIs e para a ficha técnica.
df_full: pd.DataFrame = get_equipamentos()

# ── KPIs ─────────────────────────────────────────────────────────────────────
total_ativos    = len(df_full)
total_fab       = df_full["Fabricante"].nunique() if total_ativos > 0 else 0
pot_media       = df_full["Potência (kW)"].mean()  if total_ativos > 0 else 0.0
pot_max         = df_full["Potência (kW)"].max()   if total_ativos > 0 else 0.0
tensao_mais_comum = (
    df_full["Tensão (V)"].mode().iloc[0] if total_ativos > 0 else "—"
)

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
    fabricantes_disponiveis = sorted(df_full["Fabricante"].unique().tolist()) if total_ativos > 0 else []
    fabricante_sel = st.multiselect(
        label="Fabricante",
        options=fabricantes_disponiveis,
        placeholder="Todos os fabricantes…",
        help="Selecione um ou mais fabricantes para filtrar.",
    )

with col_f2:
    if total_ativos > 0:
        pot_min_val = float(df_full["Potência (kW)"].min())
        pot_max_val = float(df_full["Potência (kW)"].max())
        # Garante que min != max (ex: só 1 registro)
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
# Os filtros são aplicados em cadeia sobre df_filtered.
# A ordem importa: fabricante → potência → TAG. Filtros mais seletivos
# reduzem o conjunto antes da busca por string, que é a operação mais
# custosa para inventários com muitos registros.
df_filtered = df_full.copy()

if fabricante_sel:
    df_filtered = df_filtered[df_filtered["Fabricante"].isin(fabricante_sel)]

if total_ativos > 0:
    df_filtered = df_filtered[
        (df_filtered["Potência (kW)"] >= faixa_potencia[0]) &
        (df_filtered["Potência (kW)"] <= faixa_potencia[1])
    ]

if busca_tag.strip():
    df_filtered = df_filtered[
        df_filtered["TAG"].str.contains(busca_tag.strip(), case=False, na=False)
    ]

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Tabela de Inventário ──────────────────────────────────────────────────────
col_th1, col_th2 = st.columns([6, 1])
with col_th1:
    st.markdown("<div class='table-title'>📋 Inventário de Equipamentos</div>", unsafe_allow_html=True)
with col_th2:
    st.markdown(
        f"<div class='tag-count' style='text-align:right'>{len(df_filtered)} registro(s)</div>",
        unsafe_allow_html=True,
    )

if df_filtered.empty:
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
    # df_display existe exclusivamente para formatação visual da tabela.
    # A ficha técnica abaixo usa df_filtered lido diretamente para
    # manter os tipos float/int originais e evitar parse de strings formatadas.
    df_display = df_filtered.copy()
    df_display["Potência (kW)"] = df_display["Potência (kW)"].map(lambda x: f"{x:.1f} kW")
    df_display["Tensão (V)"]    = df_display["Tensão (V)"].map(lambda x: f"{int(x)} V")

    st.dataframe(
        df_display,
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
    st.markdown("<br>", unsafe_allow_html=True)
    col_exp1, col_exp2 = st.columns([5, 1])
    with col_exp2:
        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
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

    # Selectbox com as TAGs disponíveis no resultado filtrado
    tags_disponiveis = df_filtered["TAG"].tolist()
    tag_selecionada = st.selectbox(
        label="Selecione a TAG do equipamento para consultar a ficha técnica:",
        options=tags_disponiveis,
        index=0,
        placeholder="Escolha uma TAG…",
        help="Escolha a TAG para visualizar todos os atributos técnicos do equipamento.",
        key="selectbox_ficha_tecnica",
    )

    if tag_selecionada:
        # Localiza o registro original (sem formatação de exibição)
        registro = df_filtered[df_filtered["TAG"] == tag_selecionada].iloc[0]

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
                # Limiar de 50 kW é a linha de corte entre motores de uso geral
                # e equipamentos de média tensão que exigem gestão de demanda
                # e infraestrutura elétrica dedicada. O st.warning sinaliza
                # essa distinção diretamente para o analista de manutenção.
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
