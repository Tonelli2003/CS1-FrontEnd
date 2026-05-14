"""
pages/3_📈_Monitoramento.py
----------------------------
Tela de Visualização de Dados Brutos — telemetria simulada de sensores.

Decisões de arquitetura:
    - Todas as dependências externas (numpy, pandas) foram removidas.
      random.gauss() do stdlib substitui np.random.normal().
      random.seed() com hash(TAG)+segundo garante variação por rerun.
    - O histórico usa seed por minuto para aparência estável durante
      a navegação dentro do mesmo minuto.
    - st.line_chart aceita list[dict] nativamente — sem DataFrame.
    - st.stop() é chamado quando não há ativos para evitar IndexError
      nos blocos subsequentes.
"""

import csv
import datetime
import io
import random
import traceback
import streamlit as st

from utils import aplicar_design_fixo_sidebar

# Import guard: apenas backend.mock_db pode falhar agora.
_deps_ok = True
_deps_traceback = ""

try:
    from backend.mock_db import (
        init_db,
        get_equipamentos,
        obter_telemetria_historica,
        obter_ultimas_duas_leituras,
        avaliar_saude,
    )
except Exception as _exc:
    _deps_ok = False
    _deps_traceback = traceback.format_exc()

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitoramento | Challenge Sprint 1",
    page_icon="📈",
    layout="wide",
)

# CSS + sidebar centralizados — persiste em qualquer rerun desta página.
aplicar_design_fixo_sidebar()

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
lista_eq: list[dict] = get_equipamentos()

# Guard clause: sem ativos, st.stop() previne IndexError nos blocos seguintes.
if not lista_eq:
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
    tags_list = [eq["TAG"] for eq in lista_eq]

    # ── Navegação Cruzada (Sprint 2) ─────────────────────────────────────────
    # Se o usuário chegou aqui via botão "Abrir Monitoramento" do Dashboard,
    # 'tag_navegacao' já está no session_state com a TAG desejada.
    # Calculamos o índice correspondente para pré-selecionar o selectbox.
    # A chave é deletada imediatamente após a leitura para que reruns
    # subsequentes (navegação manual) não a reutilizem involuntariamente.
    _default_index = 0
    if "tag_navegacao" in st.session_state:
        _tag_nav = st.session_state.pop("tag_navegacao")
        if _tag_nav in tags_list:
            _default_index = tags_list.index(_tag_nav)

    tag_sel = st.selectbox(
        label="Selecione o equipamento para monitorar:",
        options=tags_list,
        index=_default_index,
        key="monitoramento_tag_sel",
        help=(
            "Escolha a TAG do ativo cadastrado no sistema. "
            "O painel carregará automaticamente o histórico de "
            "telemetria e calculará o status de saúde em tempo real."
        ),
    )

with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    now_str = datetime.datetime.now().strftime("%H:%M:%S · %d/%m/%Y")
    st.markdown(
        f"<div class='live-badge'>● LIVE &nbsp;·&nbsp; {now_str}</div>",
        unsafe_allow_html=True,
    )

# ── Dados do ativo selecionado ────────────────────────────────────────────────
ativo = next(eq for eq in lista_eq if eq["TAG"] == tag_sel)
tensao_nominal: float = float(ativo["Tensão (V)"])
potencia_kw: float    = float(ativo["Potência (kW)"])

# rpm_nominal é estimado por heurística de placa porque o schema do ativo
# não armazena RPM. O limiar de 50 kW separa motores de indução de uso
# geral (1.800 RPM, 4 pólos) de motores de alta potência (3.600 RPM, 2 pólos).
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

# ── Sprint 2: Cabeçalho Operacional ──────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>🖥️ PAINEL OPERACIONAL</span>
        <span class='section-title'>Status e Identificação Visual do Ativo</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Obtém histórico e as duas últimas leituras para cálculo de delta.
_historico_s2          = obter_telemetria_historica(tag_sel, num_leituras=20)
_ultimo_s2, _prev_s2   = obter_ultimas_duas_leituras(tag_sel)
_status_s2             = avaliar_saude(_ultimo_s2["temperatura"], _ultimo_s2["vibracao"])
_temp_s2               = _ultimo_s2["temperatura"]
_vib_s2                = _ultimo_s2["vibracao"]
_corr_s2               = _ultimo_s2["corrente"]

# ── Notificação ativa: toast imediato se status Crítico (Sprint 2 Bônus) ──────
if _status_s2 == "🔴 Crítico":
    st.toast(
        f"⚠️ Alerta Crítico — {tag_sel}: Parâmetros fora da normalidade! "
        f"Temp: {_temp_s2:.1f} °C · Vib: {_vib_s2:.2f} mm/s",
        icon="🚨",
    )

# Cor do card de status baseada na saúde.
_status_cores = {
    "🔴 Crítico":  ("#FFEBEE", "#C62828", "#EF9A9A"),
    "🟡 Alerta":   ("#FFFDE7", "#F57F17", "#FFE082"),
    "🟢 Saudável": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
}
_bg, _fg, _border = _status_cores.get(_status_s2, ("#F7FAFF", "#0D3B8E", "#DBEAFE"))

_img_url = ativo.get("imagem_placa", "https://via.placeholder.com/300x150.png?text=Placa")
_planta   = ativo.get("planta", "—")

col_img, col_status = st.columns([1, 2])

with col_img:
    st.image(_img_url, caption=f"Placa — {ativo['Modelo']}", use_container_width=True)

with col_status:
    st.markdown(
        f"""
        <div style="background:{_bg}; border:2px solid {_border}; border-radius:12px;
                    padding:24px 28px; height:100%;">
            <div style="font-size:13px; font-weight:700; color:#64748B;
                        text-transform:uppercase; letter-spacing:0.8px;
                        margin-bottom:8px;">Status Operacional</div>
            <div style="font-size:40px; font-weight:900; color:{_fg};
                        margin-bottom:12px;">{_status_s2}</div>
            <div style="display:flex; gap:32px; flex-wrap:wrap;">
                <div>
                    <div style="font-size:10px; color:#64748B; font-weight:600;
                                text-transform:uppercase;">Planta</div>
                    <div style="font-size:16px; font-weight:700; color:{_fg};">{_planta}</div>
                </div>
                <div>
                    <div style="font-size:10px; color:#64748B; font-weight:600;
                                text-transform:uppercase;">Última Leitura</div>
                    <div style="font-size:16px; font-weight:700; color:{_fg};">{_historico_s2[-1]['horario'] if _historico_s2 else '—'}</div>
                </div>
                <div>
                    <div style="font-size:10px; color:#64748B; font-weight:600;
                                text-transform:uppercase;">Pontos no Histórico</div>
                    <div style="font-size:16px; font-weight:700; color:{_fg};">{len(_historico_s2)} h</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Sprint 2: Métricas de Tempo Real ─────────────────────────────────────────
st.markdown(
    """
    <div class='section-header'>
        <span class='section-badge'>⏱️ TEMPO REAL</span>
        <span class='section-title'>Temperatura · Vibração · Corrente — Última Leitura</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Limites operacionais Sprint 2 (alinhados com avaliar_saude).
_TEMP_CRIT, _TEMP_ALERT = 85.0, 75.0
_VIB_CRIT,  _VIB_ALERT  = 5.5,  4.5
_CORR_CRIT, _CORR_ALERT = 45,   35

# Deltas calculados via obter_ultimas_duas_leituras() — sem re-processar histórico.
_temp_prev = _prev_s2["temperatura"]
_vib_prev  = _prev_s2["vibracao"]
_corr_prev = _prev_s2["corrente"]

col_t, col_v, col_c = st.columns(3)

# Temperatura
_temp_delta = round(_temp_s2 - _temp_prev, 1)
_temp_label = "🌡️ Temperatura"
if _temp_s2 > _TEMP_CRIT:
    _temp_label += " 🔴"
    _temp_delta_color = "inverse"
elif _temp_s2 > _TEMP_ALERT:
    _temp_label += " 🟡"
    _temp_delta_color = "inverse"
else:
    _temp_delta_color = "normal"
col_t.metric(
    _temp_label,
    f"{_temp_s2:.1f} °C",
    f"{_temp_delta:+.1f} °C vs leitura anterior",
    delta_color=_temp_delta_color,
    help=(
        "Temperatura do enrolamento do motor.\n"
        "🟢 Saudável: abaixo de 75 °C\n"
        "🟡 Alerta: 75–85 °C — investigar ventilação e carga.\n"
        "🔴 Crítico: acima de 85 °C — risco de falha de isolamento."
    ),
)

# Vibração
_vib_delta = round(_vib_s2 - _vib_prev, 2)
_vib_label = "📳 Vibração"
if _vib_s2 > _VIB_CRIT:
    _vib_label += " 🔴"
    _vib_delta_color = "inverse"
elif _vib_s2 > _VIB_ALERT:
    _vib_label += " 🟡"
    _vib_delta_color = "inverse"
else:
    _vib_delta_color = "normal"
col_v.metric(
    _vib_label,
    f"{_vib_s2:.2f} mm/s",
    f"{_vib_delta:+.2f} mm/s vs leitura anterior",
    delta_color=_vib_delta_color,
    help=(
        "Vibração medida no mancal (norma ISO 10816-3).\n"
        "🟢 Saudável: abaixo de 4.5 mm/s\n"
        "🟡 Alerta: 4.5–5.5 mm/s — verificar balanceamento e rolamentos.\n"
        "🔴 Crítico: acima de 5.5 mm/s — risco de dano mecânico imediato."
    ),
)

# Corrente
_corr_delta = _corr_s2 - _corr_prev
_corr_label = "⚡ Corrente"
if _corr_s2 > _CORR_CRIT:
    _corr_label += " 🔴"
    _corr_delta_color = "inverse"
elif _corr_s2 > _CORR_ALERT:
    _corr_label += " 🟡"
    _corr_delta_color = "inverse"
else:
    _corr_delta_color = "normal"
col_c.metric(
    _corr_label,
    f"{_corr_s2} A",
    f"{_corr_delta:+d} A vs leitura anterior",
    delta_color=_corr_delta_color,
    help=(
        "Corrente de linha do motor (fase R).\n"
        "🟢 Saudável: abaixo de 35 A\n"
        "🟡 Alerta: 35–45 A — verificar sobrecarga ou desequilíbrio de fases.\n"
        "🔴 Crítico: acima de 45 A — risco de atuação do relé térmico."
    ),
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Abas de Análise (Sprint 2) ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Telemetria e Gráficos", "📊 Análise Estatística", "⚙️ Dados do Equipamento"])

# ── TAB 1: Telemetria ─────────────────────────────────────────────────────────
with tab1:
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>📈 TENDÊNCIA</span>
            <span class='section-title'>Séries Temporais — Últimas 20 Leituras</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _horas_labels = [pt["horario"]     for pt in _historico_s2]
    _temps_vals   = [pt["temperatura"] for pt in _historico_s2]
    _vibs_vals    = [pt["vibracao"]    for pt in _historico_s2]
    _corrs_vals   = [pt["corrente"]    for pt in _historico_s2]

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("<div class='chart-meta'>🌡️ <b>Temperatura (°C)</b> · Limite crítico: 85 °C</div>", unsafe_allow_html=True)
        st.line_chart([{"Temperatura (°C)": v} for v in _temps_vals], use_container_width=True, height=220, color=["#EF4444"])
    with col_g2:
        st.markdown("<div class='chart-meta'>📳 <b>Vibração (mm/s)</b> · Limite crítico: 5.5 mm/s</div>", unsafe_allow_html=True)
        st.line_chart([{"Vibração (mm/s)": v} for v in _vibs_vals], use_container_width=True, height=220, color=["#F59E0B"])
    with col_g3:
        st.markdown("<div class='chart-meta'>⚡ <b>Corrente (A)</b> · Limite crítico: 45 A</div>", unsafe_allow_html=True)
        st.line_chart([{"Corrente (A)": v} for v in _corrs_vals], use_container_width=True, height=220, color=["#1560BD"])

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>📟 SINAL BRUTO</span>
            <span class='section-title'>Leitura ADC — Valores em Bits (0 a 1023)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    import datetime as _dt
    _seed_atual = (hash(tag_sel) + int(_dt.datetime.now().second)) % (2**31)

    def _gauss_clamp(mu, sigma, lo, hi, seed):
        random.seed(seed)
        return max(lo, min(hi, random.gauss(mu, sigma)))

    def _adc_de_tensao(v_real, seed):
        bits = int((v_real / _V_REF) * _ADC_BITS)
        random.seed(seed)
        return max(0, min(_ADC_BITS, bits + int(random.gauss(0, _ADC_BITS * 0.02))))

    def _adc_de_rpm(rpm_real, seed):
        bits = int((rpm_real / _RPM_MAX) * _ADC_BITS)
        random.seed(seed)
        return max(0, min(_ADC_BITS, bits + int(random.gauss(0, _ADC_BITS * 0.015))))

    def _bits_para_volts(bits): return round((bits / _ADC_BITS) * _V_REF, 2)
    def _bits_para_rpm(bits):   return round((bits / _ADC_BITS) * _RPM_MAX, 1)

    bits_tensao_atual = _adc_de_tensao(tensao_nominal, _seed_atual)
    bits_rpm_atual    = _adc_de_rpm(rpm_nominal, _seed_atual + 1)
    volts_atual = _bits_para_volts(bits_tensao_atual)
    rpm_atual   = _bits_para_rpm(bits_rpm_atual)

    _seed_prev = (_seed_atual - 1) % (2**31)
    volts_prev = _bits_para_volts(_adc_de_tensao(tensao_nominal, _seed_prev))
    rpm_prev   = _bits_para_rpm(_adc_de_rpm(rpm_nominal, _seed_prev + 1))
    delta_volts = round(volts_atual - volts_prev, 2)
    delta_rpm   = round(rpm_atual - rpm_prev, 1)
    delta_bits_v = bits_tensao_atual - _adc_de_tensao(tensao_nominal, _seed_prev)
    delta_bits_r = bits_rpm_atual    - _adc_de_rpm(rpm_nominal, _seed_prev + 1)

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    col_b1.metric("⚡ ADC Tensão (bits)", f"{bits_tensao_atual} bits", f"{delta_bits_v:+d} bits")
    col_b2.metric("🔄 ADC RPM (bits)",    f"{bits_rpm_atual} bits",   f"{delta_bits_r:+d} bits")
    col_b3.metric("📡 Canal Ativo",        "CH-01 / CH-02",            "2 canais OK")
    col_b4.metric("🕒 Taxa de Amostragem", "1 Hz",                      "Simulado")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>🔬 GRANDEZAS FÍSICAS</span>
            <span class='section-title'>Valores Convertidos em Unidades de Engenharia</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    r_estimada = (tensao_nominal ** 2) / (potencia_kw * 1000) if potencia_kw > 0 else 1.0
    pot_estimada_w    = (volts_atual ** 2) / r_estimada
    pot_estimada_prev = (volts_prev  ** 2) / r_estimada
    delta_pot  = round((pot_estimada_w - pot_estimada_prev) / 1000, 3)
    desvio_pct = round(((volts_atual - tensao_nominal) / tensao_nominal) * 100, 2)

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("🔌 Tensão de Operação",   f"{volts_atual:.1f} V",           f"{delta_volts:+.2f} V")
    col_c2.metric("🌀 Velocidade do Eixo",    f"{rpm_atual:.0f} RPM",           f"{delta_rpm:+.1f} RPM")
    col_c3.metric("⚡ Potência Estimada",      f"{pot_estimada_w/1000:.2f} kW",  f"{delta_pot:+.3f} kW")
    col_c4.metric("📊 Desvio Tensão Nominal",  f"{desvio_pct:+.2f}%",
                  "⚠️ Fora de banda" if abs(desvio_pct) > 5 else "✅ Dentro da banda",
                  delta_color="inverse" if abs(desvio_pct) > 5 else "normal")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>📈 HISTÓRICO</span>
            <span class='section-title'>Séries Temporais — Últimas 60 Amostras</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _seed_hist = (hash(tag_sel) + int(_dt.datetime.now().minute)) % (2**31)
    random.seed(_seed_hist)
    now_dt     = _dt.datetime.now()
    timestamps = [now_dt - _dt.timedelta(seconds=(_HIST_POINTS - i)) for i in range(_HIST_POINTS)]
    drift_step = random.uniform(-2, 2) / _HIST_POINTS
    tensao_hist, rpm_hist, pot_hist_kw = [], [], []
    for i in range(_HIST_POINTS):
        v = max(0.0, min(_V_REF, tensao_nominal + random.gauss(0, tensao_nominal * 0.015) + drift_step * i))
        r = max(0.0, min(_RPM_MAX, rpm_nominal + random.gauss(0, rpm_nominal * 0.01)))
        if random.random() > 0.92:
            r = max(0.0, min(_RPM_MAX, r + random.gauss(rpm_nominal * 0.05, 10)))
        tensao_hist.append(round(v, 2))
        rpm_hist.append(round(r, 1))
        pot_hist_kw.append(round((v ** 2) / (r_estimada * 1000), 3))

    tab_v, tab_rpm, tab_pot = st.tabs(["🔌 Tensão (V)", "🌀 RPM", "⚡ Potência (kW)"])
    with tab_v:
        st.markdown(f"<div class='chart-meta'>Tensão CH-01 · Nominal: {int(tensao_nominal)} V · Desvio: {desvio_pct:+.2f}%</div>", unsafe_allow_html=True)
        st.line_chart([{"Tensão (V)": v} for v in tensao_hist], use_container_width=True, height=280, color=["#1560BD"])
    with tab_rpm:
        st.markdown(f"<div class='chart-meta'>Velocidade angular · Nominal: {int(rpm_nominal)} RPM · Última: {rpm_atual:.0f} RPM</div>", unsafe_allow_html=True)
        st.line_chart([{"RPM": v} for v in rpm_hist], use_container_width=True, height=280, color=["#2272D9"])
    with tab_pot:
        st.markdown(f"<div class='chart-meta'>Potência (Lei de Joule) · Nominal: {potencia_kw:.1f} kW · Atual: {pot_estimada_w/1000:.3f} kW</div>", unsafe_allow_html=True)
        st.line_chart([{"Potência (kW)": v} for v in pot_hist_kw], use_container_width=True, height=280, color=["#0D3B8E"])

    with st.expander("🗂️ Tabela de Dados Brutos — Últimas 60 Amostras", expanded=False):
        tabela_raw = [
            {
                "Timestamp":         timestamps[i].strftime("%H:%M:%S"),
                "ADC Tensão (bits)": _adc_de_tensao(tensao_hist[i], _seed_hist + i),
                "Tensão (V)":        tensao_hist[i],
                "ADC RPM (bits)":    _adc_de_rpm(rpm_hist[i], _seed_hist + i + 1),
                "RPM":               rpm_hist[i],
                "Potência (kW)":     pot_hist_kw[i],
            }
            for i in range(_HIST_POINTS)
        ]
        st.dataframe(tabela_raw, use_container_width=True, hide_index=True,
            column_config={
                "Timestamp":         st.column_config.TextColumn("⏱ Timestamp", width="small"),
                "ADC Tensão (bits)": st.column_config.NumberColumn("ADC Tensão (bits)", format="%d bits"),
                "Tensão (V)":        st.column_config.NumberColumn("Tensão (V)", format="%.2f V"),
                "ADC RPM (bits)":    st.column_config.NumberColumn("ADC RPM (bits)", format="%d bits"),
                "RPM":               st.column_config.NumberColumn("RPM", format="%.1f"),
                "Potência (kW)":     st.column_config.NumberColumn("Potência (kW)", format="%.3f kW"),
            })
        _buf = io.StringIO()
        _writer = csv.DictWriter(_buf, fieldnames=["Timestamp","ADC Tensão (bits)","Tensão (V)","ADC RPM (bits)","RPM","Potência (kW)"])
        _writer.writeheader(); _writer.writerows(tabela_raw)
        st.download_button("⬇️ Exportar Log CSV", _buf.getvalue().encode("utf-8"),
            file_name=f"telemetria_{tag_sel}_{now_dt.strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")


# ── TAB 2: Análise Estatística ────────────────────────────────────────────────
with tab2:
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>📊 ESTATÍSTICA</span>
            <span class='section-title'>Análise do Histórico das Últimas 20 Leituras</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _temps = [pt["temperatura"] for pt in _historico_s2]
    _vibs  = [pt["vibracao"]    for pt in _historico_s2]
    _corrs = [pt["corrente"]    for pt in _historico_s2]

    # Estatísticas — Python puro sem numpy/pandas
    def _stats(lst):
        return {
            "min":   min(lst),
            "max":   max(lst),
            "media": round(sum(lst) / len(lst), 2),
            "amp":   round(max(lst) - min(lst), 2),
        }

    st_temp = _stats(_temps)
    st_vib  = _stats(_vibs)
    st_corr = _stats([float(c) for c in _corrs])

    # Tendência: compara média da primeira e segunda metade do histórico
    def _tendencia(lst):
        mid  = len(lst) // 2
        m1   = sum(lst[:mid]) / max(mid, 1)
        m2   = sum(lst[mid:]) / max(len(lst) - mid, 1)
        diff = m2 - m1
        if diff > 2:   return "📈 Crescente", "inverse"
        if diff < -2:  return "📉 Decrescente", "normal"
        return "➡️ Estável", "off"

    tend_temp, tend_temp_color = _tendencia(_temps)
    tend_vib,  tend_vib_color  = _tendencia(_vibs)
    tend_corr, tend_corr_color = _tendencia([float(c) for c in _corrs])

    st.subheader("🌡️ Temperatura (°C)")
    ct1, ct2, ct3, ct4 = st.columns(4)
    ct1.metric("Mínima",   f"{st_temp['min']:.1f} °C")
    ct2.metric("Máxima",   f"{st_temp['max']:.1f} °C",
               "⚠️ Acima do alerta" if st_temp['max'] > 75 else "✅ Normal",
               delta_color="inverse" if st_temp['max'] > 75 else "normal")
    ct3.metric("Média",    f"{st_temp['media']:.1f} °C")
    ct4.metric("Tendência", tend_temp, delta_color=tend_temp_color)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📳 Vibração (mm/s)")
    cv1, cv2, cv3, cv4 = st.columns(4)
    cv1.metric("Mínima",   f"{st_vib['min']:.2f} mm/s")
    cv2.metric("Máxima",   f"{st_vib['max']:.2f} mm/s",
               "⚠️ Acima do alerta" if st_vib['max'] > 4.5 else "✅ Normal",
               delta_color="inverse" if st_vib['max'] > 4.5 else "normal")
    cv3.metric("Média",    f"{st_vib['media']:.2f} mm/s")
    cv4.metric("Tendência", tend_vib, delta_color=tend_vib_color)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚡ Corrente (A)")
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Mínima",   f"{st_corr['min']:.0f} A")
    cc2.metric("Máxima",   f"{st_corr['max']:.0f} A",
               "⚠️ Acima do alerta" if st_corr['max'] > 35 else "✅ Normal",
               delta_color="inverse" if st_corr['max'] > 35 else "normal")
    cc3.metric("Média",    f"{st_corr['media']:.1f} A")
    cc4.metric("Tendência", tend_corr, delta_color=tend_corr_color)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>🔎 DIAGNÓSTICO</span>
            <span class='section-title'>Resumo Automático de Rastreabilidade</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Pontos acima dos limites de alerta
    _pts_temp_alerta   = sum(1 for t in _temps if t > 75)
    _pts_temp_crit     = sum(1 for t in _temps if t > 85)
    _pts_vib_alerta    = sum(1 for v in _vibs  if v > 4.5)
    _pts_vib_crit      = sum(1 for v in _vibs  if v > 5.5)
    _total             = len(_historico_s2)

    diag_col1, diag_col2 = st.columns(2)
    with diag_col1:
        st.markdown(
            f"""
            <div style="background:#F7FAFF;border:1px solid #DBEAFE;border-left:4px solid #1560BD;
                        border-radius:8px;padding:16px 20px;">
                <div style="font-weight:700;color:#0D3B8E;margin-bottom:8px;">🌡️ Temperatura</div>
                <div style="font-size:13px;color:#4A5568;line-height:1.8;">
                    Amplitude: <b>{st_temp['amp']:.1f} °C</b><br>
                    Leituras em Alerta (>75°C): <b>{_pts_temp_alerta}/{_total}</b><br>
                    Leituras Críticas (>85°C): <b>{_pts_temp_crit}/{_total}</b><br>
                    Tendência: <b>{tend_temp}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with diag_col2:
        st.markdown(
            f"""
            <div style="background:#F7FAFF;border:1px solid #DBEAFE;border-left:4px solid #F59E0B;
                        border-radius:8px;padding:16px 20px;">
                <div style="font-weight:700;color:#0D3B8E;margin-bottom:8px;">📳 Vibração</div>
                <div style="font-size:13px;color:#4A5568;line-height:1.8;">
                    Amplitude: <b>{st_vib['amp']:.2f} mm/s</b><br>
                    Leituras em Alerta (>4.5 mm/s): <b>{_pts_vib_alerta}/{_total}</b><br>
                    Leituras Críticas (>5.5 mm/s): <b>{_pts_vib_crit}/{_total}</b><br>
                    Tendência: <b>{tend_vib}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── TAB 3: Dados do Equipamento ───────────────────────────────────────────────
with tab3:
    st.markdown(
        """
        <div class='section-header'>
            <span class='section-badge'>⚙️ CADASTRO</span>
            <span class='section-title'>Ficha Técnica do Equipamento</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_img3, col_dados3 = st.columns([1, 2])
    with col_img3:
        st.image(
            ativo.get("imagem_placa", "https://via.placeholder.com/300x150.png?text=Placa"),
            caption=f"Placa de Identificação — {ativo['Modelo']}",
            use_container_width=True,
        )
    with col_dados3:
        st.markdown(
            f"""
            <div style="background:#F7FAFF;border:1px solid #DBEAFE;border-radius:10px;padding:24px 28px;">
                <div style="font-size:22px;font-weight:800;color:#0D3B8E;margin-bottom:16px;">
                    {ativo['TAG']} &nbsp;<span style="font-size:14px;font-weight:400;color:#64748B;">{ativo['Modelo']}</span>
                </div>
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <tr><td style="color:#64748B;padding:6px 0;width:40%;">🏭 Fabricante</td>
                        <td style="font-weight:700;color:#0D3B8E;">{ativo['Fabricante']}</td></tr>
                    <tr><td style="color:#64748B;padding:6px 0;">⚡ Potência Nominal</td>
                        <td style="font-weight:700;color:#0D3B8E;">{potencia_kw:.1f} kW</td></tr>
                    <tr><td style="color:#64748B;padding:6px 0;">🔌 Tensão Nominal</td>
                        <td style="font-weight:700;color:#0D3B8E;">{int(tensao_nominal)} V</td></tr>
                    <tr><td style="color:#64748B;padding:6px 0;">📍 Planta</td>
                        <td style="font-weight:700;color:#0D3B8E;">{ativo.get('planta', '—')}</td></tr>
                    <tr><td style="color:#64748B;padding:6px 0;">🌀 RPM Estimado</td>
                        <td style="font-weight:700;color:#0D3B8E;">{int(rpm_nominal)} RPM</td></tr>
                    <tr><td style="color:#64748B;padding:6px 0;">🏷️ TAG</td>
                        <td style="font-weight:700;color:#0D3B8E;">{ativo['TAG']}</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("⚡ Potência",  f"{potencia_kw:.1f} kW")
    cm2.metric("🔌 Tensão",    f"{int(tensao_nominal)} V")
    cm3.metric("🏭 Fabricante", ativo['Fabricante'])
# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; color:#A0AEC0; font-size:11px;
                padding-top:16px; border-top:1px solid #E2E8F0; margin-top:24px;">
        Gestão de Ativos · Monitoramento · Sprint 1 / Sprint 2 · mock_db + random (stdlib)
    </div>
    """,
    unsafe_allow_html=True,
)
