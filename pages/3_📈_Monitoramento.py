"""
pages/3_📈_Monitoramento.py
----------------------------
Tela de Visualização de Dados Brutos — telemetria simulada de sensores.

Decisões de arquitetura:
    - numpy.random.default_rng com seed determinística (hash(TAG) + segundo_atual)
      gera valores diferentes a cada rerun sem depender de estado externo,
      simulando a chegada de novas amostras sem um WebSocket real.
    - O histórico usa seed indexada por minuto (não por segundo) para que
      a série temporal pareça estável durante a navegação dentro do mesmo
      minuto, enquanto a leitura atual varia a cada rerun.
    - st.stop() é chamado quando não há ativos para evitar que todos os
      blocos subsequentes renderizem com DataFrames vazios, o que geraria
      exceções de índice difíceis de depurar.
"""

import datetime
import traceback

import streamlit as st

from utils import aplicar_estilo_ui

# Import guard: numpy e pandas podem falhar por política de DLL no Windows.
# O set_page_config e o bloco de erro são renderizados antes de st.stop()
# para que a página exiba uma mensagem limpa mesmo sem o backend disponível.
_deps_ok = True
_deps_traceback = ""

try:
    import numpy as np
    import pandas as pd
    from backend.mock_db import init_db, get_equipamentos
except Exception as _exc:
    _deps_ok = False
    _deps_traceback = traceback.format_exc()

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitoramento | Challenge Sprint 1",
    page_icon="📈",
    layout="wide",
)

# CSS global centralizado — garante persistência em qualquer rerun desta página.
aplicar_estilo_ui()

# ── Inicialização do banco ────────────────────────────────────────────────────
if _deps_ok:
    init_db()

# ── Contenção de Erros ────────────────────────────────────────────────────────
if not _deps_ok:
    st.markdown(
        """
        <div style="
            background: rgba(239,68,68,0.08);
            border: 1px solid rgba(239,68,68,0.3);
            border-left: 4px solid #EF4444;
            border-radius: 8px;
            padding: 14px 20px;
            margin-bottom: 20px;
        ">
            <div style="font-weight:700; color:#FCA5A5; font-size:14px;">
                ⚠️ Não foi possível carregar os módulos técnicos de telemetria
            </div>
            <div style="color:#FCA5A5; font-size:12px; margin-top:4px;">
                Os componentes de aquisição de dados estão indisponíveis nesta sessão.
                Verifique as dependências do ambiente e reinicie a aplicação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("🔧 Exibir Detalhes Técnicos do Erro", expanded=False):
        st.code(_deps_traceback, language="python")
    st.stop()

# ── Constantes de simulação ───────────────────────────────────────────────────
# _V_REF é definido como 440 V (limite superior da classe de tensão industrial
# padrão no Brasil) para garantir que equipamentos de 380 V e 220 V fiquem
# dentro da faixa mensurável do ADC sem saturação.
_ADC_BITS: int   = 1023
_V_REF: float    = 440.0

# 3600 RPM corresponde a um motor síncrono de 2 pólos em 60 Hz.
# É o teto físico plausível sem redução mecânica para o período de simulação.
_RPM_MAX: float  = 3600.0
_HIST_POINTS: int = 60

# ── CSS da página ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0D3B8E; }
    [data-testid="stSidebar"] * { color: #E8F0FE !important; }
    [data-testid="stSidebar"] hr { border-color: #1A4FAD; }

    /* Cabeçalho */
    .page-header {
        background: linear-gradient(135deg, #0A2F6B 0%, #0D3B8E 50%, #1560BD 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 4px;
        position: relative;
        overflow: hidden;
    }
    .page-header::after {
        content: "📡";
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
    [data-testid="stMetricValue"] { color: #0D3B8E !important; font-size: 26px !important; font-weight: 800 !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* Cabeçalho de seção */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 8px 0 12px 0;
    }
    .section-badge {
        background: linear-gradient(135deg, #0D3B8E, #1560BD);
        color: #FFFFFF;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .section-title {
        color: #0D3B8E;
        font-size: 15px;
        font-weight: 700;
    }

    /* Bloco de informação do ativo */
    .asset-info-bar {
        background: #F7FAFF;
        border: 1px solid #DBEAFE;
        border-left: 4px solid #1560BD;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    .asset-info-item { display: flex; flex-direction: column; }
    .asset-info-label {
        color: #64748B;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }
    .asset-info-value {
        color: #0D3B8E;
        font-size: 15px;
        font-weight: 700;
    }

    /* Status online pulsante */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(105,240,174,0.12);
        border: 1px solid rgba(105,240,174,0.35);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        font-weight: 600;
        color: #1B5E20;
    }

    /* Divisor */
    .section-divider {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 22px 0;
    }

    /* Linha de info de gráfico */
    .chart-meta {
        color: #64748B;
        font-size: 12px;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabeçalho da Página ───────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
        <h1>Monitoramento de Telemetria</h1>
        <p>
            Visualização de dados brutos de sensores em tempo real simulado.
            Selecione um ativo para inspecionar as leituras analógicas e o histórico de sinais.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Carrega equipamentos ──────────────────────────────────────────────────────
df_eq: pd.DataFrame = get_equipamentos()

# Guard clause: sem ativos, todos os blocos posteriores falhariam em
# df_eq[df_eq["TAG"] == tag_sel].iloc[0] com IndexError silencioso.
# st.stop() interrompe a execução do script neste ponto sem lançar exceção.
if df_eq.empty:
    st.warning(
        "⚠️ **Nenhum equipamento cadastrado.**\n\n"
        "Acesse a página **➕ Novo Cadastro** para registrar ativos antes de iniciar o monitoramento."
    )
    st.stop()

# ── Seletor de equipamento ────────────────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>🎯 SELEÇÃO</span>
        <span class='section-title'>Equipamento Monitorado</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_sel, col_badge = st.columns([4, 1])

with col_sel:
    tags_list = df_eq["TAG"].tolist()
    tag_sel = st.selectbox(
        label="Selecione o equipamento para monitorar:",
        options=tags_list,
        index=0,
        key="monitoramento_tag_sel",
        help="Selecione a TAG do ativo para visualizar a telemetria simulada em tempo real.",
    )

with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    now_str = datetime.datetime.now().strftime("%H:%M:%S · %d/%m/%Y")
    st.markdown(
        f"<div class='live-badge'>● LIVE &nbsp;·&nbsp; {now_str}</div>",
        unsafe_allow_html=True,
    )

# ── Dados do ativo selecionado ────────────────────────────────────────────────
ativo = df_eq[df_eq["TAG"] == tag_sel].iloc[0]
tensao_nominal: float = float(ativo["Tensão (V)"])
potencia_kw: float    = float(ativo["Potência (kW)"])

# rpm_nominal é estimado por heurística de placa porque o schema do ativo
# não armazena RPM. O limiar de 50 kW separa motores de indução de uso
# geral (1.800 RPM, 4 pólos) de motores de alta potência (3.600 RPM, 2 pólos)
# na linha industrial padrão WEG/Siemens.
rpm_nominal = _RPM_MAX if potencia_kw >= 50 else 1800.0

# Barra de informações do ativo
st.markdown(
    f"""
    <div class='asset-info-bar'>
        <div class='asset-info-item'>
            <span class='asset-info-label'>🏷️ TAG</span>
            <span class='asset-info-value'>{ativo['TAG']}</span>
        </div>
        <div class='asset-info-item'>
            <span class='asset-info-label'>🔩 Modelo</span>
            <span class='asset-info-value'>{ativo['Modelo']}</span>
        </div>
        <div class='asset-info-item'>
            <span class='asset-info-label'>🏭 Fabricante</span>
            <span class='asset-info-value'>{ativo['Fabricante']}</span>
        </div>
        <div class='asset-info-item'>
            <span class='asset-info-label'>⚡ Potência</span>
            <span class='asset-info-value'>{potencia_kw:.1f} kW</span>
        </div>
        <div class='asset-info-item'>
            <span class='asset-info-label'>🔌 Tensão Nominal</span>
            <span class='asset-info-value'>{int(tensao_nominal)} V</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Geração de sinais simulados ───────────────────────────────────────────────
# Seeds distintas para leitura atual e histórico garantem que os dois não
# se tornem idênticos quando o usuário navega no mesmo segundo.
# `% (2**31)` mantém o seed dentro do limite aceito pelo PCG64 (numpy).
_seed = (hash(tag_sel) + int(datetime.datetime.now().second)) % (2**31)
rng   = np.random.default_rng(seed=_seed)

def _adc_de_tensao(v_real: float) -> int:
    """
    Converte Volts reais em leitura ADC de 10 bits com ruído gaussiano.

    O ruído de ±2% simula erros de quantização e variações de linha
    típicas de um ADC SAR sem filtro anti-aliasing dedicado.
    """
    bits = int((v_real / _V_REF) * _ADC_BITS)
    ruido = int(rng.normal(0, _ADC_BITS * 0.02))
    return int(np.clip(bits + ruido, 0, _ADC_BITS))

def _adc_de_rpm(rpm_real: float) -> int:
    """Converte RPM real → bits ADC (0–1023) com ruído ±1.5%."""
    bits = int((rpm_real / _RPM_MAX) * _ADC_BITS)
    ruido = int(rng.normal(0, _ADC_BITS * 0.015))
    return int(np.clip(bits + ruido, 0, _ADC_BITS))

def _bits_para_volts(bits: int) -> float:
    """Converte bits ADC → Volts reais."""
    return round((bits / _ADC_BITS) * _V_REF, 2)

def _bits_para_rpm(bits: int) -> float:
    """Converte bits ADC → RPM reais."""
    return round((bits / _ADC_BITS) * _RPM_MAX, 1)

# Leituras atuais
bits_tensao_atual = _adc_de_tensao(tensao_nominal)
bits_rpm_atual    = _adc_de_rpm(rpm_nominal)

volts_atual = _bits_para_volts(bits_tensao_atual)
rpm_atual   = _bits_para_rpm(bits_rpm_atual)

# Leituras anteriores (simula sample anterior — seed -1s)
rng_prev = np.random.default_rng(seed=(_seed - 1) % (2**31))
bits_tensao_prev = int(np.clip(
    int((tensao_nominal / _V_REF) * _ADC_BITS) + int(rng_prev.normal(0, _ADC_BITS * 0.02)),
    0, _ADC_BITS))
bits_rpm_prev = int(np.clip(
    int((rpm_nominal / _RPM_MAX) * _ADC_BITS) + int(rng_prev.normal(0, _ADC_BITS * 0.015)),
    0, _ADC_BITS))

volts_prev = _bits_para_volts(bits_tensao_prev)
rpm_prev   = _bits_para_rpm(bits_rpm_prev)

# Deltas
delta_bits_v  = bits_tensao_atual - bits_tensao_prev
delta_bits_r  = bits_rpm_atual    - bits_rpm_prev
delta_volts   = round(volts_atual  - volts_prev,   2)
delta_rpm     = round(rpm_atual    - rpm_prev,     1)

# ── Métricas — Sinal Bruto ────────────────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>📟 SINAL BRUTO</span>
        <span class='section-title'>Leitura ADC — Valores em Bits (0 a 1023)</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_b1, col_b2, col_b3, col_b4 = st.columns(4)

col_b1.metric(
    label="⚡ ADC Tensão (bits)",
    value=f"{bits_tensao_atual} bits",
    delta=f"{delta_bits_v:+d} bits",
    help="Leitura bruta do conversor analógico-digital para o canal de tensão.",
)
col_b2.metric(
    label="🔄 ADC RPM (bits)",
    value=f"{bits_rpm_atual} bits",
    delta=f"{delta_bits_r:+d} bits",
    help="Leitura bruta do encoder de velocidade angular do eixo.",
)
col_b3.metric(
    label="📡 Canal Ativo",
    value="CH-01 / CH-02",
    delta="2 canais OK",
    help="Canais ADC ativos nesta aquisição.",
)
col_b4.metric(
    label="🕒 Taxa de Amostragem",
    value="1 Hz",
    delta="Simulado",
    help="Frequência de aquisição dos dados — simulada a 1 amostra/segundo.",
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Métricas — Valores Convertidos ───────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>🔬 GRANDEZAS FÍSICAS</span>
        <span class='section-title'>Valores Convertidos em Unidades de Engenharia</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_c1, col_c2, col_c3, col_c4 = st.columns(4)

col_c1.metric(
    label="🔌 Tensão de Operação",
    value=f"{volts_atual:.1f} V",
    delta=f"{delta_volts:+.2f} V",
    help=f"Fórmula: (bits / {_ADC_BITS}) × {_V_REF} V",
)
col_c2.metric(
    label="🌀 Velocidade do Eixo",
    value=f"{rpm_atual:.0f} RPM",
    delta=f"{delta_rpm:+.1f} RPM",
    help=f"Fórmula: (bits / {_ADC_BITS}) × {_RPM_MAX} RPM",
)

# Potência estimada via V² / R (R estimada pela potência nominal)
r_estimada = (tensao_nominal ** 2) / (potencia_kw * 1000) if potencia_kw > 0 else 1.0
pot_estimada_w = (volts_atual ** 2) / r_estimada
pot_estimada_prev = (volts_prev ** 2) / r_estimada
delta_pot = round((pot_estimada_w - pot_estimada_prev) / 1000, 3)

col_c3.metric(
    label="⚡ Potência Estimada",
    value=f"{pot_estimada_w / 1000:.2f} kW",
    delta=f"{delta_pot:+.3f} kW",
    help="Estimativa via Lei de Joule: P = V² / R (R calculada da placa nominal).",
)

# Desvio percentual em relação ao nominal
desvio_pct = round(((volts_atual - tensao_nominal) / tensao_nominal) * 100, 2)
col_c4.metric(
    label="📊 Desvio da Tensão Nominal",
    value=f"{desvio_pct:+.2f}%",
    delta="⚠️ Fora de banda" if abs(desvio_pct) > 5 else "✅ Dentro da banda",
    delta_color="inverse" if abs(desvio_pct) > 5 else "normal",
    help="Desvio percentual em relação à tensão nominal de placa. Banda aceitável: ±5%.",
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Histórico Simulado ────────────────────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>📈 HISTÓRICO</span>
        <span class='section-title'>Séries Temporais — Últimas 60 Amostras</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Gera histórico usando numpy com ruído realista (seed fixo por TAG + minuto)
_seed_hist = (hash(tag_sel) + int(datetime.datetime.now().minute)) % (2**31)
rng_hist   = np.random.default_rng(seed=_seed_hist)

# Timestamps fictícios (últimos 60 segundos)
now_dt = datetime.datetime.now()
timestamps = [now_dt - datetime.timedelta(seconds=(_HIST_POINTS - i)) for i in range(_HIST_POINTS)]

# Séries de tensão com drift lento + ruído gaussiano
v_base_series   = tensao_nominal + rng_hist.normal(0, tensao_nominal * 0.015, _HIST_POINTS)
v_drift         = np.linspace(0, rng_hist.uniform(-2, 2), _HIST_POINTS)  # drift ±2 V
tensao_hist     = np.clip(v_base_series + v_drift, 0, _V_REF)

# Séries de RPM com bursts ocasionais
rpm_base_series = rpm_nominal + rng_hist.normal(0, rpm_nominal * 0.01, _HIST_POINTS)
rpm_bursts      = np.where(rng_hist.uniform(0, 1, _HIST_POINTS) > 0.92,
                           rng_hist.normal(rpm_nominal * 0.05, 10, _HIST_POINTS), 0)
rpm_hist        = np.clip(rpm_base_series + rpm_bursts, 0, _RPM_MAX)

# Potência estimada ao longo do tempo
pot_hist_kw = (tensao_hist ** 2) / (r_estimada * 1000)

df_hist = pd.DataFrame({
    "Tensão (V)":      tensao_hist.round(2),
    "RPM":             rpm_hist.round(1),
    "Potência (kW)":   pot_hist_kw.round(3),
}, index=pd.DatetimeIndex(timestamps))

# Abas de gráficos por grandeza
tab_v, tab_rpm, tab_pot = st.tabs(["🔌 Tensão (V)", "🌀 RPM", "⚡ Potência (kW)"])

with tab_v:
    st.markdown(
        f"<div class='chart-meta'>Tensão medida no canal CH-01 · Nominal: {int(tensao_nominal)} V · "
        f"Desvio atual: {desvio_pct:+.2f}%</div>",
        unsafe_allow_html=True,
    )
    st.line_chart(
        df_hist[["Tensão (V)"]],
        use_container_width=True,
        height=280,
        color=["#1560BD"],
    )

with tab_rpm:
    st.markdown(
        f"<div class='chart-meta'>Velocidade angular no eixo · Nominal: {int(rpm_nominal)} RPM · "
        f"Última leitura: {rpm_atual:.0f} RPM</div>",
        unsafe_allow_html=True,
    )
    st.line_chart(
        df_hist[["RPM"]],
        use_container_width=True,
        height=280,
        color=["#2272D9"],
    )

with tab_pot:
    st.markdown(
        f"<div class='chart-meta'>Potência estimada via Lei de Joule · Nominal: {potencia_kw:.1f} kW · "
        f"Atual: {pot_estimada_w / 1000:.3f} kW</div>",
        unsafe_allow_html=True,
    )
    st.line_chart(
        df_hist[["Potência (kW)"]],
        use_container_width=True,
        height=280,
        color=["#0D3B8E"],
    )

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Dados Brutos Tabulados ────────────────────────────────────────────────────
with st.expander("🗂️ Tabela de Dados Brutos — Últimas 60 Amostras", expanded=False):
    st.caption("Valores históricos brutos exportáveis. Use o botão de download para salvar o log.")

    df_raw = pd.DataFrame({
        "Timestamp":         [t.strftime("%H:%M:%S") for t in timestamps],
        "ADC Tensão (bits)": [_adc_de_tensao(v) for v in tensao_hist],
        "Tensão (V)":        tensao_hist.round(2),
        "ADC RPM (bits)":    [_adc_de_rpm(r) for r in rpm_hist],
        "RPM":               rpm_hist.round(1),
        "Potência (kW)":     pot_hist_kw.round(3),
    })

    st.dataframe(
        df_raw,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp":         st.column_config.TextColumn("⏱ Timestamp", width="small"),
            "ADC Tensão (bits)": st.column_config.NumberColumn("ADC Tensão (bits)", format="%d bits"),
            "Tensão (V)":        st.column_config.NumberColumn("Tensão (V)", format="%.2f V"),
            "ADC RPM (bits)":    st.column_config.NumberColumn("ADC RPM (bits)", format="%d bits"),
            "RPM":               st.column_config.NumberColumn("RPM", format="%.1f"),
            "Potência (kW)":     st.column_config.NumberColumn("Potência (kW)", format="%.3f kW"),
        },
    )

    csv_raw = df_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Exportar Log CSV",
        data=csv_raw,
        file_name=f"telemetria_{tag_sel}_{now_dt.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=False,
        help="Exporta o log de telemetria simulada para análise offline.",
    )

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; color:#A0AEC0; font-size:11px;
                padding-top:16px; border-top:1px solid #E2E8F0; margin-top:24px;">
        Gestão de Ativos · Monitoramento de Telemetria · Challenge Sprint 1 · Dados simulados via numpy.random
    </div>
    """,
    unsafe_allow_html=True,
)
