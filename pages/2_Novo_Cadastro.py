"""
pages/2_Novo_Cadastro.py
------------------------
Módulo de Cadastro Técnico de Ativos Industriais — Sprint 1.

Sprint 3: validação de TAG duplicada antes de persistir + persistência JSON automática.
"""

import streamlit as st
from backend.mock_db import init_db, adicionar_equipamento, get_equipamentos
from utils import aplicar_design_fixo_sidebar

st.set_page_config(
    page_title="Novo Cadastro | Challenge Sprint 3",
    page_icon="➕",
    layout="wide",
)
aplicar_design_fixo_sidebar()
init_db()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #0D3B8E; }
    [data-testid="stSidebar"] * { color: #E8F0FE !important; }
    [data-testid="stSidebar"] hr { border-color: #1A4FAD; }
    .page-header {
        background: linear-gradient(135deg, #064E3B 0%, #065F46 55%, #047857 100%);
        border-radius: 12px; padding: 28px 36px; margin-bottom: 24px;
        position: relative; overflow: hidden;
    }
    .page-header::after {
        content: "➕"; position: absolute; right: 32px; top: 50%;
        transform: translateY(-50%); font-size: 80px; opacity: 0.10;
    }
    .page-header h1 { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 0 0 6px 0; }
    .page-header p  { color: #A7F3D0; font-size: 14px; margin: 0; max-width: 520px; }
    .form-card { background: #FFFFFF; border: 1px solid #D1FAE5; border-radius: 12px; padding: 32px 36px; box-shadow: 0 4px 20px rgba(6,78,59,0.06); }
    .form-section-label { font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #059669; margin-bottom: 8px; display: block; }
    [data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus { border-color: #059669 !important; box-shadow: 0 0 0 2px rgba(5,150,105,0.15) !important; }
    [data-testid="stFormSubmitButton"] > button { background: linear-gradient(135deg, #047857, #059669) !important; color: #FFFFFF !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 15px !important; padding: 12px 36px !important; width: 100%; }
    [data-testid="stFormSubmitButton"] > button:hover { opacity: 0.88 !important; }
    .rules-card { background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #059669; border-radius: 10px; padding: 20px 22px; font-size: 13px; color: #1A202C; line-height: 1.8; }
    .rules-card h4 { color: #047857; font-size: 13px; font-weight: 700; margin: 0 0 10px 0; }
    .rules-card li { margin-left: 14px; }
    .success-banner { background: linear-gradient(135deg, #D1FAE5, #ECFDF5); border: 1px solid #6EE7B7; border-left: 5px solid #059669; border-radius: 10px; padding: 20px 24px; display: flex; align-items: flex-start; gap: 16px; margin-top: 8px; }
    .success-icon  { font-size: 32px; line-height: 1; }
    .success-title { font-weight: 800; color: #064E3B; font-size: 16px; }
    .success-body  { color: #047857; font-size: 13px; margin-top: 4px; line-height: 1.6; }
    .sec-div { border: none; border-top: 1px solid #E2E8F0; margin: 20px 0 16px; }
    .footer { text-align:center; color:#A0AEC0; font-size:11px; padding-top:12px; border-top:1px solid #E2E8F0; margin-top:32px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-header">
        <h1>Novo Cadastro de Ativo</h1>
        <p>Preencha os dados técnicos do equipamento. A TAG deve ser única no sistema.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_form, col_rules = st.columns([3, 1], gap="large")

with col_rules:
    st.markdown(
        """
        <div class="rules-card">
            <h4>📋 Regras de Preenchimento</h4>
            <ul>
                <li><b>TAG</b>: formato sugerido <code>EQ-XXX</code></li>
                <li><b>TAG</b>: deve ser única — duplicatas são rejeitadas</li>
                <li><b>Potência</b>: valor em kW, mínimo 0,1</li>
                <li><b>Tensão</b>: valor em V, mínimo 1</li>
                <li>Campos em branco serão rejeitados</li>
            </ul>
            <br>
            <h4>⚙️ Padrões Aceitos</h4>
            <ul>
                <li>Tensão: 127 V · 220 V · 380 V · 440 V</li>
                <li>Potência: 0,75 kW a 1000 kW</li>
            </ul>
            <br>
            <h4>💾 Persistência</h4>
            <ul>
                <li>Dados salvos em <code>assets.json</code></li>
                <li>Sobrevivem ao reinício do app</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_form:
    with st.form("cadastro_form", clear_on_submit=True):
        st.markdown("<span class='form-section-label'>Identificação do Equipamento</span>", unsafe_allow_html=True)

        col_tag, col_modelo = st.columns([1, 2])
        with col_tag:
            tag = st.text_input("TAG *", placeholder="EQ-008", help="Identificador único. Ex: EQ-008", max_chars=20)
        with col_modelo:
            modelo = st.text_input("Modelo *", placeholder="Ex: Motor WEG W22 IE3", max_chars=80)

        fabricante = st.text_input("Fabricante *", placeholder="Ex: WEG, KSB, Atlas Copco, Siemens…", max_chars=60)

        col_planta, _ = st.columns([2, 2])
        with col_planta:
            planta = st.text_input("Planta / Área", placeholder="Ex: Área Sul", max_chars=50,
                                   help="Localização do equipamento na planta industrial.")

        st.markdown("<hr class='sec-div'>", unsafe_allow_html=True)
        st.markdown("<span class='form-section-label'>Dados Elétricos Nominais</span>", unsafe_allow_html=True)

        col_pot, col_tensao = st.columns(2)
        with col_pot:
            potencia = st.number_input("Potência Nominal (kW) *", min_value=0.1, max_value=10_000.0, value=15.0, step=0.5, format="%.1f")
        with col_tensao:
            tensao = st.number_input("Tensão de Operação (V) *", min_value=1, max_value=100_000, value=380, step=1, format="%d")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("✅  Registrar Equipamento", width='stretch')

    if submitted:
        erros = []
        if not tag.strip():
            erros.append("O campo **TAG** não pode estar vazio.")
        if not modelo.strip():
            erros.append("O campo **Modelo** não pode estar vazio.")
        if not fabricante.strip():
            erros.append("O campo **Fabricante** não pode estar vazio.")

        # Validação de TAG duplicada — Sprint 3
        tag_normalizada = tag.strip().upper()
        if tag_normalizada and not erros:
            tags_existentes = {eq["TAG"] for eq in get_equipamentos()}
            if tag_normalizada in tags_existentes:
                erros.append(
                    f"A TAG **{tag_normalizada}** já está cadastrada no sistema. "
                    "Escolha um identificador diferente."
                )

        if erros:
            for e in erros:
                st.error(e, icon="⚠️")
        else:
            novo = {
                "TAG":            tag_normalizada,
                "Modelo":         modelo.strip(),
                "Fabricante":     fabricante.strip(),
                "Potência (kW)":  potencia,
                "Tensão (V)":     int(tensao),
                "planta":         planta.strip() if planta.strip() else "Sem Planta",
                "imagem_placa":   f"https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+{tag_normalizada}",
                "dados_ocr": {
                    "confiabilidade": 0.0,
                    "texto_extraido": "OCR pendente — aguardando leitura de placa",
                    "data_leitura": "—",
                },
            }

            with st.spinner("⏳ Processando e salvando dados…"):
                adicionar_equipamento(novo)

            st.markdown(
                f"""
                <div class="success-banner">
                    <div class="success-icon">✅</div>
                    <div>
                        <div class="success-title">
                            Equipamento <code style="background:#D1FAE5;padding:2px 6px;border-radius:4px;">{novo['TAG']}</code> cadastrado com sucesso!
                        </div>
                        <div class="success-body">
                            <b>{novo['Modelo']}</b> · {novo['Fabricante']} · {novo['Potência (kW)']:.1f} kW · {novo['Tensão (V)']} V · {novo['planta']}<br>
                            Dados salvos em <b>assets.json</b> — persistirão após reinício.<br>
                            Acesse <b>📊 Dashboard de Ativos</b> para conferir o novo registro.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.balloons()

st.markdown(
    """<div class="footer">Gestão de Ativos · Challenge Sprint 3 · Formulário de Cadastro Técnico</div>""",
    unsafe_allow_html=True,
)
