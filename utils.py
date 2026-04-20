"""
utils.py
--------
Utilitários compartilhados entre todas as páginas da aplicação.

Decisão de arquitetura:
    O Streamlit reexecuta o script completo de cada página a cada
    interação do usuário (clique de botão, seleção de widget etc.).
    CSS injetado em app.py não é herdado pelas páginas filhas nesse
    ciclo de reexecução. Centralizar a injeção em uma função chamada
    em cada página garante que os seletores de sanitização do framework
    sejam aplicados de forma consistente em toda a navegação,
    independente de qual página está ativa.
"""

import streamlit as st


def aplicar_estilo_ui() -> None:
    """
    Injeta o CSS global de sanitização do framework Streamlit.

    Deve ser chamada imediatamente após st.set_page_config() em cada
    arquivo de página. A ordem importa: o Streamlit processa os blocos
    de CSS na ordem em que são injetados no DOM; chamar antes de qualquer
    outro st.markdown garante que os seletores tenham a maior
    especificidade possível.

    Seletores cobertos:
        - [data-testid="stHeader"]       → header fixo superior
        - [data-testid="stBottom"]       → rodapé "Made with Streamlit"
        - footer                         → fallback do rodapé em versões antigas
        - #MainMenu                      → menu hambúrguer superior direito
        - [data-testid="stSidebarHeader"]→ título nativo "app" da sidebar
        - .block-container               → compensa o gap do header removido
        - [data-testid="stSidebar"]      → divider roxo lateral
        - links de navegação da sidebar  → espaçamento entre itens de menu
    """
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

        /* Compensa o espaço do header removido para evitar gap no topo */
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
