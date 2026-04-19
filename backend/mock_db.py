"""
backend/mock_db.py
------------------
Camada de persistência simulada (in-memory) para o Challenge Sprint 1.

Decisão de arquitetura:
    st.session_state foi escolhido como mecanismo de armazenamento
    porque sobrevive a reruns do Streamlit sem exigir I/O externo,
    permitindo testar o contrato CRUD completo antes da integração
    com o backend FastAPI.

    O contrato público deste módulo (init_db / get_equipamentos /
    adicionar_equipamento) é idêntico ao que será exposto pelas
    chamadas REST futuras, isolando o frontend de qualquer detalhe
    de persistência.
"""

import time
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

# Chave única no session_state. Centralizar como constante evita conflitos
# de nome entre páginas distintas que compartilham o mesmo estado global.
_DB_KEY: str = "equipamentos_db"

# Schema explícito garante que concatenações via pd.concat respeitem a
# ordem das colunas independente da ordem dos dicts passados como entrada.
_COLUNAS: list[str] = ["TAG", "Modelo", "Fabricante", "Potência (kW)", "Tensão (V)"]


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Inicializa o banco de dados simulado no st.session_state.

    A guarda `if _DB_KEY not in st.session_state` é intencional:
    o Streamlit reexecuta o script inteiro a cada interação do usuário,
    portanto sem ela os dados seriam sobrescritos a cada rerun.
    Os registros de exemplo servem para garantir que as demais páginas
    tenham dados válidos para renderizar sem depender de cadastro prévio.

    Returns:
        None
    """
    if _DB_KEY not in st.session_state:
        dados_iniciais: list[dict] = [
            {
                "TAG": "EQ-001",
                "Modelo": "Motor WEG W22",
                "Fabricante": "WEG",
                "Potência (kW)": 75.0,
                "Tensão (V)": 380,
            },
            {
                "TAG": "EQ-002",
                "Modelo": "Bomba Centrífuga BC-40",
                "Fabricante": "KSB",
                "Potência (kW)": 15.0,
                "Tensão (V)": 220,
            },
        ]
        st.session_state[_DB_KEY] = pd.DataFrame(dados_iniciais, columns=_COLUNAS)


def get_equipamentos() -> pd.DataFrame:
    """
    Retorna cópia defensiva do DataFrame de equipamentos cadastrados.

    Retorna `.copy()` para evitar que mutações no DataFrame do chamador
    corrompam o estado global. O RuntimeError serve de contrato explícito:
    qualquer página que chame esta função sem init_db() anterior recebe
    uma mensagem acionável em vez de um KeyError difícil de rastrear.

    Returns:
        pd.DataFrame: Cópia do DataFrame com todos os equipamentos cadastrados.

    Raises:
        RuntimeError: Se `init_db()` não foi chamado antes desta função.
    """
    if _DB_KEY not in st.session_state:
        raise RuntimeError(
            "Banco de dados não inicializado. "
            "Certifique-se de chamar `init_db()` na inicialização do app."
        )
    return st.session_state[_DB_KEY].copy()


def adicionar_equipamento(novo_dict: dict) -> None:
    """
    Persiste um novo equipamento no estado da sessão.

    O `time.sleep(1)` simula a latência de uma requisição HTTP real ao
    backend FastAPI. Mantê-lo durante o desenvolvimento permite validar
    os componentes de feedback de UX (spinners, mensagens de estado)
    antes da integração, sem precisar de um servidor em execução.

    pd.concat é usado no lugar de df.append (removido no Pandas 2.0)
    e garante que o índice seja reiniciado para evitar duplicatas.

    Args:
        novo_dict (dict): Dicionário com os dados do novo equipamento.
            Chaves obrigatórias: "TAG", "Modelo", "Fabricante",
            "Potência (kW)", "Tensão (V)".

    Raises:
        RuntimeError: Se `init_db()` não foi chamado antes desta função.

    Example:
        >>> adicionar_equipamento({
        ...     "TAG": "EQ-003",
        ...     "Modelo": "Compressor Atlas Copco GA-55",
        ...     "Fabricante": "Atlas Copco",
        ...     "Potência (kW)": 55.0,
        ...     "Tensão (V)": 380,
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

    novo_df: pd.DataFrame = pd.DataFrame([novo_dict], columns=_COLUNAS)
    st.session_state[_DB_KEY] = pd.concat(
        [st.session_state[_DB_KEY], novo_df],
        ignore_index=True,
    )
