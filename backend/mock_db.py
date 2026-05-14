"""
backend/mock_db.py
------------------
Camada de persistência simulada (in-memory) para o Challenge Sprint 1 / Sprint 2.

Decisão de arquitetura:
    st.session_state foi escolhido como mecanismo de armazenamento
    porque sobrevive a reruns do Streamlit sem exigir I/O externo,
    permitindo testar o contrato CRUD completo antes da integração
    com o backend FastAPI.

    O contrato público deste módulo (init_db / get_equipamentos /
    adicionar_equipamento / obter_telemetria_historica / avaliar_saude)
    é idêntico ao que será exposto pelas chamadas REST futuras, isolando
    o frontend de qualquer detalhe de persistência.

    Refatoração Sprint 1: pandas removido — o estado é uma lista nativa
    de dicionários. st.dataframe() aceita esse formato diretamente e
    todas as operações de filtragem usam list comprehension.

    Novidades Sprint 2:
    - Campos 'planta' e 'imagem_placa' nos ativos mockados.
    - obter_telemetria_historica(): telemetria simulada com picos de anomalia;
      retorna 'horario' como chave de tempo (formato HH:MM), num_leituras=20.
    - avaliar_saude(): Crítico se temp>85 ou vib>5.5; Alerta se temp>75 ou vib>4.5.

    Restrição: apenas Python puro — sem pandas, sem numpy.
"""

import math
import random
import time

import streamlit as st

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

# Chave única no session_state. Centralizar como constante evita conflitos
# de nome entre páginas distintas que compartilham o mesmo estado global.
_DB_KEY: str = "equipamentos_db"

# Chaves canônicas do schema — usadas para garantir ordem consistente
# na exportação CSV e na exibição tabular.
_COLUNAS: list[str] = [
    "TAG",
    "Modelo",
    "Fabricante",
    "Potência (kW)",
    "Tensão (V)",
    "planta",
    "imagem_placa",
]

# Semente fixa: garante que a telemetria gerada para a mesma TAG
# seja determinística em reruns da mesma sessão.
_SEED_BASE: int = 42


# ---------------------------------------------------------------------------
# Funções públicas — CRUD
# ---------------------------------------------------------------------------


def init_db() -> None:
    """
    Inicializa o banco de dados simulado no st.session_state.

    A guarda `if _DB_KEY not in st.session_state` é intencional:
    o Streamlit reexecuta o script inteiro a cada interação do usuário,
    portanto sem ela os dados seriam sobrescritos a cada rerun.
    Os registros de exemplo servem para garantir que as demais páginas
    tenham dados válidos para renderizar sem depender de cadastro prévio.

    Sprint 2: os registros agora incluem os campos 'planta' e
    'imagem_placa', compatíveis com a tela de ficha técnica expandida.

    Returns:
        None
    """
    if _DB_KEY not in st.session_state:
        st.session_state[_DB_KEY] = [
            {
                "TAG": "EQ-001",
                "Modelo": "Motor WEG W22",
                "Fabricante": "WEG",
                "Potência (kW)": 75.0,
                "Tensão (V)": 380,
                "planta": "Área Sul",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Motor+EQ-001"
                ),
            },
            {
                "TAG": "EQ-002",
                "Modelo": "Bomba Centrífuga BC-40",
                "Fabricante": "KSB",
                "Potência (kW)": 15.0,
                "Tensão (V)": 220,
                "planta": "Área Norte",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Bomba+EQ-002"
                ),
            },
            {
                "TAG": "EQ-003",
                "Modelo": "Compressor Atlas Copco GA-55",
                "Fabricante": "Atlas Copco",
                "Potência (kW)": 55.0,
                "Tensão (V)": 380,
                "planta": "Área Leste",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Compressor+EQ-003"
                ),
            },
            # ------------------------------------------------------------------
            # Registros adicionados na Sprint 2 — cobertura de filtros por planta
            # ------------------------------------------------------------------
            {
                "TAG": "EQ-004",
                "Modelo": "Motor Siemens SIMOTICS SD 1LE1",
                "Fabricante": "Siemens",
                "Potência (kW)": 110.0,
                "Tensão (V)": 440,
                "planta": "Área Oeste",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Motor+EQ-004"
                ),
            },
            {
                "TAG": "EQ-005",
                "Modelo": "Motor WEG W22 IE3",
                "Fabricante": "WEG",
                "Potência (kW)": 37.0,
                "Tensão (V)": 380,
                "planta": "Área Sul",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Motor+EQ-005"
                ),
            },
            {
                "TAG": "EQ-006",
                "Modelo": "Bomba KSB Etanorm SYT",
                "Fabricante": "KSB",
                "Potência (kW)": 22.0,
                "Tensão (V)": 220,
                "planta": "Área Leste",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Bomba+EQ-006"
                ),
            },
            {
                "TAG": "EQ-007",
                "Modelo": "Motor Siemens SIMOTICS GP 1LA7",
                "Fabricante": "Siemens",
                "Potência (kW)": 5.5,
                "Tensão (V)": 220,
                "planta": "Área Oeste",
                "imagem_placa": (
                    "https://via.placeholder.com/300x150.png?text=Placa+Motor+EQ-007"
                ),
            },
        ]


def get_equipamentos() -> list[dict]:
    """
    Retorna cópia defensiva da lista de equipamentos cadastrados.

    Retorna uma cópia rasa via list() para evitar que mutações no
    chamador corrompam o estado global. O RuntimeError serve de
    contrato explícito: qualquer página que chame esta função sem
    init_db() anterior recebe uma mensagem acionável em vez de um
    KeyError difícil de rastrear.

    Returns:
        list[dict]: Cópia da lista de dicionários com todos os equipamentos.

    Raises:
        RuntimeError: Se `init_db()` não foi chamado antes desta função.
    """
    if _DB_KEY not in st.session_state:
        raise RuntimeError(
            "Banco de dados não inicializado. "
            "Certifique-se de chamar `init_db()` na inicialização do app."
        )
    return list(st.session_state[_DB_KEY])


def adicionar_equipamento(novo_dict: dict) -> None:
    """
    Persiste um novo equipamento no estado da sessão.

    O `time.sleep(1)` simula a latência de uma requisição HTTP real ao
    backend FastAPI. Mantê-lo durante o desenvolvimento permite validar
    os componentes de feedback de UX (spinners, mensagens de estado)
    antes da integração, sem precisar de um servidor em execução.

    list.append() opera in-place diretamente sobre a referência do
    session_state, dispensando reatribuição explícita.

    Args:
        novo_dict (dict): Dicionário com os dados do novo equipamento.
            Chaves obrigatórias: "TAG", "Modelo", "Fabricante",
            "Potência (kW)", "Tensão (V)".
            Chaves opcionais Sprint 2: "planta", "imagem_placa".

    Raises:
        RuntimeError: Se `init_db()` não foi chamado antes desta função.

    Example:
        >>> adicionar_equipamento({
        ...     "TAG": "EQ-004",
        ...     "Modelo": "Redutor SEW SA-30",
        ...     "Fabricante": "SEW-Eurodrive",
        ...     "Potência (kW)": 30.0,
        ...     "Tensão (V)": 380,
        ...     "planta": "Área Sul",
        ...     "imagem_placa": "https://via.placeholder.com/300x150.png?text=Placa+EQ-004",
        ... })
    """
    if _DB_KEY not in st.session_state:
        raise RuntimeError(
            "Banco de dados não inicializado. "
            "Certifique-se de chamar `init_db()` na inicialização do app."
        )

    # Latência simulada: equivale ao RTT esperado para uma chamada POST
    # ao endpoint /equipamentos do FastAPI em ambiente de produção (~800ms–1.2s).
    # Remover apenas quando a integração real estiver ativa.
    time.sleep(1)

    st.session_state[_DB_KEY].append(novo_dict)


# ---------------------------------------------------------------------------
# Funções públicas — Telemetria e Saúde (Sprint 2)
# ---------------------------------------------------------------------------


def obter_telemetria_historica(tag: str, num_leituras: int = 20) -> list[dict]:
    """
    Gera e retorna uma lista de dicionários simulando as últimas `horas`
    horas de telemetria do motor identificado por `tag`.

    Estratégia de geração (Python puro, sem numpy):
    - Os valores base variam suavemente usando seno/cosseno para simular
      o comportamento cíclico real de um motor industrial.
    - A semente do gerador aleatório é derivada da TAG para que a mesma
      TAG produza sempre a mesma série histórica dentro de uma sessão,
      garantindo consistência visual nos reruns do Streamlit.
    - Picos de anomalia são injetados em 15% dos instantes para simular
      eventos reais (sobrecarga térmica, vibração mecânica, demanda de
      corrente incomum).

    Faixas operacionais normais:
        temperatura : 40 – 75 ºC   (pico: até 92 ºC)
        vibração    : 1.0 – 4.5 mm/s (pico: até 6.8 mm/s)
        corrente    : 10 – 40 A     (pico: até 52 A)

    Args:
        tag          (str): Identificador do equipamento (ex: "EQ-001").
        num_leituras (int): Quantidade de pontos horários a gerar. Padrão: 20.
            Use pelo menos 2 para que obter_ultimas_duas_leituras() possa
            calcular deltas entre leitura atual e anterior.

    Returns:
        list[dict]: Lista de `num_leituras` dicionários, cada um com as chaves:
            - 'horario'     (str)   : Horário fictício no formato "HH:MM".
            - 'temperatura' (float) : Temperatura em ºC.
            - 'vibracao'    (float) : Vibração em mm/s.
            - 'corrente'    (int)   : Corrente elétrica em A.

    See also:
        obter_ultimas_duas_leituras() — retorna apenas os dois últimos pontos
        formatados como (atual, anterior) para cálculo direto de delta.

    Example:
        >>> historico = obter_telemetria_historica("EQ-001", num_leituras=5)
        >>> historico[0].keys()
        dict_keys(['horario', 'temperatura', 'vibracao', 'corrente'])
    """
    # Semente derivada da TAG garante séries determinísticas por equipamento.
    seed = _SEED_BASE + sum(ord(c) for c in tag)
    rng = random.Random(seed)

    # Índices em que anomalias serão injetadas (~15% dos pontos).
    anomaly_indices: set[int] = {
        i for i in range(num_leituras) if rng.random() < 0.15
    }

    registros: list[dict] = []
    hora_base = 8  # Simula início do turno às 08:00

    for i in range(num_leituras):
        horario_str = f"{(hora_base + i) % 24:02d}:00"

        # Componente senoidal: simula aquecimento gradual ao longo do turno.
        fase = math.sin(math.pi * i / max(num_leituras - 1, 1))

        if i in anomaly_indices:
            # Pico de anomalia: valores acima dos limites operacionais normais.
            temperatura = round(82.0 + rng.uniform(0.0, 10.0), 1)
            vibracao    = round(5.2 + rng.uniform(0.0, 1.6), 2)
            corrente    = int(43 + rng.randint(0, 9))
        else:
            # Operação normal com variação senoidal + ruído aleatório.
            temperatura = round(48.0 + 22.0 * fase + rng.uniform(-3.0, 3.0), 1)
            vibracao    = round(1.5 + 2.5 * fase + rng.uniform(-0.3, 0.3), 2)
            corrente    = int(14 + 22 * fase + rng.randint(-2, 2))

        registros.append(
            {
                "horario":     horario_str,
                "temperatura": temperatura,
                "vibracao":    vibracao,
                "corrente":    corrente,
            }
        )

    return registros


def obter_ultimas_duas_leituras(tag: str) -> tuple[dict, dict]:
    """
    Retorna as duas últimas leituras de telemetria para uma TAG,
    facilitando o cálculo de delta (variação) nos componentes de UI.

    Internamente chama obter_telemetria_historica(tag, num_leituras=20) e
    extrai os dois últimos pontos. Se o histórico tiver apenas 1 ponto,
    retorna o mesmo registro para atual e anterior (delta = 0).

    Args:
        tag (str): Identificador do equipamento (ex: "EQ-001").

    Returns:
        tuple[dict, dict]: (leitura_atual, leitura_anterior)
            Cada dict contém as chaves 'horario', 'temperatura',
            'vibracao' e 'corrente'.

    Example:
        >>> atual, anterior = obter_ultimas_duas_leituras("EQ-001")
        >>> delta_temp = atual['temperatura'] - anterior['temperatura']
    """
    historico = obter_telemetria_historica(tag, num_leituras=20)
    if not historico:
        _vazio = {"horario": "--:--", "temperatura": 0.0, "vibracao": 0.0, "corrente": 0}
        return _vazio, _vazio
    atual    = historico[-1]
    anterior = historico[-2] if len(historico) >= 2 else historico[-1]
    return atual, anterior


def avaliar_saude(temperatura: float, vibracao: float) -> str:
    """
    Classifica o estado de saúde operacional de um ativo com base nos
    seus últimos valores de temperatura e vibração.

    Lógica de limites (ajustada na Sprint 2):
        🔴 Crítico  — temperatura > 85 ºC  OU  vibração > 5.5 mm/s
        🟡 Alerta   — temperatura > 75 ºC  OU  vibração > 4.5 mm/s
        🟢 Saudável — demais casos

    Args:
        temperatura (float): Temperatura atual do ativo em ºC.
        vibracao    (float): Vibração atual do ativo em mm/s.

    Returns:
        str: Uma das três strings de status:
            - '🔴 Crítico'
            - '🟡 Alerta'
            - '🟢 Saudável'

    Example:
        >>> avaliar_saude(90.0, 2.5)
        '🔴 Crítico'
        >>> avaliar_saude(78.0, 4.7)
        '🟡 Alerta'
        >>> avaliar_saude(60.0, 2.0)
        '🟢 Saudável'
    """
    if temperatura > 85.0 or vibracao > 5.5:
        return "🔴 Crítico"
    if temperatura > 75.0 or vibracao > 4.5:
        return "🟡 Alerta"
    return "🟢 Saudável"
