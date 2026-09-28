"""Baseline conservador de elogios explícitos à entrega; requer avaliação externa."""
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class RotuloElogio:
    temas: frozenset[str]
    misto: bool


def _normalizar(texto: str) -> str:
    sem_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto.lower())
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sem_acentos).strip()


DIVISOES = re.compile(r"[.!?;,]|\b(?:mas|porem|fora isso|no entanto|contudo)\b")
NEGATIVO = re.compile(
    r"\b(?:nao|nunca|jamais|demor\w*|atras\w*|falt\w*|amassad\w*|"
    r"quebrad\w*|errad\w*|avariad\w*|arriscad\w*|lent\w*|ruim|"
    r"decepcion\w*|pessim\w*|horriv\w*)\b"
)
CHEGADA = r"\b(?:entreg\w*|entrag\w*|cheg\w*|receb\w*|vei\w*)\b"
PRAZO_POSITIVO = re.compile(
    rf"{CHEGADA}.{{0,50}}\b(?:rapid\w*|antes\s+(?:do\s+prazo|da\s+data|do\s+previsto|"
    r"do\s+combinado)|dentro\s+do\s+prazo|no\s+prazo|na\s+data\s+prevista|"
    r"antecipad\w*|(?:em\s+)?menos\s+de\s+[12]\s+dias?)\b|"
    r"\b(?:pontual\w*|cumprimento\s+do\s+prazo)\b|"
    r"\bprazo\b.{0,35}\b(?:antecipad\w*|cumprid\w*|muito\s+antes)\b|"
    rf"\brapid\w*\b.{{0,25}}{CHEGADA}|"
    r"\b(?:muito\s+bom|otim\w*|excelente)\b.{0,40}\bprazo\s+de\s+entrega\b"
)
INTEGRIDADE = re.compile(
    rf"{CHEGADA}.{{0,50}}\b(?:intact\w*|inteir\w*|perfeit\w*\s+condic\w*|"
    r"perfeito\s+estado|sem\s+avaria\w*|bem\s+embalad\w*)\b"
)
PEDIDO_CORRETO = re.compile(
    rf"{CHEGADA}.{{0,50}}"
    r"\b(?:certinho|corret\w*|completo|conforme\s+(?:o\s+)?(?:pedido|comprado)|"
    r"conforme\s+(?:o\s+)?anunciad\w*|"
    r"de\s+acordo\s+com\s+(?:o\s+)?(?:pedido|comprado))\b"
)
GERAL = re.compile(
    r"\bentreg\w*\b.{0,25}\b(?:boa|excelente|otim\w*|perfeit\w*|garantid\w*)\b|"
    r"\b(?:boa|excelente|otim\w*|perfeit\w*)\s+entreg\w*\b|"
    r"\b(?:tudo\s+perfeito|excelente\s+(?:o\s+)?processo\s+de\s+compra)\b"
    r".{0,45}\bentreg\w*\b"
)


def classificar_elogio(texto: str) -> RotuloElogio:
    """Devolve temas detectados; ausência de tema não prova ausência de elogio."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("A avaliação precisa de texto não vazio.")
    temas: set[str] = set()
    negativo = False
    for trecho in DIVISOES.split(_normalizar(texto)):
        if NEGATIVO.search(trecho):
            negativo = True
            continue
        if PRAZO_POSITIVO.search(trecho):
            temas.add("prazo_rapidez")
        if INTEGRIDADE.search(trecho):
            temas.add("integridade")
        if PEDIDO_CORRETO.search(trecho):
            temas.add("pedido_correto")
        if not temas and GERAL.search(trecho):
            temas.add("elogio_geral")
    return RotuloElogio(frozenset(temas), bool(temas) and negativo)
