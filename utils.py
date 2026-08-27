"""
utils.py
--------
Design system, componentes reutilizáveis e sidebar da aplicação.

Sprint 3 — novidades:
    - Sidebar: badge de alertas ativos (vermelho) visível em todas as páginas.
    - render_sparkline(): mini gráfico Plotly de tendência para o painel de alertas.
    - alert_card(): card de alerta com NLP, botão de reconhecimento e link de monitoramento.
    - recommendation_card(): card de ação de manutenção por urgência.
    - event_row(): linha do log de histórico de eventos.
"""

import datetime
import html as _html
import streamlit as st


# ── Paleta de cores central ───────────────────────────────────────────────────
class _Palette:
    bg_primary   = "#0F0F11"
    bg_surface   = "#18181B"
    bg_elevated  = "#1E1E22"
    border       = "#2E2E35"
    text_primary   = "#E4E4E7"
    text_secondary = "#9CA3AF"
    text_muted     = "#6B7280"
    critical = "#EF4444"
    alert    = "#F59E0B"
    safe     = "#34D399"
    info     = "#5AC8FA"
    brand_primary   = "#1560BD"
    brand_secondary = "#2272D9"
    brand_accent    = "#7C3AED"


PALETTE = _Palette()


def cor_por_status(status: str) -> str:
    if "Crítico" in status:
        return PALETTE.critical
    if "Alerta" in status:
        return PALETTE.alert
    return PALETTE.safe


# ── Componentes Sprint 1 & 2 ─────────────────────────────────────────────────

def kpi_card(label, value, accent=None, delta=None, hint=None):
    accent = accent or PALETTE.brand_primary
    parts = [
        f'<div class="ga-kpi" style="--ga-accent:{accent}">',
        f'<div class="ga-kpi-label">{label}</div>',
        f'<div class="ga-kpi-value">{value}</div>',
    ]
    if delta:
        sign_color = (
            PALETTE.safe if delta.strip().startswith(("+", "↑"))
            else PALETTE.critical if delta.strip().startswith(("-", "↓"))
            else PALETTE.text_secondary
        )
        parts.append(f'<div class="ga-kpi-delta" style="color:{sign_color}">{delta}</div>')
    if hint:
        parts.append(f'<div class="ga-kpi-hint">{hint}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def status_card(status, tag=None):
    color = cor_por_status(status)
    hint_text = f"Ativo: {tag}" if tag else None
    kpi_card("🩺 Saúde Operacional", status, accent=color, hint=hint_text)


def section_header(title, subtitle=None, accent=None):
    accent = accent or PALETTE.brand_primary
    parts = [
        '<div class="ga-section-header">',
        f'<div class="ga-section-bar" style="background:{accent}"></div>',
        f'<h3 class="ga-section-title">{title}</h3>',
    ]
    if subtitle:
        parts.append(f'<div class="ga-section-sub">{subtitle}</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ── CSS global ────────────────────────────────────────────────────────────────

_GLOBAL_CSS = f"""
<style>
[data-testid="stBottom"], footer {{ display: none !important; }}
#MainMenu {{ display: none !important; }}
[data-testid="stSidebarHeader"]{{ display: none !important; }}
.block-container {{ padding-top: 1.5rem !important; }}

[data-testid="stSidebar"] {{
    background-color: #111113 !important;
    border-right: 1px solid rgba(124, 58, 237, 0.20) !important;
    padding: 0 !important;
}}
[data-testid="stSidebarContent"] {{ padding: 1.2rem 1rem !important; }}

.sb-card {{
    background: linear-gradient(135deg, #1A3FBF 0%, {PALETTE.brand_primary} 60%, {PALETTE.brand_secondary} 100%);
    border-radius: 14px; padding: 18px 16px 14px 16px;
    text-align: center; margin-bottom: 18px;
    box-shadow: 0 4px 18px rgba(21, 96, 189, 0.35);
}}
.sb-card-title {{
    color: #FFFFFF; font-size: 15px; font-weight: 800;
    letter-spacing: 1.5px; text-transform: uppercase; line-height: 1.3;
}}
.sb-card-sub {{
    color: rgba(255,255,255,0.75); font-size: 10px;
    font-weight: 500; letter-spacing: 0.8px; margin-top: 5px; text-transform: uppercase;
}}
.sb-alert-badge {{
    display: inline-block;
    background: {PALETTE.critical};
    color: #fff;
    font-size: 11px; font-weight: 800;
    border-radius: 99px;
    padding: 2px 9px;
    margin-left: 6px;
    vertical-align: middle;
    animation: pulse 1.5s infinite;
}}
@keyframes pulse {{
    0%   {{ opacity: 1; }}
    50%  {{ opacity: 0.6; }}
    100% {{ opacity: 1; }}
}}
.sb-status-label {{
    color: {PALETTE.text_secondary}; font-size: 10px; font-weight: 600;
    letter-spacing: 1.2px; text-transform: uppercase; margin: 14px 0 8px 2px;
}}
.sb-badge {{
    display: flex; align-items: center; gap: 8px;
    background: {PALETTE.bg_elevated}; border: 1px solid {PALETTE.border};
    border-radius: 20px; padding: 6px 14px; margin-bottom: 6px;
    font-size: 12px; font-weight: 500; color: {PALETTE.text_primary};
}}
.sb-dot-green  {{ color: {PALETTE.safe};     font-size: 10px; }}
.sb-dot-yellow {{ color: {PALETTE.alert};    font-size: 10px; }}
.sb-dot-red    {{ color: {PALETTE.critical}; font-size: 10px; }}
.sb-divider {{ border: none; border-top: 1px solid {PALETTE.border}; margin: 14px 0; }}
.sb-section-label {{
    color: {PALETTE.text_muted}; font-size: 10px; font-weight: 700;
    letter-spacing: 1.4px; text-transform: uppercase; margin: 0 0 6px 2px;
}}
.sb-env {{ color: {PALETTE.text_muted}; font-size: 10px; line-height: 1.8; margin-top: 4px; padding-left: 2px; }}

.ga-kpi {{
    background: linear-gradient(135deg, {PALETTE.bg_surface} 0%, {PALETTE.bg_elevated} 100%);
    border: 1px solid {PALETTE.border}; border-radius: 12px;
    padding: 16px 18px; height: 100%; position: relative; overflow: hidden; margin-bottom: 2px;
}}
.ga-kpi::before {{
    content: ""; position: absolute; top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--ga-accent, {PALETTE.brand_primary});
    border-radius: 2px 0 0 2px;
}}
.ga-kpi-label {{ color: {PALETTE.text_secondary}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 6px; }}
.ga-kpi-value {{ color: {PALETTE.text_primary}; font-size: 1.65rem; font-weight: 800; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.ga-kpi-delta {{ font-size: 0.78rem; margin-top: 5px; font-weight: 500; }}
.ga-kpi-hint  {{ color: {PALETTE.text_muted}; font-size: 0.68rem; margin-top: 5px; }}

.ga-section-header {{ display: flex; align-items: center; gap: 10px; margin: 16px 0 12px 0; }}
.ga-section-bar {{ width: 4px; height: 20px; border-radius: 2px; flex-shrink: 0; }}
.ga-section-title {{ margin: 0; color: {PALETTE.text_primary}; font-size: 1.05rem; font-weight: 700; }}
.ga-section-sub {{ color: {PALETTE.text_secondary}; font-size: 0.8rem; margin-left: auto; }}

.js-plotly-plot .plotly {{ background: transparent !important; }}
</style>
"""


# ── Inicialização principal ───────────────────────────────────────────────────

def aplicar_estilo_ui() -> None:
    aplicar_design_fixo_sidebar()


def aplicar_design_fixo_sidebar() -> None:
    """Injeta CSS global e renderiza sidebar com badge de alertas ativos."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

    # Conta alertas via função pública do backend (evita acesso direto a chave privada)
    from backend.mock_db import contar_alertas_ativos
    criticos, total_nao_reconh = contar_alertas_ativos()

    badge_html = ""
    if criticos > 0:
        badge_html = f'<span class="sb-alert-badge">🔴 {criticos}</span>'
    elif total_nao_reconh > 0:
        badge_html = f'<span class="sb-alert-badge" style="background:{PALETTE.alert}">{total_nao_reconh}</span>'

    now_str = datetime.datetime.now().strftime("%H:%M · %d/%m/%Y")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sb-card">
                <div class="sb-card-title">Gestão de Ativos{badge_html}</div>
                <div class="sb-card-sub">Challenge Sprint 3 · FIAP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status do sistema com indicador de alertas
        dot_alertas = "sb-dot-red" if criticos > 0 else ("sb-dot-yellow" if total_nao_reconh > 0 else "sb-dot-green")
        txt_alertas = f"🚨 {total_nao_reconh} Alerta(s) Ativo(s)" if total_nao_reconh > 0 else "✔ Sem Alertas Ativos"

        st.markdown(
            f"""
            <div class="sb-status-label">Status do Sistema</div>
            <div class="sb-badge"><span class="sb-dot-green">●</span> Serviço Online</div>
            <div class="sb-badge"><span class="sb-dot-green">●</span> Banco de Dados OK</div>
            <div class="sb-badge"><span class="sb-dot-yellow">●</span> API — Modo Mock</div>
            <div class="sb-badge"><span class="{dot_alertas}">●</span> {txt_alertas}</div>
            <div style="color:{PALETTE.text_muted};font-size:10px;margin:6px 0 0 4px;">
                Última verificação: {now_str}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="sb-section-label">Ambiente</div>
            <div class="sb-env">
                🔖 Sprint 3 &nbsp;·&nbsp; v0.3.0<br>
                🏗️ Stack: Streamlit + Python puro<br>
                🔗 Backend: Mock (FastAPI em breve)<br>
                💾 Persistência: JSON local
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Sprint 3 — Componentes do Painel de Alertas ──────────────────────────────

def render_sparkline(valores: list[float], cor: str, altura: int = 80):
    """
    Mini gráfico Plotly de tendência (sparkline) para cards de alerta.

    Args:
        valores : lista de floats (ex: temperaturas das últimas N leituras).
        cor     : cor hex da linha e preenchimento.
        altura  : altura em px do gráfico. Padrão: 80.
    """
    import plotly.graph_objects as go

    if not valores:
        return

    # Converte hex (#RRGGBB) para rgba — Plotly não aceita hex de 8 dígitos
    def _hex_to_rgba(hex_color: str, alpha: float = 0.13) -> str:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=valores,
        mode="lines",
        fill="tozeroy",
        fillcolor=_hex_to_rgba(cor),
        line=dict(color=cor, width=1.5),
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=altura,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def alert_card(
    tag, modelo, planta, status_raw, temperatura, vibracao,
    timestamp, resumo_nlp, reconhecido=False, alerta_id="",
    telemetria=None,
):
    """
    Card de alerta operacional com resumo NLP, sparkline de tendência,
    botão de reconhecimento e link de navegação para monitoramento.

    Returns:
        "reconhecer" se o botão de reconhecimento foi clicado.
        "monitorar"  se o botão de monitoramento foi clicado.
        None         caso contrário.
    """
    cor = cor_por_status(status_raw)
    ts  = timestamp.strftime("%d/%m/%Y %H:%M") if hasattr(timestamp, "strftime") else str(timestamp)
    opacidade = "0.5" if reconhecido else "1"
    badge_extra = "  ✔ Reconhecido" if reconhecido else ""
    # Escape de campos vindos do formulário para evitar injeção de HTML
    tag_s    = _html.escape(str(tag))
    modelo_s = _html.escape(str(modelo))
    planta_s = _html.escape(str(planta))

    st.markdown(
        f"""
        <div style="
            border-left: 5px solid {cor};
            background: linear-gradient(135deg, {PALETTE.bg_surface} 0%, {PALETTE.bg_elevated} 100%);
            border: 1px solid {PALETTE.border};
            border-left: 5px solid {cor};
            border-radius: 10px;
            padding: 16px 20px 10px 20px;
            margin-bottom: 4px;
            opacity: {opacidade};
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
                <span style="font-size:1.05rem; font-weight:800; color:{cor};">{tag_s}</span>
                <span style="font-size:0.78rem; color:{PALETTE.text_muted};">{ts} &nbsp;·&nbsp; {planta_s}</span>
            </div>
            <div style="font-size:0.87rem; color:{PALETTE.text_secondary}; margin-bottom:8px;">{modelo_s}</div>
            <div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:10px; align-items:center;">
                <span style="font-size:0.88rem; color:{PALETTE.text_secondary};">
                    🌡️ <b style="color:{cor}">{temperatura:.1f} °C</b>
                </span>
                <span style="font-size:0.88rem; color:{PALETTE.text_secondary};">
                    📳 <b style="color:{cor}">{vibracao:.2f} mm/s</b>
                </span>
                <span style="font-size:0.8rem; padding:3px 12px; border-radius:99px;
                             background:{cor}22; color:{cor}; font-weight:700;">
                    {status_raw}{badge_extra}
                </span>
            </div>
            <div style="font-size:0.87rem; color:{PALETTE.text_primary};
                        background:rgba(0,0,0,0.3); border-radius:8px;
                        padding:10px 14px; line-height:1.6; border-left:3px solid {cor}44;">
                {resumo_nlp}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Linha de ações: sparkline | botões
    col_spark, col_btns = st.columns([3, 2])

    with col_spark:
        if telemetria:
            render_sparkline(telemetria, cor, altura=70)

    with col_btns:
        resultado = None
        if not reconhecido and alerta_id:
            b1, b2 = st.columns(2)
            with b1:
                if st.button(f"✔ Reconhecer", key=f"ack_{alerta_id}", width='stretch'):
                    resultado = "reconhecer"
            with b2:
                if st.button(f"📈 Monitorar", key=f"mon_{alerta_id}", width='stretch'):
                    resultado = "monitorar"
        elif reconhecido:
            if st.button(f"📈 Ver {tag_s}", key=f"mon_r_{alerta_id}", width='stretch'):
                resultado = "monitorar"

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    return resultado


def recommendation_card(acao, detalhe, icone="🔧", urgente=False):
    """Card de recomendação de manutenção."""
    cor_topo = PALETTE.critical if urgente else PALETTE.brand_primary
    st.markdown(
        f"""
        <div style="border:1px solid {PALETTE.border}; border-top:3px solid {cor_topo};
                    background:{PALETTE.bg_elevated}; border-radius:8px;
                    padding:14px 16px; margin-bottom:8px;">
            <div style="font-size:0.95rem; font-weight:700; color:{PALETTE.text_primary}; margin-bottom:4px;">
                {icone} {acao}
            </div>
            <div style="font-size:0.83rem; color:{PALETTE.text_secondary}; line-height:1.5;">
                {detalhe}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def event_row(timestamp, tag, evento, status_raw, temp, vib):
    """Linha do histórico de eventos com cor semântica."""
    cor     = cor_por_status(status_raw)
    ts      = timestamp.strftime("%d/%m %H:%M") if hasattr(timestamp, "strftime") else str(timestamp)
    tag_s   = _html.escape(str(tag))
    evento_s = _html.escape(str(evento))
    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns:110px 80px 1fr 130px 80px 90px;
                    gap:8px; align-items:center; padding:7px 12px;
                    border-bottom:1px solid {PALETTE.border}; font-size:0.81rem;">
            <span style="color:{PALETTE.text_muted};">{ts}</span>
            <span style="font-weight:700; color:{PALETTE.text_primary};">{tag_s}</span>
            <span style="color:{PALETTE.text_secondary};">{evento_s}</span>
            <span style="color:{cor}; font-weight:600;">{status_raw}</span>
            <span style="color:{PALETTE.text_secondary};">🌡️ {temp:.1f} °C</span>
            <span style="color:{PALETTE.text_secondary};">📳 {vib:.2f} mm/s</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
