"""
app.py
------
Shell global da aplicação Streamlit — Challenge Sprint 2.

Decisão de arquitetura:
    Este arquivo age como ponto de entrada único por duas razões:
    1. O runtime do Streamlit exige que set_page_config seja a primeira
       chamada de cada script. Como o mecanismo de /pages executa
       app.py antes de qualquer página, centralizar a configuração
       aqui previne inconsistências de layout entre rotas.
    2. init_db() precisa rodar uma única vez por sessão antes que
       qualquer página tente acessar o estado. O shell garante essa
       ordem de inicialização sem acoplamento entre as páginas.
"""

import datetime
import traceback
import streamlit as st

from utils import aplicar_design_fixo_sidebar, kpi_card, section_header, PALETTE

# Import guard: pandas/numpy podem falhar por política de DLL no Windows.
# O bloco try/except isola o crash no shell, permitindo que o CSS de
# sanitização e a sidebar renderizem antes de qualquer mensagem de erro.
_backend_ok = True
_backend_error: Exception | None = None
_backend_traceback: str = ""

try:
    from backend.mock_db import init_db
except Exception as _exc:
    _backend_ok = False
    _backend_error = _exc
    _backend_traceback = traceback.format_exc()

# ── 1. Configuração da Página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Ativos | Challenge Sprint 2",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**Gestão de Ativos** · Challenge Sprint 2 · FIAP · 2026",
    },
)

# Injeta CSS global + renderiza sidebar completa (card, status, nav).
# Chamada antes de init_db para garantir que o design esteja presente
# mesmo que o backend falhe logo em seguida.
aplicar_design_fixo_sidebar()
# init_db é invocado no shell e não dentro das páginas individuais porque
# o Streamlit não garante a ordem de execução das páginas em caso de
# navegação direta via URL. Centralizando aqui, toda sessão tem estado
# válido antes que qualquer rota seja resolvida.
if _backend_ok:
    init_db()



# ── 3. CSS Global Inline ─────────────────────────────────────────────────────
# Complementa o config.toml com ajustes finos que o tema não expõe.
st.markdown(
    """
    <style>
    /* --- Sidebar Dark Tech --- */
    [data-testid="stSidebar"] {
        background-color: #18181B;
    }
    [data-testid="stSidebar"] * {
        color: #E4E4E7 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(124,58,237,0.3);
    }

    /* --- Bloco de Logo --- */
    .logo-block {
        background: linear-gradient(135deg, #1560BD 0%, #0D3B8E 100%);
        border: 1px solid #2272D9;
        border-radius: 10px;
        padding: 18px 16px 14px;
        text-align: center;
        margin-bottom: 4px;
    }
    .logo-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
        color: #FFFFFF !important;
        text-transform: uppercase;
    }
    .logo-subtitle {
        font-size: 10px;
        letter-spacing: 2px;
        color: #90CAF9 !important;
        text-transform: uppercase;
    }

    /* --- Badge de Status --- */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 500;
        width: 100%;
        justify-content: center;
    }
    .dot-online  { color: #69F0AE; font-size: 10px; }
    .dot-warning { color: #FFD740; font-size: 10px; }

    /* --- Hero da Landing Page --- */
    .hero-container {
        background: linear-gradient(135deg, #0D3B8E 0%, #1560BD 60%, #2272D9 100%);
        border-radius: 16px;
        padding: 56px 48px;
        color: #FFFFFF;
        position: relative;
        overflow: hidden;
    }
    .hero-container::after {
        content: "⚙";
        position: absolute;
        right: 40px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 120px;
        opacity: 0.08;
    }
    .hero-eyebrow {
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #90CAF9;
        margin-bottom: 8px;
    }
    .hero-title {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: 16px;
    }
    .hero-lead {
        font-size: 16px;
        color: #BBDEFB;
        max-width: 540px;
        line-height: 1.7;
    }

    /* --- Rodapé --- */
    .footer {
        text-align: center;
        color: #A0AEC0;
        font-size: 11px;
        padding-top: 12px;
        border-top: 1px solid #E2E8F0;
        margin-top: 32px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 4. Sidebar ───────────────────────────────────────────────────────────────
# Renderizada via utils.aplicar_design_fixo_sidebar() chamada acima.


# ── 5. Contenção de Erros de Backend ────────────────────────────────────────
# Exibido antes do corpo principal para que o utilizador de negócio
# veja uma mensagem limpa; o traceback técnico fica contido no expander.
if not _backend_ok:
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
                ⚠️ Não foi possível carregar os módulos técnicos da plataforma
            </div>
            <div style="color:#FCA5A5; font-size:12px; margin-top:4px;">
                O serviço de dados está indisponível nesta sessão.
                Verifique o ambiente de execução e reinicie a aplicação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("🔧 Exibir Detalhes Técnicos do Erro", expanded=False):
        st.code(_backend_traceback, language="python")
    st.stop()

# ── 6. Corpo Principal — Landing Page ────────────────────────────────────────

# Título de página com divisor visual
st.markdown(
    """
    <div style="margin-bottom: 4px;">
        <span style="font-size:11px; letter-spacing:3px; text-transform:uppercase;
                     color:#7C3AED; font-weight:600;">Challenge Sprint 2 · FIAP</span>
        <h1 style="font-size:26px; font-weight:800; margin:4px 0 0 0; color:#E4E4E7;">
            Plataforma de Gestão de Ativos
        </h1>
    </div>
    <hr style="border:none; border-top:1px solid rgba(124,58,237,0.25); margin:12px 0 24px 0;">
    """,
    unsafe_allow_html=True,
)

# Hero
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-eyebrow">Challenge Sprint 2 · FIAP</div>
        <div class="hero-title">Plataforma de<br>Gestão de Ativos</div>
        <div class="hero-lead">
            Centralize o cadastro técnico dos seus equipamentos industriais.
            Rastreie TAG, modelo, fabricante, potência e tensão com
            precisão e agilidade — tudo em um único lugar.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# Métricas rápidas (dados do session_state)
# session_state é lido diretamente aqui, sem chamar get_equipamentos(),
# porque a landing page exibe apenas um resumo superficial. Evitar a
# função pública preserva a semântica de que get_equipamentos() é
# exclusivo de páginas que consomem o DataFrame completo.

df = st.session_state.get("equipamentos_db")

# Cálculos com Python puro — sem pandas.
# Mantém zero-dependency do projeto (ver README, seção Decisão Técnica).
if df and isinstance(df, list) and len(df) > 0:
    total   = len(df)
    fab_u   = len(set(eq["Fabricante"] for eq in df))
    pot_med = f'{sum(eq["Potência (kW)"] for eq in df) / total:.1f} kW'
else:
    total   = 0
    fab_u   = 0
    pot_med = "—"

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    kpi_card("⚙️ Ativos Cadastrados", str(total), accent=PALETTE.brand_primary,
             hint="equipamentos no sistema")
with col_m2:
    kpi_card("🏭 Fabricantes", str(fab_u), accent=PALETTE.info,
             hint="fabricantes distintos")
with col_m3:
    kpi_card("⚡ Potência Média", pot_med, accent=PALETTE.alert,
             hint="kW por equipamento")
with col_m4:
    kpi_card("📡 Status API", "Mock Ativo", accent=PALETTE.safe,
             hint="FastAPI em breve")

st.markdown("<br>", unsafe_allow_html=True)

# Módulos da plataforma
section_header("Módulos da Plataforma", subtitle="Navegue pelo menu lateral")

c1, c2, c3 = st.columns(3)

_card_style = (
    f"background:{PALETTE.bg_elevated};"
    f"border:1px solid {PALETTE.border};"
    f"border-left:4px solid {{accent}};"
    "border-radius:10px;padding:20px 22px;height:100%;"
)

with c1:
    st.markdown(
        f'<div style="{_card_style.format(accent=PALETTE.brand_primary)}">'
        '<div style="font-size:28px;margin-bottom:10px">🔩</div>'
        f'<h4 style="color:{PALETTE.text_primary};font-size:15px;margin-bottom:6px">Cadastro de Ativos</h4>'
        f'<p style="color:{PALETTE.text_secondary};font-size:13px;line-height:1.6;margin:0">'
        'Registre novos equipamentos com TAG única, dados de fabricante, '
        'potência e tensão nominal. Validação em tempo real.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div style="{_card_style.format(accent=PALETTE.info)}">'
        '<div style="font-size:28px;margin-bottom:10px">📋</div>'
        f'<h4 style="color:{PALETTE.text_primary};font-size:15px;margin-bottom:6px">Dashboard de Ativos</h4>'
        f'<p style="color:{PALETTE.text_secondary};font-size:13px;line-height:1.6;margin:0">'
        'Visualize, filtre e exporte o inventário completo. '
        'KPIs por planta com status de saúde operacional em tempo real.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div style="{_card_style.format(accent=PALETTE.alert)}">'
        '<div style="font-size:28px;margin-bottom:10px">📡</div>'
        f'<h4 style="color:{PALETTE.text_primary};font-size:15px;margin-bottom:6px">Monitoramento</h4>'
        f'<p style="color:{PALETTE.text_secondary};font-size:13px;line-height:1.6;margin:0">'
        'Telemetria em tempo real com gráficos Plotly, alertas críticos, '
        'OCR de placa e séries históricas por TAG.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

# Rodapé
st.markdown(
    f"""
    <div class="footer">
        Gestão de Ativos · Challenge Sprint 2 · FIAP · v0.1.0 ·
        {datetime.date.today().strftime("%Y")}
    </div>
    """,
    unsafe_allow_html=True,
)
