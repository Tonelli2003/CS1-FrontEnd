"""
pages/3_📈_Monitoramento.py
----------------------------
Tela de Monitoramento de Telemetria — Challenge Sprint 2.

Estrutura:
    - Seletor de TAG (com navegação cruzada via st.session_state['tag_navegacao'])
    - Cabeçalho de métricas em tempo real (Temperatura, Vibração, Corrente + deltas)
    - Alerta de saúde visível quando status for Crítico ou Alerta
    - st.tabs com três abas:
        1. 📈 Séries Temporais  — gráficos históricos
        2. 👁️ Visão Computacional — imagem da placa + dados OCR simulados
        3. ⚙️ Ficha Técnica      — dados cadastrais estáticos

Restrições: Python puro — sem pandas, sem numpy.
"""

import datetime
import streamlit as st
import plotly.graph_objects as go

from utils import aplicar_design_fixo_sidebar, kpi_card, status_card, section_header, PALETTE
from backend.mock_db import (
    init_db,
    get_equipamentos,
    obter_telemetria_historica,
    obter_ultimas_duas_leituras,
    avaliar_saude,
)

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitoramento | Challenge Sprint 2",
    page_icon="📈",
    layout="wide",
)
aplicar_design_fixo_sidebar()
init_db()

# ── CSS da página ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #0D3B8E; }
    [data-testid="stSidebar"] * { color: #E8F0FE !important; }

    .page-header {
        background: linear-gradient(135deg, #0A2F6B 0%, #0D3B8E 50%, #1560BD 100%);
        border-radius: 12px; padding: 28px 36px; margin-bottom: 4px;
        position: relative; overflow: hidden;
    }
    .page-header::after {
        content: "📡"; position: absolute; right: 32px; top: 50%;
        transform: translateY(-50%); font-size: 80px; opacity: 0.10;
    }
    .page-header h1 { color:#fff; font-size:28px; font-weight:800; margin:0 0 6px 0; }
    .page-header p  { color:#BBDEFB; font-size:14px; margin:0; }

    [data-testid="stMetric"] {
        background:#fff; border:1px solid #DBEAFE;
        border-top:4px solid #1560BD; border-radius:10px;
        padding:16px 20px !important;
        box-shadow:0 2px 8px rgba(21,96,189,0.07);
    }
    [data-testid="stMetricLabel"] { color:#4A5568 !important; font-size:12px !important; }
    [data-testid="stMetricValue"] { color:#0D3B8E !important; font-size:26px !important; font-weight:800 !important; }

    .asset-bar {
        background:#F7FAFF; border:1px solid #DBEAFE;
        border-left:4px solid #1560BD; border-radius:8px;
        padding:12px 20px; margin:12px 0;
        display:flex; gap:28px; flex-wrap:wrap; align-items:center;
    }
    .asset-bar-item { display:flex; flex-direction:column; }
    .asset-bar-label { color:#64748B; font-size:10px; font-weight:600;
                       text-transform:uppercase; letter-spacing:.7px; }
    .asset-bar-value { color:#0D3B8E; font-size:15px; font-weight:700; }

    .section-divider { border:none; border-top:1px solid #E2E8F0; margin:20px 0; }

    .ocr-card {
        background:#F0F9FF; border:1px solid #BAE6FD;
        border-left:4px solid #0EA5E9; border-radius:10px; padding:20px 24px;
    }
    .ocr-label { color:#0369A1; font-size:11px; font-weight:700;
                 text-transform:uppercase; letter-spacing:.8px; margin-bottom:4px; }
    .ocr-value { color:#0C4A6E; font-size:14px; font-weight:600; }
    .ocr-raw   { font-family:monospace; background:#E0F2FE; border-radius:6px;
                 padding:10px 14px; color:#0C4A6E; font-size:13px;
                 margin-top:6px; word-break:break-word; }

    .ficha-row { display:flex; gap:0; flex-wrap:wrap; margin-bottom:12px; }
    .ficha-cell {
        flex:1; min-width:150px;
        background:#F7FAFF; border:1px solid #DBEAFE;
        border-radius:8px; padding:14px 18px; margin:4px;
    }
    .ficha-cell-label { color:#64748B; font-size:11px; font-weight:600;
                        text-transform:uppercase; letter-spacing:.7px; }
    .ficha-cell-value { color:#0D3B8E; font-size:20px; font-weight:800; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
        <h1>Monitoramento de Telemetria</h1>
        <p>Selecione um ativo para inspecionar leituras em tempo real simulado,
           análise de visão computacional e ficha técnica.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Carrega equipamentos ──────────────────────────────────────────────────────
lista_eq: list[dict] = get_equipamentos()

if not lista_eq:
    st.warning(
        "⚠️ **Nenhum equipamento cadastrado.**\n\n"
        "Acesse **➕ Novo Cadastro** para registrar ativos."
    )
    st.stop()

# ── Seletor com navegação cruzada ─────────────────────────────────────────────
tags_list = [eq["TAG"] for eq in lista_eq]

_default_index = 0
if "tag_navegacao" in st.session_state:
    _tag_nav = st.session_state.pop("tag_navegacao")
    if _tag_nav in tags_list:
        _default_index = tags_list.index(_tag_nav)

col_sel, col_live = st.columns([4, 1])
with col_sel:
    tag_sel = st.selectbox(
        "Selecione o equipamento para monitorar:",
        options=tags_list,
        index=_default_index,
        key="monitoramento_tag_sel",
        help="TAG do ativo cadastrado no sistema.",
    )
with col_live:
    st.markdown("<br>", unsafe_allow_html=True)
    now_str = datetime.datetime.now().strftime("%H:%M:%S · %d/%m/%Y")
    st.markdown(
        f"""
        <div style="display:inline-flex;align-items:center;gap:6px;
                    background:rgba(105,240,174,0.12);border:1px solid rgba(105,240,174,.35);
                    border-radius:20px;padding:6px 14px;font-size:12px;
                    font-weight:600;color:#1B5E20;">
            ● LIVE &nbsp;·&nbsp; {now_str}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Ativo selecionado ─────────────────────────────────────────────────────────
ativo: dict = next(eq for eq in lista_eq if eq["TAG"] == tag_sel)
tensao_nominal = float(ativo["Tensão (V)"])
potencia_kw    = float(ativo["Potência (kW)"])

# Barra de info do ativo
st.markdown(
    f"""
    <div class="asset-bar">
        <div class="asset-bar-item">
            <span class="asset-bar-label">🏷️ TAG</span>
            <span class="asset-bar-value">{ativo['TAG']}</span>
        </div>
        <div class="asset-bar-item">
            <span class="asset-bar-label">🔩 Modelo</span>
            <span class="asset-bar-value">{ativo['Modelo']}</span>
        </div>
        <div class="asset-bar-item">
            <span class="asset-bar-label">🏭 Fabricante</span>
            <span class="asset-bar-value">{ativo['Fabricante']}</span>
        </div>
        <div class="asset-bar-item">
            <span class="asset-bar-label">📍 Planta</span>
            <span class="asset-bar-value">{ativo.get('planta', '—')}</span>
        </div>
        <div class="asset-bar-item">
            <span class="asset-bar-label">⚡ Potência</span>
            <span class="asset-bar-value">{potencia_kw:.1f} kW</span>
        </div>
        <div class="asset-bar-item">
            <span class="asset-bar-label">🔌 Tensão</span>
            <span class="asset-bar-value">{int(tensao_nominal)} V</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Telemetria: métricas + deltas ─────────────────────────────────────────────
historico   = obter_telemetria_historica(tag_sel, num_leituras=20)
atual, prev = obter_ultimas_duas_leituras(tag_sel)
status      = avaliar_saude(atual["temperatura"], atual["vibracao"])

# ── Alerta de saúde ───────────────────────────────────────────────────────────
if status == "🔴 Crítico":
    st.error(
        f"🚨 **ALERTA CRÍTICO — {tag_sel}** | "
        f"Temperatura: **{atual['temperatura']:.1f} °C** · "
        f"Vibração: **{atual['vibracao']:.2f} mm/s** — "
        "Parâmetros fora dos limites operacionais. Intervenção imediata necessária."
    )
    st.toast(f"⚠️ {tag_sel}: Estado Crítico detectado!", icon="🚨")
elif status == "🟡 Alerta":
    st.warning(
        f"⚠️ **ALERTA — {tag_sel}** | "
        f"Temperatura: **{atual['temperatura']:.1f} °C** · "
        f"Vibração: **{atual['vibracao']:.2f} mm/s** — "
        "Parâmetros em faixa de atenção. Monitoramento reforçado recomendado."
    )

# Métricas com delta (último vs penúltimo ponto do histórico)
_TEMP_CRIT, _TEMP_ALERT = 85.0, 75.0
_VIB_CRIT,  _VIB_ALERT  = 5.5,  4.5
_CORR_CRIT, _CORR_ALERT = 45,   35

temp_delta = round(atual["temperatura"] - prev["temperatura"], 1)
vib_delta  = round(atual["vibracao"]    - prev["vibracao"],    2)
corr_delta = atual["corrente"] - prev["corrente"]

temp_label = "🌡️ Temperatura"
vib_label  = "📳 Vibração"
corr_label = "⚡ Corrente"
if atual["temperatura"] > _TEMP_CRIT:  temp_label += " 🔴"
elif atual["temperatura"] > _TEMP_ALERT: temp_label += " 🟡"
if atual["vibracao"] > _VIB_CRIT:     vib_label  += " 🔴"
elif atual["vibracao"] > _VIB_ALERT:  vib_label  += " 🟡"
if atual["corrente"]  > _CORR_CRIT:   corr_label += " 🔴"
elif atual["corrente"] > _CORR_ALERT: corr_label += " 🟡"

col_t, col_v, col_c, col_s = st.columns(4)

# Determina acento por criticidade — PALETTE garante mesma cor em todo o sistema
def _accent_temp(t):
    return PALETTE.critical if t > _TEMP_CRIT else PALETTE.alert if t > _TEMP_ALERT else PALETTE.safe

def _accent_vib(v):
    return PALETTE.critical if v > _VIB_CRIT else PALETTE.alert if v > _VIB_ALERT else PALETTE.safe

def _accent_corr(c):
    return PALETTE.critical if c > _CORR_CRIT else PALETTE.alert if c > _CORR_ALERT else PALETTE.safe

with col_t:
    kpi_card(
        "🌡️ Temperatura",
        f"{atual['temperatura']:.1f} °C",
        accent=_accent_temp(atual["temperatura"]),
        delta=f"{temp_delta:+.1f} °C vs anterior",
        hint=f"Crítico: {_TEMP_CRIT} °C · Alerta: {_TEMP_ALERT} °C",
    )
with col_v:
    kpi_card(
        "📳 Vibração",
        f"{atual['vibracao']:.2f} mm/s",
        accent=_accent_vib(atual["vibracao"]),
        delta=f"{vib_delta:+.2f} mm/s vs anterior",
        hint=f"Crítico: {_VIB_CRIT} mm/s · Alerta: {_VIB_ALERT} mm/s",
    )
with col_c:
    kpi_card(
        "⚡ Corrente",
        f"{atual['corrente']} A",
        accent=_accent_corr(atual["corrente"]),
        delta=f"{corr_delta:+d} A vs anterior",
        hint=f"Crítico: {_CORR_CRIT} A · Alerta: {_CORR_ALERT} A",
    )
with col_s:
    status_card(status, tag=tag_sel)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Abas ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(
    ["📈 Séries Temporais", "👁️ Visão Computacional", "⚙️ Ficha Técnica"]
)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 1 — Séries Temporais
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("##### 📈 Histórico das Últimas 20 Leituras")
    st.caption(
        f"Equipamento **{tag_sel}** · Última leitura: **{atual['horario']}** · "
        f"Status: **{status}**"
    )

    temps = [pt["temperatura"] for pt in historico]
    vibs  = [pt["vibracao"]    for pt in historico]
    corrs = [pt["corrente"]    for pt in historico]
    horas = [pt["horario"]     for pt in historico]

    # Cor da série: semântica pelo status atual do ativo
    _status_color = (
        PALETTE.critical if "Crítico" in status
        else PALETTE.alert if "Alerta" in status
        else PALETTE.safe
    )

    # Layout base reutilizado nos dois gráficos Plotly desta aba.
    # xaxis e yaxis ficam FORA do base para evitar TypeError de kwarg duplicado
    # quando update_layout recebe **_PLOTLY_BASE + yaxis=... explícito.
    _PLOTLY_BASE = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PALETTE.text_primary, size=11),
        margin=dict(l=10, r=10, t=36, b=10),
        legend=dict(
            bgcolor="rgba(30,30,34,0.85)",
            bordercolor=PALETTE.border,
            borderwidth=1,
        ),
    )

    # ── Gráfico 1: Temperatura + Vibração (duplo eixo Y) ────────────────────
    section_header(
        "Temperatura & Vibração",
        subtitle="Barras = °C (eixo esq.) · Linha = mm/s (eixo dir.)",
        accent=_status_color,
    )

    fig_tv = go.Figure()
    fig_tv.add_trace(go.Bar(
        x=horas, y=temps,
        name="Temperatura (°C)",
        marker_color=_status_color,
        opacity=0.55,
        hovertemplate="<b>%{x}</b><br>Temperatura: %{y:.1f} °C<extra></extra>",
    ))
    fig_tv.add_trace(go.Scatter(
        x=horas, y=vibs,
        name="Vibração (mm/s)",
        mode="lines+markers",
        line=dict(color=PALETTE.alert, width=2.5),
        marker=dict(size=5),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Vibração: %{y:.2f} mm/s<extra></extra>",
    ))
    fig_tv.add_hline(
        y=_TEMP_CRIT, line_dash="dot",
        line_color=PALETTE.critical, line_width=1.2,
        annotation_text=f"Crítico {_TEMP_CRIT}°C",
        annotation_font_color=PALETTE.critical, annotation_font_size=10,
    )
    fig_tv.add_hline(
        y=_TEMP_ALERT, line_dash="dot",
        line_color=PALETTE.alert, line_width=1,
        annotation_text=f"Alerta {_TEMP_ALERT}°C",
        annotation_font_color=PALETTE.alert, annotation_font_size=10,
    )
    fig_tv.update_layout(
        **_PLOTLY_BASE,
        xaxis=dict(gridcolor=PALETTE.border, zerolinecolor=PALETTE.border,
                   tickfont=dict(color=PALETTE.text_secondary)),
        yaxis=dict(title="Temperatura (°C)", gridcolor=PALETTE.border,
                   tickfont=dict(color=PALETTE.text_secondary)),
        yaxis2=dict(title="Vibração (mm/s)", overlaying="y", side="right",
                    showgrid=False, tickfont=dict(color=PALETTE.alert)),
        hovermode="x unified",
        height=320,
        barmode="overlay",
    )
    st.plotly_chart(fig_tv, width="stretch", theme=None)

    # ── Gráfico 2: Corrente elétrica (área preenchida) ───────────────────────
    section_header(
        "Corrente Elétrica",
        subtitle="Série histórica em Amperes · área = acumulado de carga",
        accent=PALETTE.brand_primary,
    )
    fig_c = go.Figure()
    fig_c.add_trace(go.Scatter(
        x=horas, y=corrs,
        name="Corrente (A)",
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(21,96,189,0.12)",
        line=dict(color=PALETTE.brand_primary, width=2.5),
        marker=dict(size=5, color=PALETTE.brand_primary),
        hovertemplate="<b>%{x}</b><br>Corrente: %{y} A<extra></extra>",
    ))
    fig_c.add_hline(
        y=_CORR_CRIT, line_dash="dot",
        line_color=PALETTE.critical, line_width=1.2,
        annotation_text=f"Crítico {_CORR_CRIT} A",
        annotation_font_color=PALETTE.critical, annotation_font_size=10,
    )
    fig_c.add_hline(
        y=_CORR_ALERT, line_dash="dot",
        line_color=PALETTE.alert, line_width=1,
        annotation_text=f"Alerta {_CORR_ALERT} A",
        annotation_font_color=PALETTE.alert, annotation_font_size=10,
    )
    fig_c.update_layout(
        **_PLOTLY_BASE,
        xaxis=dict(gridcolor=PALETTE.border, zerolinecolor=PALETTE.border,
                   tickfont=dict(color=PALETTE.text_secondary)),
        yaxis=dict(title="Corrente (A)", gridcolor=PALETTE.border,
                   tickfont=dict(color=PALETTE.text_secondary)),
        hovermode="x unified",
        height=280,
    )
    st.plotly_chart(fig_c, width="stretch", theme=None)

    # ── Estatísticas do período — Python puro (mantidas sem alteração) ───────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("##### 📊 Estatísticas do Período")

    def _stats(lst):
        n = len(lst)
        return {"min": min(lst), "max": max(lst), "media": sum(lst) / n}

    st_t = _stats(temps)
    st_v = _stats(vibs)
    st_c = _stats([float(c) for c in corrs])

    st.subheader("🌡️ Temperatura")
    c_t1, c_t2, c_t3 = st.columns(3)
    c_t1.metric("Mínima",  f"{st_t['min']:.1f} °C")
    c_t2.metric("Média",   f"{st_t['media']:.1f} °C")
    c_t3.metric("Máxima",  f"{st_t['max']:.1f} °C")

    st.write("")
    st.subheader("📳 Vibração")
    c_v1, c_v2, c_v3 = st.columns(3)
    c_v1.metric("Mínima",  f"{st_v['min']:.1f}")
    c_v2.metric("Média",   f"{st_v['media']:.1f}")
    c_v3.metric("Máxima",  f"{st_v['max']:.1f}")

    st.write("")
    st.subheader("⚡ Corrente")
    c_c1, c_c2, c_c3 = st.columns(3)
    c_c1.metric("Mínima",  f"{st_c['min']:.1f} A")
    c_c2.metric("Média",   f"{st_c['media']:.1f} A")
    c_c3.metric("Máxima",  f"{st_c['max']:.1f} A")


# ─────────────────────────────────────────────────────────────────────────────
# ABA 2 — Visão Computacional
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("##### 👁️ Leitura Automática da Placa por IA (OCR Simulado)")
    st.caption(
        "Os dados abaixo simulam o retorno de um modelo de visão computacional "
        "que capturou e interpretou a placa de identificação física do equipamento."
    )

    ocr: dict = ativo.get("dados_ocr", {})
    img_url   = ativo.get(
        "imagem_placa",
        "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Sem+Imagem",
    )

    col_img, col_ocr = st.columns([1, 2])

    with col_img:
        st.image(img_url, caption=f"Placa — {ativo['Modelo']}", width='stretch')
        st.markdown(
            f"""
            <div style="text-align:center;margin-top:8px;">
                <span style="background:#0EA5E9;color:#fff;border-radius:20px;
                             padding:4px 14px;font-size:12px;font-weight:700;">
                    🤖 IA · OCR Ativo
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ocr:
        if not ocr:
            st.info("ℹ️ Dados de OCR não disponíveis para este equipamento.")
        else:
            conf = ocr.get("confiabilidade", 0.0)
            texto = ocr.get("texto_extraido", "—")
            data  = ocr.get("data_leitura", "—")

            # Cor da barra de confiabilidade
            if conf >= 0.97:
                conf_color, conf_label = "#16A34A", "Alta"
            elif conf >= 0.94:
                conf_color, conf_label = "#D97706", "Média"
            else:
                conf_color, conf_label = "#DC2626", "Baixa"

            conf_pct = int(conf * 100)

            html_box = f"""<div class="ocr-card">
<div style="margin-bottom:16px;">
<div class="ocr-label">🎯 Confiabilidade do Modelo</div>
<div style="display:flex;align-items:center;gap:12px;margin-top:6px;">
<div style="flex:1;background:#E0F2FE;border-radius:20px;height:10px;">
<div style="width:{conf_pct}%;background:{conf_color};border-radius:20px;height:10px;transition:width .4s ease;"></div>
</div>
<span style="font-size:20px;font-weight:800;color:{conf_color};">{conf_pct}%</span>
<span style="font-size:12px;font-weight:600;color:{conf_color};">{conf_label}</span>
</div>
</div>
<div style="margin-bottom:16px;">
<div class="ocr-label">📅 Data da Leitura</div>
<div class="ocr-value">{data}</div>
</div>
<div>
<div class="ocr-label">📝 Texto Extraído pela IA</div>
<div class="ocr-raw">{texto}</div>
</div>
</div>"""
            st.markdown(html_box, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA 3 — Ficha Técnica
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("##### ⚙️ Dados Cadastrais do Equipamento")
    st.caption("Informações estáticas registradas no sistema de gestão de ativos.")

    rpm_nominal = 3600.0 if potencia_kw >= 50 else 1800.0

    st.markdown(
        f"""
        <div style="background:#F7FAFF;border:1px solid #DBEAFE;border-radius:12px;
                    padding:24px 28px;margin-bottom:20px;">
            <div style="font-size:24px;font-weight:800;color:#0D3B8E;margin-bottom:6px;">
                {ativo['TAG']}
                <span style="font-size:14px;font-weight:400;color:#64748B;margin-left:10px;">
                    {ativo['Modelo']}
                </span>
            </div>
            <div style="font-size:12px;color:#64748B;">
                Status atual: <b>{status}</b>
            </div>
        </div>

        <div class="ficha-row">
            <div class="ficha-cell">
                <div class="ficha-cell-label">🏭 Fabricante</div>
                <div class="ficha-cell-value">{ativo['Fabricante']}</div>
            </div>
            <div class="ficha-cell">
                <div class="ficha-cell-label">📍 Planta</div>
                <div class="ficha-cell-value">{ativo.get('planta', '—')}</div>
            </div>
            <div class="ficha-cell">
                <div class="ficha-cell-label">⚡ Potência Nominal</div>
                <div class="ficha-cell-value">{potencia_kw:.1f} kW</div>
            </div>
            <div class="ficha-cell">
                <div class="ficha-cell-label">🔌 Tensão Nominal</div>
                <div class="ficha-cell-value">{int(tensao_nominal)} V</div>
            </div>
            <div class="ficha-cell">
                <div class="ficha-cell-label">🌀 RPM Estimado</div>
                <div class="ficha-cell-value">{int(rpm_nominal)} RPM</div>
            </div>
            <div class="ficha-cell">
                <div class="ficha-cell-label">🏷️ TAG</div>
                <div class="ficha-cell-value">{ativo['TAG']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Métricas de resumo
    st.markdown("<br>", unsafe_allow_html=True)
    cm1, cm2, cm3, cm4 = st.columns(4)
    cm1.metric("⚡ Potência",  f"{potencia_kw:.1f} kW")
    cm2.metric("🔌 Tensão",    f"{int(tensao_nominal)} V")
    cm3.metric("🌀 RPM",       f"{int(rpm_nominal)}")
    cm4.metric("🏭 Fabricante", ativo["Fabricante"])


# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;color:#A0AEC0;font-size:11px;
                padding-top:16px;border-top:1px solid #E2E8F0;margin-top:24px;">
        Gestão de Ativos · Monitoramento · Sprint 2 · mock_db + stdlib Python
    </div>
    """,
    unsafe_allow_html=True,
)
