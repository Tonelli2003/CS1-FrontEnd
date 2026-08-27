"""
pages/0_🚨_Painel_Alertas.py
-----------------------------
Sprint 3 — Painel de Alertas e Estados Operacionais.

Página inicial da aplicação (prefixo 0_ garante posição no menu).
Exibe alertas ativos, resumos NLP, recomendações de manutenção
e histórico de eventos. Atualização por botão ou timer automático.

Arquitetura:
    - Consome exclusivamente as funções públicas do backend/mock_db.py.
    - Componentes visuais via utils.py (alert_card, recommendation_card,
      event_row, section_header, kpi_card).
    - NLP desacoplado: gerar_resumo_nlp() é chamada nesta página no momento
      da renderização. Para integrar NLP/ML real, substitua apenas o corpo
      de gerar_resumo_nlp() — nenhuma linha desta página muda.
    - Timer não-bloqueante via @st.fragment(run_every=...) — sem time.sleep().
"""

import datetime
import io
import csv

import streamlit as st

# ── Setup da página ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Painel de Alertas · Gestão de Ativos",
    page_icon="🚨",
    layout="wide",
)

from backend.mock_db import (
    init_db,
    gerar_alertas,
    gerar_resumo_nlp,
    obter_historico_eventos,
    simular_novo_alerta,
    reconhecer_alerta,
    sincronizar_alertas,
)
from utils import (
    aplicar_design_fixo_sidebar,
    PALETTE,
    alert_card,
    recommendation_card,
    event_row,
    section_header,
    kpi_card,
    cor_por_status,
)

# ── Inicialização ────────────────────────────────────────────────────────────
init_db()
sincronizar_alertas()           # Detecta novos equipamentos sem apagar histórico
aplicar_design_fixo_sidebar()

# ── Estado de sessão ─────────────────────────────────────────────────────────
if "_painel_ultimo_refresh" not in st.session_state:
    st.session_state["_painel_ultimo_refresh"] = datetime.datetime.now()
if "_painel_novo_alerta_msg" not in st.session_state:
    st.session_state["_painel_novo_alerta_msg"] = None

# ── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-bottom:4px;">
        <h1 style="color:{PALETTE.text_primary}; font-size:1.7rem; font-weight:900;
                   letter-spacing:0.02em; margin:0 0 4px 0;">
            🚨 Painel de Alertas e Estados
        </h1>
        <p style="color:{PALETTE.text_secondary}; font-size:0.9rem; margin:0;">
            Monitoramento contínuo · Inteligência Operacional · Sprint 3
        </p>
    </div>
    <hr style="border:none; border-top:1px solid {PALETTE.border}; margin:12px 0 20px 0;">
    """,
    unsafe_allow_html=True,
)

# ── Controles de atualização ─────────────────────────────────────────────────
col_btn, col_timer, col_auto, col_ts = st.columns([1.2, 1.2, 1.8, 3])

with col_btn:
    atualizar = st.button("⟳ Atualizar agora", type="primary", width='stretch')

with col_timer:
    intervalo = st.selectbox(
        "Timer (seg)",
        options=[0, 15, 30, 60],
        format_func=lambda v: "Desligado" if v == 0 else f"{v}s",
        key="_painel_intervalo",
        label_visibility="collapsed",
    )

with col_auto:
    st.markdown(
        f"<div style='padding-top:8px; font-size:0.85rem; color:{PALETTE.text_secondary};'>"
        f"⏱ Auto-refresh: <b>{'Ativo' if intervalo > 0 else 'Desligado'}</b></div>",
        unsafe_allow_html=True,
    )

with col_ts:
    ts_refresh = st.session_state["_painel_ultimo_refresh"].strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(
        f"<div style='padding-top:8px; font-size:0.8rem; color:{PALETTE.text_muted}; text-align:right;'>"
        f"Última atualização: {ts_refresh}</div>",
        unsafe_allow_html=True,
    )

# ── Lógica do botão "Atualizar agora" ────────────────────────────────────────
if atualizar:
    novo = simular_novo_alerta()
    st.session_state["_painel_ultimo_refresh"] = datetime.datetime.now()
    if novo:
        st.session_state["_painel_novo_alerta_msg"] = (
            f"⚡ Novo alerta simulado: **{novo['tag']} — {novo['modelo']}** "
            f"({novo['temperatura']:.1f} °C / {novo['vibracao']:.2f} mm/s)"
        )
    st.rerun()

# Notificação de novo alerta (persiste um ciclo de rerun)
if st.session_state["_painel_novo_alerta_msg"]:
    st.toast(st.session_state["_painel_novo_alerta_msg"], icon="🔴")
    st.session_state["_painel_novo_alerta_msg"] = None

# ── KPIs de resumo ───────────────────────────────────────────────────────────
alertas = gerar_alertas()
total     = len(alertas)
criticos  = sum(1 for a in alertas if "Crítico" in a["status_raw"])
em_alerta = sum(1 for a in alertas if "Alerta"  in a["status_raw"] and "Crítico" not in a["status_raw"])
reconh    = sum(1 for a in alertas if a["reconhecido"])

st.markdown("<div style='margin-bottom:4px;'></div>", unsafe_allow_html=True)
kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    kpi_card("Total de Alertas", str(total), accent=PALETTE.brand_primary)
with kc2:
    kpi_card("🔴 Críticos", str(criticos), accent=PALETTE.critical)
with kc3:
    kpi_card("🟡 Em Alerta", str(em_alerta), accent=PALETTE.alert)
with kc4:
    kpi_card("✔ Reconhecidos", str(reconh), accent=PALETTE.safe)

st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

# ── Tabs principais ──────────────────────────────────────────────────────────
tab_alertas, tab_recomendacoes, tab_historico = st.tabs([
    f"🚨 Alertas Ativos ({total})",
    "🔧 Recomendações",
    "📋 Histórico de Eventos",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Alertas Ativos
# ─────────────────────────────────────────────────────────────────────────────
with tab_alertas:
    if not alertas:
        st.markdown(
            f"""
            <div style="text-align:center; padding:60px 20px;
                        color:{PALETTE.text_muted}; font-size:1rem;">
                🟢 Nenhum alerta ativo no momento.<br>
                <span style="font-size:0.85rem;">
                    Todos os equipamentos operam dentro dos parâmetros nominais.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        filtro_col, _ = st.columns([2, 5])
        with filtro_col:
            filtro_status = st.selectbox(
                "Filtrar por status",
                options=["Todos", "🔴 Crítico", "🟡 Alerta", "✔ Reconhecidos"],
                key="_painel_filtro_status",
                label_visibility="collapsed",
            )

        alertas_exibir = alertas
        if filtro_status == "🔴 Crítico":
            alertas_exibir = [a for a in alertas if "Crítico" in a["status_raw"]]
        elif filtro_status == "🟡 Alerta":
            alertas_exibir = [a for a in alertas if "Alerta" in a["status_raw"] and "Crítico" not in a["status_raw"]]
        elif filtro_status == "✔ Reconhecidos":
            alertas_exibir = [a for a in alertas if a["reconhecido"]]

        if not alertas_exibir:
            st.info("Nenhum alerta encontrado para o filtro selecionado.")
        else:
            for alerta in alertas_exibir:
                # NLP chamado aqui no ponto de renderização — substituir
                # gerar_resumo_nlp() por endpoint HTTP sem alterar esta página.
                resumo = gerar_resumo_nlp(
                    alerta["tag"], alerta["status_raw"],
                    alerta["temperatura"], alerta["vibracao"],
                )
                resultado = alert_card(
                    tag=alerta["tag"],
                    modelo=alerta["modelo"],
                    planta=alerta["planta"],
                    status_raw=alerta["status_raw"],
                    temperatura=alerta["temperatura"],
                    vibracao=alerta["vibracao"],
                    timestamp=alerta["timestamp"],
                    resumo_nlp=resumo,
                    reconhecido=alerta["reconhecido"],
                    alerta_id=alerta["id"],
                    telemetria=alerta["telemetria"],  # sparkline ligado
                )
                if resultado == "reconhecer":
                    reconhecer_alerta(alerta["id"])
                    st.toast(f"✔ Alerta {alerta['tag']} reconhecido.", icon="✅")
                    st.rerun()
                elif resultado == "monitorar":
                    # Navegação cruzada direta — mesma pattern do Dashboard
                    st.session_state["tag_navegacao"] = alerta["tag"]
                    st.switch_page("pages/3_Monitoramento.py")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Recomendações de Decisão
# ─────────────────────────────────────────────────────────────────────────────
with tab_recomendacoes:
    if not alertas:
        st.info("Nenhum alerta ativo — nenhuma recomendação de ação imediata.")
    else:
        criticos_list = [a for a in alertas if "Crítico" in a["status_raw"] and not a["reconhecido"]]
        alertas_list  = [a for a in alertas if "Alerta"  in a["status_raw"] and "Crítico" not in a["status_raw"] and not a["reconhecido"]]

        if criticos_list:
            section_header("⚡ Ações Imediatas — Equipamentos Críticos", accent=PALETTE.critical)
            for alerta in criticos_list:
                st.markdown(
                    f"<div style='font-size:0.9rem; font-weight:700; color:{PALETTE.critical}; "
                    f"margin:10px 0 6px 0;'>{alerta['tag']} — {alerta['modelo']}</div>",
                    unsafe_allow_html=True,
                )
                for rec in alerta.get("recomendacoes", []):
                    recommendation_card(acao=rec["acao"], detalhe=rec["detalhe"],
                                        icone=rec["icone"], urgente=True)

        if alertas_list:
            section_header("📅 Ações Planejadas — Equipamentos em Alerta", accent=PALETTE.alert)
            for alerta in alertas_list:
                st.markdown(
                    f"<div style='font-size:0.9rem; font-weight:700; color:{PALETTE.alert}; "
                    f"margin:10px 0 6px 0;'>{alerta['tag']} — {alerta['modelo']}</div>",
                    unsafe_allow_html=True,
                )
                for rec in alerta.get("recomendacoes", []):
                    recommendation_card(acao=rec["acao"], detalhe=rec["detalhe"],
                                        icone=rec["icone"], urgente=False)

        if not criticos_list and not alertas_list:
            st.success("✔ Todos os alertas ativos já foram reconhecidos pela equipe.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Histórico de Eventos
# ─────────────────────────────────────────────────────────────────────────────
with tab_historico:
    historico = obter_historico_eventos(limite=50)

    if not historico:
        st.info("Nenhum evento registrado ainda.")
    else:
        col_hdr, col_csv = st.columns([3, 1])
        with col_hdr:
            section_header(
                "📋 Log de Eventos",
                subtitle=f"{len(historico)} registros",
            )
        with col_csv:
            # Exportação CSV — zero-pandas
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["timestamp", "tag", "evento", "status", "temp_c", "vib_mms"])
            writer.writeheader()
            for ev in historico:
                writer.writerow({
                    "timestamp": ev["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "tag": ev["tag"],
                    "evento": ev["evento"],
                    "status": ev["status_raw"],
                    "temp_c": f"{ev['temp']:.1f}",
                    "vib_mms": f"{ev['vib']:.2f}",
                })
            st.download_button(
                "⬇️ Exportar CSV",
                data=buf.getvalue().encode("utf-8"),
                file_name=f"historico_alertas_{datetime.date.today()}.csv",
                mime="text/csv",
                width='stretch',
            )

        st.markdown(
            f"""
            <div style="
                display:grid;
                grid-template-columns: 110px 80px 1fr 130px 80px 90px;
                gap:8px; padding:6px 12px;
                font-size:0.75rem; font-weight:700;
                letter-spacing:0.08em; text-transform:uppercase;
                color:{PALETTE.text_muted};
                border-bottom:2px solid {PALETTE.border}; margin-bottom:4px;
            ">
                <span>Horário</span><span>TAG</span><span>Evento</span>
                <span>Status</span><span>Temp.</span><span>Vibração</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for ev in historico:
            event_row(timestamp=ev["timestamp"], tag=ev["tag"], evento=ev["evento"],
                      status_raw=ev["status_raw"], temp=ev["temp"], vib=ev["vib"])

# ── Auto-refresh não-bloqueante via @st.fragment ─────────────────────────────
# Substitui o time.sleep() + st.rerun() bloqueante (fix: UI responsiva durante timer).
# @st.fragment(run_every=N) reexecuta APENAS este fragmento a cada N segundos,
# sem travar os botões Reconhecer/Monitorar da UI principal.
if intervalo > 0:
    @st.fragment(run_every=intervalo)
    def _auto_tick():
        novo = simular_novo_alerta()
        st.session_state["_painel_ultimo_refresh"] = datetime.datetime.now()
        if novo:
            st.toast(
                f"⚡ Timer ({intervalo}s): novo alerta em **{novo['tag']}** "
                f"({novo['temperatura']:.1f} °C / {novo['vibracao']:.2f} mm/s)",
                icon="🔴",
            )
        # scope="app" força rerun completo para atualizar KPIs e lista de alertas
        st.rerun(scope="app")

    _auto_tick()

# ── Modo Demo ────────────────────────────────────────────────────────────────
with st.expander("🧪 Modo Demo — Simulação de Eventos", expanded=False):
    st.caption("Ferramentas para demonstração ao vivo. Não disponível em produção.")
    d1, d2, d3 = st.columns(3)
    with d1:
        if st.button("⚡ Injetar Alerta", width='stretch'):
            novo = simular_novo_alerta()
            if novo:
                st.toast(f"Alerta {novo['status_raw']} injetado em {novo['tag']}", icon="🔴")
            st.rerun()
    with d2:
        if st.button("✔ Reconhecer Todos", width='stretch'):
            for a in st.session_state.get("_s3_alertas_ativos", []):
                a["reconhecido"] = True
            st.toast("Todos os alertas reconhecidos.", icon="✅")
            st.rerun()
    with d3:
        if st.button("🗑 Limpar Alertas", width='stretch'):
            st.session_state.pop("_s3_alertas_ativos", None)
            st.session_state.pop("_s3_historico_eventos", None)
            st.toast("Alertas limpos. Painel reiniciado.", icon="🔄")
            st.rerun()
