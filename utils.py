"""
utils.py
--------
Utilitários compartilhados entre todas as páginas da aplicação.
Inclui design system, sidebar persistente e componentes reutilizáveis.

Mudanças Sprint 2 (adaptadas do projeto PYRO//GUARD):
    - kpi_card(): componente de KPI com barra lateral colorida por
      criticidade, delta e hint — reutilizável em Dashboard e Monitoramento.
      Adaptado de ui/components.py do PYRO//GUARD para o tema azul industrial.
    - status_card(): variante do kpi_card para exibir status de saúde
      operacional com cor semântica (verde/amarelo/vermelho).
    - inject_plotly_js(): helper para garantir que o Plotly esteja disponível
      nas páginas que usam go.Figure sem import explícito.
"""

import datetime
import streamlit as st


# ── Paleta de cores central ───────────────────────────────────────────────────
# Fonte única de verdade: todas as cores do sistema vêm daqui.
# Adapta o padrão PYRO//GUARD (core/palette.py) para o contexto industrial azul.
class _Palette:
    # Superfícies
    bg_primary  = "#0F0F11"
    bg_surface  = "#18181B"
    bg_elevated = "#1E1E22"
    border      = "#2E2E35"
    # Texto
    text_primary   = "#E4E4E7"
    text_secondary = "#9CA3AF"
    text_muted     = "#6B7280"
    # Semânticas de saúde operacional
    critical = "#EF4444"   # 🔴 temperatura > 85°C ou vibração > 5.5 mm/s
    alert    = "#F59E0B"   # 🟡 temperatura > 75°C ou vibração > 4.5 mm/s
    safe     = "#34D399"   # 🟢 operação normal
    info     = "#5AC8FA"
    # Brand azul industrial
    brand_primary   = "#1560BD"
    brand_secondary = "#2272D9"
    brand_accent    = "#7C3AED"


PALETTE = _Palette()


def cor_por_status(status: str) -> str:
    """Retorna a cor hexadecimal correspondente ao status de saúde.

    Centraliza o mapeamento status → cor para que kpi_card, status_card
    e a sidebar usem exatamente a mesma referência.

    Args:
        status: string retornada por avaliar_saude() —
                '🔴 Crítico', '🟡 Alerta' ou '🟢 Saudável'.
    Returns:
        Hex string da cor semântica.
    """
    if "Crítico" in status:
        return PALETTE.critical
    if "Alerta" in status:
        return PALETTE.alert
    return PALETTE.safe


# ── Componentes reutilizáveis ─────────────────────────────────────────────────

def kpi_card(
    label: str,
    value: str,
    accent: str | None = None,
    delta: str | None = None,
    hint: str | None = None,
) -> None:
    """Cartão de KPI com barra lateral colorida — reutilizável em qualquer página.

    Adaptado do componente kpi_card do PYRO//GUARD (ui/components.py) para o
    tema azul industrial da Gestão de Ativos. A barra lateral muda de cor
    conforme o parâmetro `accent`, permitindo semântica visual de criticidade
    sem modificar o layout.

    ATENÇÃO: o HTML é montado via lista + join() SEM indentação interna.
    Multi-line f-strings com linhas em branco quando delta/hint=None fazem
    o CommonMark do Streamlit tratar o bloco como código literal.
    Padrão herdado do PYRO//GUARD para evitar esse bug.

    Args:
        label:  rótulo curto em caixa alta (ex.: "Temperatura Atual").
        value:  valor principal formatado (ex.: "72.3 °C").
        accent: cor hex da barra lateral; padrão = azul brand.
        delta:  variação opcional (ex.: "+2.1 °C vs anterior").
                Começa com '+'/'-'/'↑'/'↓' para coloração automática.
        hint:   texto auxiliar menor (ex.: "limite crítico: 85 °C").
    """
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
        parts.append(
            f'<div class="ga-kpi-delta" style="color:{sign_color}">{delta}</div>'
        )
    if hint:
        parts.append(f'<div class="ga-kpi-hint">{hint}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def status_card(status: str, tag: str | None = None) -> None:
    """Card de status de saúde operacional com cor semântica automática.

    Variante do kpi_card especializada para exibir o resultado de
    avaliar_saude() com visual destacado. Usada na coluna de saúde
    da tela de Monitoramento.

    Args:
        status: string de avaliar_saude() — '🔴 Crítico', '🟡 Alerta', '🟢 Saudável'.
        tag:    TAG do ativo (opcional) — exibida como hint.
    """
    color = cor_por_status(status)
    hint_text = f"Ativo: {tag}" if tag else None
    kpi_card("🩺 Saúde Operacional", status, accent=color, hint=hint_text)


def section_header(title: str, subtitle: str | None = None, accent: str | None = None) -> None:
    """Cabeçalho de seção com barra vertical colorida.

    Adaptado de ui/components.py do PYRO//GUARD. Substitui st.subheader()
    para manter consistência visual com os componentes do design system.

    Args:
        title:    título da seção.
        subtitle: texto menor exibido à direita (opcional).
        accent:   cor da barra vertical; padrão = azul brand.
    """
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


# ── CSS global do design system ───────────────────────────────────────────────

_GLOBAL_CSS = f"""
<style>
/* ── Sanitização do framework ──────────────────────────────────────────── */
[data-testid="stBottom"],
footer                         {{ display: none !important; }}
#MainMenu                      {{ display: none !important; }}
[data-testid="stSidebarHeader"]{{ display: none !important; }}
.block-container               {{ padding-top: 1.5rem !important; }}

/* ── Sidebar — estrutura geral ────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: #111113 !important;
    border-right: 1px solid rgba(124, 58, 237, 0.20) !important;
    padding: 0 !important;
}}
[data-testid="stSidebarContent"] {{
    padding: 1.2rem 1rem !important;
}}

/* ── Card de identidade (azul vibrante) ───────────────────────────────── */
.sb-card {{
    background: linear-gradient(135deg, #1A3FBF 0%, {PALETTE.brand_primary} 60%, {PALETTE.brand_secondary} 100%);
    border-radius: 14px;
    padding: 18px 16px 14px 16px;
    text-align: center;
    margin-bottom: 18px;
    box-shadow: 0 4px 18px rgba(21, 96, 189, 0.35);
}}
.sb-card-title {{
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    line-height: 1.3;
}}
.sb-card-sub {{
    color: rgba(255,255,255,0.75);
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.8px;
    margin-top: 5px;
    text-transform: uppercase;
}}

/* ── Badges de status ─────────────────────────────────────────────────── */
.sb-status-label {{
    color: {PALETTE.text_secondary};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin: 14px 0 8px 2px;
}}
.sb-badge {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: {PALETTE.bg_elevated};
    border: 1px solid {PALETTE.border};
    border-radius: 20px;
    padding: 6px 14px;
    margin-bottom: 6px;
    font-size: 12px;
    font-weight: 500;
    color: {PALETTE.text_primary};
}}
.sb-dot-green  {{ color: {PALETTE.safe};  font-size: 10px; }}
.sb-dot-yellow {{ color: {PALETTE.alert}; font-size: 10px; }}

/* ── Divider ──────────────────────────────────────────────────────────── */
.sb-divider {{
    border: none;
    border-top: 1px solid {PALETTE.border};
    margin: 14px 0;
}}
.sb-section-label {{
    color: {PALETTE.text_muted};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin: 0 0 6px 2px;
}}
.sb-env {{
    color: {PALETTE.text_muted};
    font-size: 10px;
    line-height: 1.8;
    margin-top: 4px;
    padding-left: 2px;
}}

/* ── KPI Card (design system PYRO adaptado) ───────────────────────────── */
.ga-kpi {{
    background: linear-gradient(135deg, {PALETTE.bg_surface} 0%, {PALETTE.bg_elevated} 100%);
    border: 1px solid {PALETTE.border};
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
    position: relative;
    overflow: hidden;
    margin-bottom: 2px;
}}
.ga-kpi::before {{
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--ga-accent, {PALETTE.brand_primary});
    border-radius: 2px 0 0 2px;
}}
.ga-kpi-label {{
    color: {PALETTE.text_secondary};
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 6px;
}}
.ga-kpi-value {{
    color: {PALETTE.text_primary};
    font-size: 1.65rem;
    font-weight: 800;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.ga-kpi-delta {{
    font-size: 0.78rem;
    margin-top: 5px;
    font-weight: 500;
}}
.ga-kpi-hint {{
    color: {PALETTE.text_muted};
    font-size: 0.68rem;
    margin-top: 5px;
}}

/* ── Section Header ───────────────────────────────────────────────────── */
.ga-section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 16px 0 12px 0;
}}
.ga-section-bar {{
    width: 4px;
    height: 20px;
    border-radius: 2px;
    flex-shrink: 0;
}}
.ga-section-title {{
    margin: 0;
    color: {PALETTE.text_primary};
    font-size: 1.05rem;
    font-weight: 700;
}}
.ga-section-sub {{
    color: {PALETTE.text_secondary};
    font-size: 0.8rem;
    margin-left: auto;
}}

/* ── Plotly fundo transparente ────────────────────────────────────────── */
.js-plotly-plot .plotly {{
    background: transparent !important;
}}
</style>
"""


# ── Função principal de inicialização ────────────────────────────────────────

def aplicar_estilo_ui() -> None:
    """Mantida por compatibilidade. Delega para aplicar_design_fixo_sidebar()."""
    aplicar_design_fixo_sidebar()


def aplicar_design_fixo_sidebar() -> None:
    """Injeta CSS global + renderiza sidebar completa (card, status, nav).

    Deve ser chamada imediatamente após st.set_page_config() em cada arquivo
    de página. O Streamlit reexecuta o script inteiro a cada interação, então
    a sidebar precisa ser reconstruída em cada ciclo de execução.

    Mudança Sprint 2: CSS agora é gerado a partir de PALETTE (única fonte
    de verdade), eliminando duplicação de valores hex entre páginas.
    """
    # ── 1. CSS Global ─────────────────────────────────────────────────────────
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

    # ── 2. Conteúdo da Sidebar ────────────────────────────────────────────────
    now_str = datetime.datetime.now().strftime("%H:%M · %d/%m/%Y")

    with st.sidebar:
        # Card de identidade azul
        st.markdown(
            """
            <div class="sb-card">
                <div class="sb-card-title">Gestão de Ativos</div>
                <div class="sb-card-sub">Challenge Sprint 2 · FIAP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status do sistema
        st.markdown(
            f"""
            <div class="sb-status-label">Status do Sistema</div>
            <div class="sb-badge"><span class="sb-dot-green">●</span> Serviço Online</div>
            <div class="sb-badge"><span class="sb-dot-green">●</span> Banco de Dados OK</div>
            <div class="sb-badge"><span class="sb-dot-yellow">●</span> API — Modo Mock</div>
            <div style="color:{PALETTE.text_muted};font-size:10px;margin:6px 0 0 4px;">
                Última verificação: {now_str}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

        # Informações de ambiente
        st.markdown(
            """
            <div class="sb-section-label">Ambiente</div>
            <div class="sb-env">
                🔖 Sprint 2 &nbsp;·&nbsp; v0.2.0<br>
                🏗️ Stack: Streamlit + Python puro<br>
                🔗 Backend: Mock (FastAPI em breve)
            </div>
            """,
            unsafe_allow_html=True,
        )
