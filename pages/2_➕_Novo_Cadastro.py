"""
pages/2_➕_Novo_Cadastro.py
---------------------------
Módulo de Cadastro Técnico de Ativos Industriais — Challenge Sprint 1.

Decisões de arquitetura:
    - st.form encapsula todos os inputs para que o Streamlit só dispare
      um rerun ao pressionar o botão de submit, evitando que a validação
      seja executada a cada tecla digitada pelo usuário.
    - A validação e a persistência ficam fora do bloco `with st.form`
      porque st.spinner e st.markdown não podem ser chamados de dentro
      de um form antes do submit ser processado.
    - clear_on_submit=True limpa os campos após persistência bem-sucedida,
      prevenindo resubmissão acidental do mesmo equipamento.
"""

import streamlit as st
from backend.mock_db import init_db, adicionar_equipamento

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Novo Cadastro | Challenge Sprint 1",
    page_icon="➕",
    layout="wide",
)

# ── Inicialização do banco ────────────────────────────────────────────────────
init_db()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar corporativa */
    [data-testid="stSidebar"] { background-color: #0D3B8E; }
    [data-testid="stSidebar"] * { color: #E8F0FE !important; }
    [data-testid="stSidebar"] hr { border-color: #1A4FAD; }

    /* Cabeçalho da página */
    .page-header {
        background: linear-gradient(135deg, #064E3B 0%, #065F46 55%, #047857 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .page-header::after {
        content: "➕";
        position: absolute;
        right: 32px; top: 50%;
        transform: translateY(-50%);
        font-size: 80px;
        opacity: 0.10;
    }
    .page-header h1 { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 0 0 6px 0; }
    .page-header p  { color: #A7F3D0; font-size: 14px; margin: 0; max-width: 520px; }

    /* Card do formulário */
    .form-card {
        background: #FFFFFF;
        border: 1px solid #D1FAE5;
        border-radius: 12px;
        padding: 32px 36px;
        box-shadow: 0 4px 20px rgba(6,78,59,0.06);
    }

    /* Seção interna */
    .form-section-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #059669;
        margin-bottom: 8px;
        display: block;
    }

    /* Inputs — borda accent ao focar */
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #059669 !important;
        box-shadow: 0 0 0 2px rgba(5,150,105,0.15) !important;
    }

    /* Botão de submit */
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #047857, #059669) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 36px !important;
        width: 100%;
        transition: opacity 0.2s !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        opacity: 0.88 !important;
    }

    /* Painel lateral de regras */
    .rules-card {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 4px solid #059669;
        border-radius: 10px;
        padding: 20px 22px;
        font-size: 13px;
        color: #1A202C;
        line-height: 1.8;
    }
    .rules-card h4 {
        color: #047857;
        font-size: 13px;
        font-weight: 700;
        margin: 0 0 10px 0;
    }
    .rules-card li { margin-left: 14px; }

    /* Banner de sucesso customizado */
    .success-banner {
        background: linear-gradient(135deg, #D1FAE5, #ECFDF5);
        border: 1px solid #6EE7B7;
        border-left: 5px solid #059669;
        border-radius: 10px;
        padding: 20px 24px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        margin-top: 8px;
        animation: slideIn 0.35s ease;
    }
    .success-icon { font-size: 32px; line-height: 1; }
    .success-title { font-weight: 800; color: #064E3B; font-size: 16px; }
    .success-body  { color: #047857; font-size: 13px; margin-top: 4px; line-height: 1.6; }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Divider */
    .sec-div {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 20px 0 16px;
    }

    /* Rodapé */
    .footer {
        text-align:center; color:#A0AEC0; font-size:11px;
        padding-top:12px; border-top:1px solid #E2E8F0; margin-top:32px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
        <h1>Novo Cadastro de Ativo</h1>
        <p>
            Preencha os dados técnicos do equipamento. Todos os campos são
            obrigatórios. A TAG deve ser única no sistema.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Layout: formulário (esquerda) + regras (direita) ─────────────────────────
col_form, col_rules = st.columns([3, 1], gap="large")

with col_rules:
    st.markdown(
        """
        <div class="rules-card">
            <h4>📋 Regras de Preenchimento</h4>
            <ul>
                <li><b>TAG</b>: formato sugerido <code>EQ-XXX</code></li>
                <li><b>Potência</b>: valor em kW, mínimo 0,1</li>
                <li><b>Tensão</b>: valor em V, mínimo 1</li>
                <li>Campos em branco serão rejeitados</li>
                <li>TAGs duplicadas devem ser evitadas</li>
            </ul>
            <br>
            <h4>⚙️ Padrões Aceitos</h4>
            <ul>
                <li>Tensão: 127 V · 220 V · 380 V · 440 V</li>
                <li>Potência: 0,75 kW a 1000 kW</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_form:
    # ── Formulário ────────────────────────────────────────────────────────────
    with st.form("cadastro_form", clear_on_submit=True):

        # — Seção 1: Identificação ————————————————————————————————————————
        st.markdown("<span class='form-section-label'>Identificação do Equipamento</span>", unsafe_allow_html=True)

        col_tag, col_modelo = st.columns([1, 2])
        with col_tag:
            tag = st.text_input(
                label="TAG *",
                placeholder="EQ-003",
                help="Identificador único. Ex: EQ-003, BOMB-001",
                max_chars=20,
            )
        with col_modelo:
            modelo = st.text_input(
                label="Modelo *",
                placeholder="Ex: Motor WEG W22 IE3",
                help="Modelo completo conforme plaqueta do fabricante.",
                max_chars=80,
            )

        fabricante = st.text_input(
            label="Fabricante *",
            placeholder="Ex: WEG, KSB, Atlas Copco, Siemens…",
            help="Nome oficial do fabricante.",
            max_chars=60,
        )

        st.markdown("<hr class='sec-div'>", unsafe_allow_html=True)

        # — Seção 2: Dados Elétricos ——————————————————————————————————————
        st.markdown("<span class='form-section-label'>Dados Elétricos Nominais</span>", unsafe_allow_html=True)

        col_pot, col_tensao = st.columns(2)
        with col_pot:
            potencia = st.number_input(
                label="Potência Nominal (kW) *",
                min_value=0.1,
                max_value=10_000.0,
                value=15.0,
                step=0.5,
                format="%.1f",
                help="Potência nominal em quilowatts conforme plaqueta.",
            )
        with col_tensao:
            tensao = st.number_input(
                label="Tensão de Operação (V) *",
                min_value=1,
                max_value=100_000,
                value=380,
                step=1,
                format="%d",
                help="Tensão nominal de operação em Volts.",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # — Botão de submissão ————————————————————————————————————————————
        submitted = st.form_submit_button(
            label="✅  Registrar Equipamento",
            use_container_width=True,
        )

    # ── Lógica pós-submissão (fora do form, mas dentro de col_form) ──────────
    if submitted:
        # Validação no frontend antes de chamar o backend.
        # A regra de TAGútag duplicada não é verificada aqui porque o mock_db
        # não impõe constraints de unicidade. Em produção, o FastAPI retornará
        # HTTP 409 Conflict e este bloco deverá tratar o status code.
        erros = []
        if not tag.strip():
            erros.append("O campo **TAG** não pode estar vazio.")
        if not modelo.strip():
            erros.append("O campo **Modelo** não pode estar vazio.")
        if not fabricante.strip():
            erros.append("O campo **Fabricante** não pode estar vazio.")

        if erros:
            for e in erros:
                st.error(e, icon="⚠️")
        else:
            # TAG é normalizada para maiúsculas para evitar duplicatas
            # case-sensitive (ex: "eq-001" e "EQ-001" seriam registros distintos
            # no DataFrame sem essa normalização).
            novo = {
                "TAG"           : tag.strip().upper(),
                "Modelo"        : modelo.strip(),
                "Fabricante"    : fabricante.strip(),
                "Potência (kW)" : potencia,
                "Tensão (V)"    : int(tensao),
            }

            # ② Spinner de latência simulada (human-in-the-loop)
            with st.spinner("⏳ Processando e validando dados no servidor…"):
                adicionar_equipamento(novo)   # time.sleep(1) interno

            # ③ Banner de sucesso com animação
            st.markdown(
                f"""
                <div class="success-banner">
                    <div class="success-icon">✅</div>
                    <div>
                        <div class="success-title">
                            Equipamento <code style="background:#D1FAE5;padding:2px 6px;
                            border-radius:4px;">{novo['TAG']}</code> cadastrado com sucesso!
                        </div>
                        <div class="success-body">
                            <b>{novo['Modelo']}</b> · {novo['Fabricante']} ·
                            {novo['Potência (kW)']:.1f} kW · {novo['Tensão (V)']} V<br>
                            Acesse o <b>📊 Dashboard de Ativos</b> no menu lateral
                            para conferir o novo registro na listagem completa.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ④ Balão comemorativo discreto
            st.balloons()

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="footer">
        Gestão de Ativos · Challenge Sprint 1 · Formulário de Cadastro Técnico
    </div>
    """,
    unsafe_allow_html=True,
)
