"""
app.py
------
Shell global da aplicação Streamlit — Challenge Sprint 1.

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
    page_title="Gestão de Ativos | Challenge Sprint 1",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**Gestão de Ativos** · Challenge Sprint 1 · FIAP · 2026",
    },
)

# ── 2. Inicialização do Banco de Dados ───────────────────────────────────────
# init_db é invocado no shell e não dentro das páginas individuais porque
# o Streamlit não garante a ordem de execução das páginas em caso de
# navegação direta via URL. Centralizando aqui, toda sessão tem estado
# válido antes que qualquer rota seja resolvida.
if _backend_ok:
    init_db()

# ── 2.1 Sanitização do Framework ─────────────────────────────────────────────
# Remove elementos nativos do Streamlit que expõem o framework ao usuário
# final: header fixo, rodapé "Made with Streamlit" e menu hambúrguer.
# Os seletores são baseados em data-testid estáveis entre versões minor;
# verificar em atualizações de versão major do Streamlit.
st.markdown(
    """
    <style>
    /* Header fixo superior */
    [data-testid="stHeader"] { display: none !important; }

    /* Rodapé "Made with Streamlit" */
    [data-testid="stBottom"], footer { display: none !important; }

    /* Menu hambúrguer superior direito */
    #MainMenu { display: none !important; }

    /* Título nativo "app" no topo da sidebar gerado pelo Streamlit */
    [data-testid="stSidebarHeader"] { display: none !important; }

    /* Compensa o espaço do header removido */
    .block-container { padding-top: 1.5rem !important; }

    /* Divider sutil entre sidebar e área de conteúdo */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(124, 58, 237, 0.25) !important;
    }

    /* Espaçamento aumentado nos itens de navegação (st.page_link) */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarContent"] a {
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        display: block !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

    /* --- Cards de Módulo --- */
    .module-card {
        background: #FFFFFF;
        border: 1px solid #DBEAFE;
        border-left: 4px solid #1560BD;
        border-radius: 10px;
        padding: 20px 22px;
        height: 100%;
        transition: box-shadow 0.2s;
    }
    .module-card:hover { box-shadow: 0 4px 18px rgba(21,96,189,0.12); }
    .module-card h4  { color: #0D3B8E; font-size: 15px; margin-bottom: 6px; }
    .module-card p   { color: #4A5568; font-size: 13px; line-height: 1.6; margin: 0; }
    .module-icon     { font-size: 28px; margin-bottom: 10px; }

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
# A sidebar é renderizada explicitamente aqui para garantir consistência
# visual em todas as páginas. O Streamlit herda o conteúdo da sidebar do
# app.py em cada navegação, eliminando a necessidade de duplicar o bloco
# em cada arquivo de /pages.
with st.sidebar:

    # 4.1  Identidade Visual — substitui o título nativo "app" do Streamlit
    st.markdown(
        """
        <div class="logo-block">
            <div class="logo-title">GESTÃO DE ATIVOS</div>
            <div class="logo-subtitle">Challenge Sprint 1 · FIAP</div>
        </div>
        """,
        unsafe_allow_html=True,
)

    st.markdown("---")

    # 4.2  Indicadores de Status do Sistema
    st.markdown("**Status do Sistema**")

    now_str = datetime.datetime.now().strftime("%H:%M · %d/%m/%Y")

    st.markdown(
        f"""
        <div class="status-badge">
            <span class="dot-online">●</span> Serviço Online
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Última verificação: {now_str}")

    st.markdown(
        """
        <div class="status-badge" style="margin-top:6px">
            <span class="dot-online">●</span> Banco de Dados OK
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-badge" style="margin-top:6px">
            <span class="dot-warning">●</span> API Externa — Modo Mock
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 4.3  Navegação (atalhos para as páginas /pages)
    st.markdown("**Navegação**")
    st.page_link("app.py",                             label="🏠 Home"               )
    st.page_link("pages/1_📊_Dashboard_Ativos.py", label="📊 Dashboard de Ativos"  )
    st.page_link("pages/2_➕_Novo_Cadastro.py",    label="➕ Novo Cadastro"         )
    st.page_link("pages/3_📈_Monitoramento.py",    label="📈 Monitoramento"         )

    st.markdown("---")

    # 4.4  Informações de Ambiente
    st.markdown("**Ambiente**")
    st.caption("🔖 Sprint 1 — v0.1.0")
    st.caption("🏗️ Stack: Streamlit + Pandas")
    st.caption("🔗 Backend: Mock (FastAPI em breve)")


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
                     color:#7C3AED; font-weight:600;">Challenge Sprint 1 · FIAP</span>
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
        <div class="hero-eyebrow">Challenge Sprint 1 · FIAP</div>
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
total   = len(df) if df is not None else 0
fab_u   = df["Fabricante"].nunique() if df is not None else 0
pot_med = f'{df["Potência (kW)"].mean():.1f} kW' if df is not None and total > 0 else "—"

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("⚙️ Ativos Cadastrados", total)
col_m2.metric("🏭 Fabricantes",         fab_u)
col_m3.metric("⚡ Potência Média",       pot_med)
col_m4.metric("📡 Status API",           "Mock Ativo")

st.markdown("---")

# Cards de módulos disponíveis
st.subheader("Módulos da Plataforma")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div class="module-card">
            <div class="module-icon">🔩</div>
            <h4>Cadastro de Ativos</h4>
            <p>Registre novos equipamentos com TAG única, dados de fabricante,
            potência e tensão nominal. Validação em tempo real.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="module-card">
            <div class="module-icon">📋</div>
            <h4>Lista de Ativos</h4>
            <p>Visualize, filtre e exporte o inventário completo de
            equipamentos cadastrados. Tabela interativa com busca dinâmica.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="module-card">
            <div class="module-icon">📡</div>
            <h4>Integração FastAPI</h4>
            <p>Arquitetura preparada para substituir o mock por chamadas REST
            reais ao backend FastAPI sem alterar o frontend.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Rodapé
st.markdown(
    f"""
    <div class="footer">
        Gestão de Ativos · Challenge Sprint 1 · FIAP · v0.1.0 ·
        {datetime.date.today().strftime("%Y")}
    </div>
    """,
    unsafe_allow_html=True,
)
