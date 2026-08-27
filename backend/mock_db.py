"""
backend/mock_db.py
------------------
Camada de persistência simulada (in-memory + JSON) para o Challenge Sprint 1 / 2 / 3.

Sprint 3 — novidades:
    - Persistência JSON (assets.json na raiz): equipamentos sobrevivem ao restart.
    - @st.cache_data(ttl=30): telemetria fica "viva" para simulação de live data.
    - API de alertas/NLP desacoplada: gerar_alertas, simular_novo_alerta,
      reconhecer_alerta, obter_historico_eventos, gerar_resumo_nlp, sincronizar_alertas.
"""

import json
import math
import os
import random
import uuid
import datetime as _dt

import streamlit as st

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_DB_KEY: str = "equipamentos_db"
_COLUNAS: list[str] = [
    "TAG", "Modelo", "Fabricante", "Potência (kW)", "Tensão (V)", "planta", "imagem_placa",
]
_SEED_BASE: int = 42
_MAX_ALERTAS: int = 20          # cap de alertas ativos na lista
_JSON_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets.json")

# ---------------------------------------------------------------------------
# Persistência JSON — Sprint 3
# ---------------------------------------------------------------------------

def _load_from_json() -> list[dict] | None:
    """Carrega equipamentos do arquivo assets.json, se existir."""
    try:
        if os.path.exists(_JSON_PATH):
            with open(_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass
    return None


def _save_to_json(equipamentos: list[dict]) -> None:
    """Persiste a lista de equipamentos em assets.json."""
    try:
        with open(_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(equipamentos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Dados padrão (mock)
# ---------------------------------------------------------------------------

_MOCK_DEFAULT: list[dict] = [
    {
        "TAG": "EQ-001", "Modelo": "Motor WEG W22", "Fabricante": "WEG",
        "Potência (kW)": 75.0, "Tensão (V)": 380, "planta": "Área Sul",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Motor+EQ-001",
        "dados_ocr": {"confiabilidade": 0.97, "texto_extraido": "WEG MOTOR INDUCAO 3 FASES 75kW 380V IP55 LOTE 2024-A", "data_leitura": "2026-05-01"},
    },
    {
        "TAG": "EQ-002", "Modelo": "Bomba Centrífuga BC-40", "Fabricante": "KSB",
        "Potência (kW)": 15.0, "Tensão (V)": 220, "planta": "Área Norte",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Bomba+EQ-002",
        "dados_ocr": {"confiabilidade": 0.94, "texto_extraido": "KSB BOMBA CENTRIFUGA BC-40 15kW 220V 60Hz S/N 00492", "data_leitura": "2026-05-03"},
    },
    {
        "TAG": "EQ-003", "Modelo": "Compressor Atlas Copco GA-55", "Fabricante": "Atlas Copco",
        "Potência (kW)": 55.0, "Tensão (V)": 380, "planta": "Área Leste",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Compressor+EQ-003",
        "dados_ocr": {"confiabilidade": 0.96, "texto_extraido": "ATLAS COPCO GA-55 COMPRESSOR PARAFUSO 55kW 380V 60Hz", "data_leitura": "2026-05-05"},
    },
    {
        "TAG": "EQ-004", "Modelo": "Motor Siemens SIMOTICS SD 1LE1", "Fabricante": "Siemens",
        "Potência (kW)": 110.0, "Tensão (V)": 440, "planta": "Área Oeste",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Motor+EQ-004",
        "dados_ocr": {"confiabilidade": 0.99, "texto_extraido": "SIEMENS SIMOTICS SD 1LE1 110kW 440V IE3 3~ 60Hz IP55", "data_leitura": "2026-05-07"},
    },
    {
        "TAG": "EQ-005", "Modelo": "Motor WEG W22 IE3", "Fabricante": "WEG",
        "Potência (kW)": 37.0, "Tensão (V)": 380, "planta": "Área Sul",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Motor+EQ-005",
        "dados_ocr": {"confiabilidade": 0.95, "texto_extraido": "WEG W22 IE3 MOTOR TRIFASICO 37kW 380V 60Hz IP55 CL.F", "data_leitura": "2026-05-08"},
    },
    {
        "TAG": "EQ-006", "Modelo": "Bomba KSB Etanorm SYT", "Fabricante": "KSB",
        "Potência (kW)": 22.0, "Tensão (V)": 220, "planta": "Área Leste",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Bomba+EQ-006",
        "dados_ocr": {"confiabilidade": 0.92, "texto_extraido": "KSB ETANORM SYT 22kW 220V 60Hz CLASSE PROT IP44 2024", "data_leitura": "2026-05-09"},
    },
    {
        "TAG": "EQ-007", "Modelo": "Motor Siemens SIMOTICS GP 1LA7", "Fabricante": "Siemens",
        "Potência (kW)": 5.5, "Tensão (V)": 220, "planta": "Área Oeste",
        "imagem_placa": "https://dummyimage.com/300x150/1e1e26/00d2ff.png&text=Placa+Motor+EQ-007",
        "dados_ocr": {"confiabilidade": 0.98, "texto_extraido": "SIEMENS SIMOTICS GP 1LA7 5.5kW 220V 3~ IE2 60Hz IP55", "data_leitura": "2026-05-10"},
    },
]


# ---------------------------------------------------------------------------
# Funções públicas — CRUD
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Inicializa o banco de dados no st.session_state.
    Sprint 3: tenta carregar de assets.json antes de usar dados padrão.
    """
    if _DB_KEY not in st.session_state:
        from_json = _load_from_json()
        st.session_state[_DB_KEY] = from_json if from_json is not None else list(_MOCK_DEFAULT)


def get_equipamentos() -> list[dict]:
    """Retorna cópia defensiva da lista de equipamentos cadastrados."""
    if _DB_KEY not in st.session_state:
        raise RuntimeError("Banco de dados não inicializado. Chame `init_db()` primeiro.")
    return list(st.session_state[_DB_KEY])


def adicionar_equipamento(novo_dict: dict) -> None:
    """
    Persiste um novo equipamento no estado da sessão e salva em JSON.
    Sprint 3: persiste automaticamente em assets.json após cada cadastro.
    Chama sincronizar_alertas() para incluir o novo ativo sem apagar alertas
    existentes (corrige bug de reset silencioso do painel).
    """
    if _DB_KEY not in st.session_state:
        raise RuntimeError("Banco de dados não inicializado. Chame `init_db()` primeiro.")
    st.session_state[_DB_KEY].append(novo_dict)
    _save_to_json(st.session_state[_DB_KEY])
    # Sincroniza alertas mantendo o histórico existente
    sincronizar_alertas()


# ---------------------------------------------------------------------------
# Funções públicas — Telemetria e Saúde (Sprint 2)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=30)
def obter_telemetria_historica(tag: str, num_leituras: int = 20) -> list[dict]:
    """
    Gera série histórica de telemetria simulada para o ativo `tag`.
    Sprint 3: ttl=30 s para renovar dados no painel de alertas em tempo real.
    """
    seed = _SEED_BASE + sum(ord(c) for c in tag)
    rng = random.Random(seed)
    anomaly_indices: set[int] = {i for i in range(num_leituras) if rng.random() < 0.15}
    registros: list[dict] = []
    hora_base = 8

    for i in range(num_leituras):
        horario_str = f"{(hora_base + i) % 24:02d}:00"
        fase = math.sin(math.pi * i / max(num_leituras - 1, 1))

        if i in anomaly_indices:
            temperatura = round(82.0 + rng.uniform(0.0, 10.0), 1)
            vibracao    = round(5.2 + rng.uniform(0.0, 1.6), 2)
            corrente    = int(43 + rng.randint(0, 9))
        else:
            temperatura = round(48.0 + 22.0 * fase + rng.uniform(-3.0, 3.0), 1)
            vibracao    = round(1.5 + 2.5 * fase + rng.uniform(-0.3, 0.3), 2)
            corrente    = int(14 + 22 * fase + rng.randint(-2, 2))

        registros.append({"horario": horario_str, "temperatura": temperatura,
                          "vibracao": vibracao, "corrente": corrente})
    return registros


def obter_ultimas_duas_leituras(tag: str) -> tuple[dict, dict]:
    """Retorna (leitura_atual, leitura_anterior) para cálculo de delta."""
    historico = obter_telemetria_historica(tag, num_leituras=20)
    if not historico:
        _v = {"horario": "--:--", "temperatura": 0.0, "vibracao": 0.0, "corrente": 0}
        return _v, _v
    atual    = historico[-1]
    anterior = historico[-2] if len(historico) >= 2 else historico[-1]
    return atual, anterior


def avaliar_saude(temperatura: float, vibracao: float) -> str:
    """
    Classifica o estado de saúde operacional:
        🔴 Crítico  — temp > 85 °C ou vib > 5.5 mm/s  (ISO 10816-3)
        🟡 Alerta   — temp > 75 °C ou vib > 4.5 mm/s  (IEC 60034-14)
        🟢 Saudável — demais casos
    """
    if temperatura > 85.0 or vibracao > 5.5:
        return "🔴 Crítico"
    if temperatura > 75.0 or vibracao > 4.5:
        return "🟡 Alerta"
    return "🟢 Saudável"


# ---------------------------------------------------------------------------
# Sprint 3 — NLP simulado e recomendações
# ---------------------------------------------------------------------------

_NLP_TEMPLATES_S3 = {
    "Crítico": [
        "Anomalia severa detectada em <b>{tag}</b>. Temperatura de <b>{temp:.1f} °C</b> e vibração de <b>{vib:.2f} mm/s</b> excedem os limites normativos (ISO 10816-3 / IEC 60034-14). Modelo preditivo classifica <b>probabilidade de falha nas próximas 4 h como ALTA</b>. Recomenda-se parada imediata e acionamento da equipe de manutenção corretiva.",
        "<b>{tag}</b> em estado crítico de operação. O padrão de vibração de <b>{vib:.2f} mm/s</b> indica possível falha de rolamento. Temperatura de <b>{temp:.1f} °C</b> sugere comprometimento do sistema de refrigeração. Acione o supervisor de turno imediatamente.",
    ],
    "Alerta": [
        "Desvio identificado em <b>{tag}</b>. Temperatura de <b>{temp:.1f} °C</b> e vibração de <b>{vib:.2f} mm/s</b> estão na zona de atenção (acima do baseline nominal). Tendência ascendente detectada nas últimas leituras. Recomenda-se <b>agendar inspeção preditiva nas próximas 24 h</b>.",
        "<b>{tag}</b> em estado de atenção. Padrão de vibração sugere início de desbalanceamento mecânico. Inspecione acoplamento, verifique alinhamento do eixo e aplique lubrificação conforme ficha técnica.",
    ],
    "Saudável": [
        "<b>{tag}</b> operando dentro dos parâmetros nominais. Temperatura <b>{temp:.1f} °C</b> e vibração <b>{vib:.2f} mm/s</b> — baseline estável. Próxima manutenção preventiva conforme calendário trimestral.",
    ],
}

_RECOMENDACOES_S3 = {
    "Crítico": [
        {"acao": "Parada imediata",         "detalhe": "Isolar o equipamento e acionar supervisor de turno.",             "icone": "🛑"},
        {"acao": "Inspeção de rolamento",   "detalhe": "Verificar folga axial e radial; substituir se desgaste > 0,1 mm.", "icone": "🔧"},
        {"acao": "Sistema de resfriamento", "detalhe": "Checar fluxo de óleo/água e limpeza dos radiadores.",              "icone": "❄️"},
    ],
    "Alerta": [
        {"acao": "Agendar inspeção",        "detalhe": "Programar manutenção preditiva em até 24 h.",                     "icone": "📅"},
        {"acao": "Lubrificação",            "detalhe": "Aplicar graxas conforme ficha técnica do fabricante.",             "icone": "🛢️"},
        {"acao": "Monitoramento contínuo",  "detalhe": "Aumentar frequência de leitura para a cada 15 min.",              "icone": "📡"},
    ],
    "Saudável": [
        {"acao": "Manutenção preventiva",   "detalhe": "Seguir calendário padrão de revisão trimestral.",                  "icone": "✅"},
    ],
}


def _status_sem_emoji(status: str) -> str:
    for chave in ("Crítico", "Alerta", "Saudável"):
        if chave in status:
            return chave
    return "Saudável"


def _gerar_resumo_interno(tag: str, status_raw: str, temp: float, vib: float) -> str:
    status = _status_sem_emoji(status_raw)
    templates = _NLP_TEMPLATES_S3.get(status, _NLP_TEMPLATES_S3["Saudável"])
    return random.choice(templates).format(tag=tag, temp=temp, vib=vib)


def _init_alertas_s3() -> None:
    if "_s3_alertas_ativos" in st.session_state:
        return
    st.session_state["_s3_alertas_ativos"] = []
    st.session_state["_s3_historico_eventos"] = []
    equipamentos = st.session_state.get(_DB_KEY, [])
    agora = _dt.datetime.now()

    for eq in equipamentos:
        tag = eq["TAG"]
        historico = obter_telemetria_historica(tag, num_leituras=20)
        if not historico:
            continue

        # Varrer TODA a série — anomalias podem ocorrer no meio do histórico,
        # não apenas na última leitura (fix: estado 🟡 Alerta antes inalcançável).
        max_temp = max(p["temperatura"] for p in historico)
        max_vib  = max(p["vibracao"]    for p in historico)
        status_raw = avaliar_saude(max_temp, max_vib)
        status = _status_sem_emoji(status_raw)

        if status in ("Crítico", "Alerta"):
            ts = agora - _dt.timedelta(minutes=random.randint(5, 90))
            # score_anomalia simula a confiança do modelo ML (placeholder)
            score = round(max_temp / 85.0, 2) if max_temp > 85 else round(max_vib / 5.5, 2)
            alerta = {
                "id": f"ALT-{tag}-{uuid.uuid4().hex[:8]}",   # UUID: sem colisão de chaves
                "tag": tag, "modelo": eq.get("Modelo", tag),
                "planta": eq.get("planta", "—"),
                "status_raw": status_raw, "status": status,
                "temperatura": max_temp, "vibracao": max_vib,
                "timestamp": ts,
                "recomendacoes": _RECOMENDACOES_S3.get(status, []),
                "reconhecido": False,
                "telemetria": [p["temperatura"] for p in historico],
                # Campos de integração ML/NLP (placeholders para endpoint real)
                "confianca":      round(random.uniform(0.82, 0.99), 2),
                "score_anomalia": min(round(score, 2), 1.0),
                "modelo_versao":  "mock-v1.0",
            }
            st.session_state["_s3_alertas_ativos"].append(alerta)
            st.session_state["_s3_historico_eventos"].append({
                "timestamp": ts, "tag": tag,
                "evento": f"Alerta {status_raw} disparado",
                "status_raw": status_raw,
                "temp": max_temp, "vib": max_vib,
            })

    st.session_state["_s3_alertas_ativos"].sort(
        key=lambda a: (0 if "Crítico" in a["status_raw"] else 1, -a["timestamp"].timestamp())
    )
    st.session_state["_s3_historico_eventos"].sort(key=lambda e: e["timestamp"], reverse=True)


# ---------------------------------------------------------------------------
# API pública — Sprint 3
# ---------------------------------------------------------------------------

def gerar_alertas() -> list[dict]:
    """Retorna lista de alertas ativos (Crítico e Alerta), críticos primeiro."""
    _init_alertas_s3()
    return list(st.session_state["_s3_alertas_ativos"])


def obter_historico_eventos(limite: int = 50) -> list[dict]:
    """Retorna os últimos `limite` eventos do log, mais recentes primeiro."""
    _init_alertas_s3()
    return list(st.session_state["_s3_historico_eventos"])[:limite]


def gerar_resumo_nlp(tag: str, status_raw: str, temperatura: float, vibracao: float) -> str:
    """
    Resumo textual do estado operacional (NLP simulado).
    Estrutura preparada para substituição por endpoint NLP/LLM real.
    """
    return _gerar_resumo_interno(tag, status_raw, temperatura, vibracao)


def simular_novo_alerta() -> dict | None:
    """
    Injeta um alerta simulado (usado pelo botão/timer do painel).
    Alterna entre 🟡 Alerta e 🔴 Crítico para exercitar os dois estados.
    Retorna o alerta criado ou None se não houver equipamentos.
    """
    _init_alertas_s3()
    equipamentos = st.session_state.get(_DB_KEY, [])
    if not equipamentos:
        return None

    # Cap: mantém no máximo _MAX_ALERTAS alertas na lista
    while len(st.session_state["_s3_alertas_ativos"]) >= _MAX_ALERTAS:
        st.session_state["_s3_alertas_ativos"].pop()

    eq  = random.choice(equipamentos)
    tag = eq["TAG"]
    agora = _dt.datetime.now()

    # 50 % Alerta (zona IEC 60034-14) / 50 % Crítico (zona ISO 10816-3)
    if random.random() < 0.5:
        temperatura = round(random.uniform(76.0, 84.9), 1)
        vibracao    = round(random.uniform(4.6,  5.4),  2)
    else:
        temperatura = round(random.uniform(87.0, 103.0), 1)
        vibracao    = round(random.uniform(5.7,  8.2),  2)

    status_raw = avaliar_saude(temperatura, vibracao)
    status     = _status_sem_emoji(status_raw)

    historico  = obter_telemetria_historica(tag, num_leituras=20)
    spark_vals = [p["temperatura"] for p in historico] + [temperatura]
    score = round(temperatura / 85.0, 2) if temperatura > 85 else round(vibracao / 5.5, 2)

    alerta = {
        "id": f"ALT-{tag}-{uuid.uuid4().hex[:8]}",   # UUID: sem colisão de chaves
        "tag": tag, "modelo": eq.get("Modelo", tag),
        "planta": eq.get("planta", "—"),
        "status_raw": status_raw, "status": status,
        "temperatura": temperatura, "vibracao": vibracao,
        "timestamp": agora,
        "recomendacoes": _RECOMENDACOES_S3.get(status, []),
        "reconhecido": False,
        "telemetria": spark_vals,
        "confianca":      round(random.uniform(0.82, 0.99), 2),
        "score_anomalia": min(round(score, 2), 1.0),
        "modelo_versao":  "mock-v1.0",
    }

    st.session_state["_s3_alertas_ativos"].insert(0, alerta)
    st.session_state["_s3_historico_eventos"].insert(0, {
        "timestamp": agora, "tag": tag,
        "evento": "⚡ Novo alerta simulado via atualização",
        "status_raw": status_raw, "temp": temperatura, "vib": vibracao,
    })
    return alerta


def contar_alertas_ativos() -> tuple[int, int]:
    """
    Retorna (n_críticos, n_total_não_reconhecidos) para o badge da sidebar.
    Função pública evita acesso direto a chave privada _s3_alertas_ativos
    em utils.py (corrige vazamento de camada).
    """
    alertas = st.session_state.get("_s3_alertas_ativos", [])
    criticos       = sum(1 for a in alertas if "Crítico" in a.get("status_raw", "") and not a.get("reconhecido"))
    total_nao_recn = sum(1 for a in alertas if not a.get("reconhecido"))
    return criticos, total_nao_recn


def reconhecer_alerta(alerta_id: str) -> bool:
    """Marca um alerta como reconhecido pela equipe de manutenção."""
    _init_alertas_s3()
    for alerta in st.session_state["_s3_alertas_ativos"]:
        if alerta["id"] == alerta_id:
            alerta["reconhecido"] = True
            st.session_state["_s3_historico_eventos"].insert(0, {
                "timestamp": _dt.datetime.now(), "tag": alerta["tag"],
                "evento": "✔ Alerta reconhecido pela equipe",
                "status_raw": alerta["status_raw"],
                "temp": alerta["temperatura"], "vib": alerta["vibracao"],
            })
            return True
    return False


def sincronizar_alertas() -> None:
    """
    Sincroniza alertas com o estado atual dos equipamentos cadastrados.
    Detecta novos ativos (cadastrados após a inicialização) e gera alertas
    para os que estiverem em estado Crítico ou Alerta.
    Chamada automaticamente ao carregar o Painel de Alertas.
    """
    if "_s3_alertas_ativos" not in st.session_state:
        _init_alertas_s3()
        return

    tags_com_alerta = {a["tag"] for a in st.session_state["_s3_alertas_ativos"]}
    equipamentos = st.session_state.get(_DB_KEY, [])
    agora = _dt.datetime.now()

    for eq in equipamentos:
        tag = eq["TAG"]
        if tag in tags_com_alerta:
            continue
        historico = obter_telemetria_historica(tag, num_leituras=20)
        if not historico:
            continue
        max_temp = max(p["temperatura"] for p in historico)
        max_vib  = max(p["vibracao"]    for p in historico)
        status_raw = avaliar_saude(max_temp, max_vib)
        status = _status_sem_emoji(status_raw)
        if status in ("Crítico", "Alerta"):
            ts = agora - _dt.timedelta(minutes=random.randint(1, 10))
            score = round(max_temp / 85.0, 2) if max_temp > 85 else round(max_vib / 5.5, 2)
            alerta = {
                "id": f"ALT-{tag}-{uuid.uuid4().hex[:8]}",
                "tag": tag, "modelo": eq.get("Modelo", tag),
                "planta": eq.get("planta", "—"),
                "status_raw": status_raw, "status": status,
                "temperatura": max_temp, "vibracao": max_vib,
                "timestamp": ts,
                "recomendacoes": _RECOMENDACOES_S3.get(status, []),
                "reconhecido": False,
                "telemetria": [p["temperatura"] for p in historico],
                "confianca":      round(random.uniform(0.82, 0.99), 2),
                "score_anomalia": min(round(score, 2), 1.0),
                "modelo_versao":  "mock-v1.0",
            }
            st.session_state["_s3_alertas_ativos"].insert(0, alerta)
            st.session_state["_s3_historico_eventos"].insert(0, {
                "timestamp": ts, "tag": tag,
                "evento": f"Alerta {status_raw} — novo equipamento detectado",
                "status_raw": status_raw,
                "temp": max_temp, "vib": max_vib,
            })
