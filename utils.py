"""
utils.py
--------
Utilitários compartilhados entre todas as páginas da aplicação.

Decisão de arquitetura:
    O Streamlit reexecuta o script completo de cada página a cada
    interação do usuário. CSS e conteúdo de sidebar injetados apenas
    em app.py não sobrevivem ao ciclo de rerun das páginas filhas.

    aplicar_design_fixo_sidebar() resolve esse problema renderizando
    tanto o CSS quanto o conteúdo da sidebar (card azul + status +
    navegação) em cada página, garantindo persistência total do design
    independente de qual página está ativa ou qual widget foi acionado.
"""

import datetime
import streamlit as st


def aplicar_estilo_ui() -> None:
    """
    Mantida por compatibilidade. Internamente delega para
    aplicar_design_fixo_sidebar(), que já inclui toda a sanitização.
    """
    aplicar_design_fixo_sidebar()


def aplicar_design_fixo_sidebar() -> None:
    """
    Injeta o CSS global de sanitização + design Dark Tech e renderiza
    o conteúdo completo da sidebar (card de identidade, status, navegação).

    Deve ser chamada imediatamente após st.set_page_config() em cada
    arquivo de página. A função faz duas coisas em sequência:

    1. st.markdown → injeta o bloco <style> com todos os seletores
       de sanitização do framework e o design visual da sidebar.
    2. with st.sidebar → renderiza o card azul, os badges de status
       e os links de navegação.

    Renderizar o conteúdo da sidebar aqui (e não só o CSS) é a única
    forma confiável de garantir persistência: o Streamlit sobrescreve
    o conteúdo da sidebar a cada rerun, então ela precisa ser
    reconstruída em cada ciclo de execução de cada página.
    """

    # ── 1. CSS Global ────────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
        /* ── Sanitização do framework ─────────────────────────────────── */
        /* [data-testid="stHeader"]       { display: none !important; } */
        [data-testid="stBottom"],
        footer                         { display: none !important; }
        #MainMenu                      { display: none !important; }
        [data-testid="stSidebarHeader"]{ display: none !important; }
        .block-container               { padding-top: 1.5rem !important; }

        /* ── Sidebar — estrutura geral ────────────────────────────────── */
        [data-testid="stSidebar"] {
            background-color: #111113 !important;
            border-right: 1px solid rgba(124, 58, 237, 0.20) !important;
            padding: 0 !important;
        }
        [data-testid="stSidebarContent"] {
            padding: 1.2rem 1rem !important;
        }

        /* ── Card de identidade (azul vibrante) ───────────────────────── */
        .sb-card {
            background: linear-gradient(135deg, #1A3FBF 0%, #1560BD 60%, #2272D9 100%);
            border-radius: 14px;
            padding: 18px 16px 14px 16px;
            text-align: center;
            margin-bottom: 18px;
            box-shadow: 0 4px 18px rgba(21, 96, 189, 0.35);
        }
        .sb-card-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            line-height: 1.3;
        }
        .sb-card-sub {
            color: rgba(255,255,255,0.75);
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.8px;
            margin-top: 5px;
            text-transform: uppercase;
        }

        /* ── Badges de status ─────────────────────────────────────────── */
        .sb-status-label {
            color: #9CA3AF;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin: 14px 0 8px 2px;
        }
        .sb-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #1E1E22;
            border: 1px solid #2E2E35;
            border-radius: 20px;
            padding: 6px 14px;
            margin-bottom: 6px;
            font-size: 12px;
            font-weight: 500;
            color: #E4E4E7;
        }
        .sb-dot-green  { color: #34D399; font-size: 10px; }
        .sb-dot-yellow { color: #FBBF24; font-size: 10px; }

        /* ── Divider ──────────────────────────────────────────────────── */
        .sb-divider {
            border: none;
            border-top: 1px solid #2E2E35;
            margin: 14px 0;
        }

        /* ── Label de seção ───────────────────────────────────────────── */
        .sb-section-label {
            color: #6B7280;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin: 0 0 6px 2px;
        }

        /* ── Links de navegação (st.page_link) ───────────────────────── */
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarContent"] a {
            border-radius: 8px !important;
            padding: 9px 12px !important;
            margin-bottom: 2px !important;
            color: #D1D5DB !important;
            font-size: 13px !important;
            display: flex !important;
            align-items: center !important;
            transition: background 0.15s ease !important;
        }
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarContent"] a:hover {
            background: rgba(124, 58, 237, 0.12) !important;
            color: #FFFFFF !important;
        }

        /* ── Info de ambiente ─────────────────────────────────────────── */
        .sb-env {
            color: #6B7280;
            font-size: 10px;
            line-height: 1.8;
            margin-top: 4px;
            padding-left: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. Conteúdo da Sidebar ───────────────────────────────────────────────
    # Renderizado aqui (e não só em app.py) para garantir que o Streamlit
    # reconstrua a sidebar a cada rerun de qualquer página.
    now_str = datetime.datetime.now().strftime("%H:%M · %d/%m/%Y")

    with st.sidebar:

        # Card de identidade azul
        st.markdown(
            """
            <div class="sb-card">
                <div class="sb-card-title">Gestão de Ativos</div>
                <div class="sb-card-sub">Challenge Sprint 1 · FIAP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status do sistema
        st.markdown(
            f"""
            <div class="sb-status-label">Status do Sistema</div>

            <div class="sb-badge">
                <span class="sb-dot-green">●</span> Serviço Online
            </div>
            <div class="sb-badge">
                <span class="sb-dot-green">●</span> Banco de Dados OK
            </div>
            <div class="sb-badge">
                <span class="sb-dot-yellow">●</span> API — Modo Mock
            </div>

            <div style="color:#6B7280; font-size:10px; margin: 6px 0 0 4px;">
                Última verificação: {now_str}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

        # Navegação
        st.markdown("<div class='sb-section-label'>Navegação</div>", unsafe_allow_html=True)
        st.page_link("app.py",                             label="🏠  Home")
        st.page_link("pages/1_📊_Dashboard_Ativos.py",    label="📊  Dashboard de Ativos")
        st.page_link("pages/2_➕_Novo_Cadastro.py",       label="➕  Novo Cadastro")
        st.page_link("pages/3_📈_Monitoramento.py",       label="📈  Monitoramento")

        st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

        # Informações de ambiente
        st.markdown(
            """
            <div class="sb-section-label">Ambiente</div>
            <div class="sb-env">
                🔖 Sprint 1 &nbsp;·&nbsp; v0.1.0<br>
                🏗️ Stack: Streamlit + Python puro<br>
                🔗 Backend: Mock (FastAPI em breve)
            </div>
            """,
            unsafe_allow_html=True,
        )
