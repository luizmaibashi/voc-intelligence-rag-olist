"""Gera o formulário local para julgar julgamento_filtros.csv (spec 0009).

A página fica em data/processed/ (fora do Git) porque traz texto de avaliações.
Abre direto no navegador, sem servidor e sem rede; o CSV baixado tem as mesmas
colunas da planilha, com `relevante` preenchido.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PLANILHA = RAIZ / "data/eval/julgamento_filtros.csv"
JULGAMENTO = RAIZ / "data/eval/julgamento.csv"
TEMPLATE = Path(__file__).with_name("julgamento_filtros_template.html")
SAIDA = RAIZ / "data/processed/julgamento_filtros_local.html"

# Critérios reconstruídos do julgamento de setembro; P09 segue o AGENTS.md.
CRITERIOS = {
    "P01": "Sim se fala de atraso ou demora na entrega, inclusive “ainda não recebi”. "
           "Não se não fala de atraso.",
    "P02": "Sim se o cliente relata que o pedido não chegou (não recebido, entrega não feita). "
           "Não se só atrasou e chegou, ou se fala de outra coisa.",
    "P09": "Sim se elogia a entrega: prazo ou rapidez, chegou inteiro, pedido correto ou elogio "
           "geral à entrega. Cumprir a data prevista conta; texto misto com elogio também é sim. "
           "Não se só reclama ou pede melhoria.",
    "P10": "Sim se o cliente se mostra satisfeito com o produto ou com a compra. "
           "Não se reclama ou relata problema.",
    "P11": "Sim se aponta um problema ou motivo de insatisfação, o que puxa nota ruim. "
           "Não se é só elogio.",
}
SEM_EXEMPLO_NAO = "(em setembro você não marcou nenhuma como 0 nesta pergunta)"
# Escolhidos à mão entre os julgamentos de setembro que seguem o critério acima.
EXEMPLOS = {
    "P01": ("Tive atraso na entrega", None),
    "P02": ("Entrega nao feita. O pedido esta como se fosse entregue mais nao recebi nada",
            "entrega fora do prazo"),
    "P09": ("Entregue muito antes do prazo! Excelente! Loja muito atenciosa com o cliente. Recomendo!",
            "Mais agilidade na entrega"),
    "P10": ("Cliente satisfeito.",
            "Produto chegou quebrado, ficaram de trocar"),
    "P11": ("O zíper é de má qualidade", "Nota 10. Entrega bem antes do prazo super indico esse site ."),
}


def _exemplo(julgamento: pd.DataFrame, pid: str, texto: str | None, valor: int, excluir: set) -> str:
    """Confere que o exemplo foi julgado com esse valor e não está na planilha atual."""
    if texto is None:
        return SEM_EXEMPLO_NAO
    achado = julgamento[(julgamento.id_pergunta == pid) & (julgamento.texto == texto)]
    if achado.empty or int(achado.relevante.iloc[0]) != valor or texto.lower() in excluir:
        raise ValueError(f"exemplo inválido em {pid}: {texto!r}")
    return texto


def montar_dados(planilha: pd.DataFrame, julgamento: pd.DataFrame) -> dict:
    faltam = set(planilha.id_pergunta) - set(CRITERIOS)
    if faltam:
        raise ValueError(f"pergunta sem critério: {sorted(faltam)}")
    excluir = set(planilha.texto.str.lower())
    perguntas = {}
    for pid, grupo in planilha.groupby("id_pergunta"):
        sim, nao = EXEMPLOS[pid]
        perguntas[pid] = {"pergunta": grupo.pergunta.iloc[0], "criterio": CRITERIOS[pid],
                          "exemplo_sim": _exemplo(julgamento, pid, sim, 1, excluir),
                          "exemplo_nao": _exemplo(julgamento, pid, nao, 0, excluir)}
    colunas = list(planilha.columns)
    itens = planilha.astype(str).to_dict("records")
    versao = hashlib.sha256(json.dumps(itens, ensure_ascii=False).encode()).hexdigest()[:12]
    return {"versao": versao, "colunas": colunas, "perguntas": perguntas, "itens": itens}


def gerar() -> Path:
    planilha = pd.read_csv(PLANILHA, sep=";", encoding="utf-8-sig", keep_default_na=False)
    julgamento = pd.read_csv(JULGAMENTO, sep=";", encoding="utf-8-sig")
    dados = json.dumps(montar_dados(planilha, julgamento), ensure_ascii=False).replace("<", "\\u003c")
    modelo = TEMPLATE.read_text(encoding="utf-8")
    if modelo.count("__DADOS_JSON__") != 1:
        raise ValueError("Modelo do formulário sem marcador único de dados.")
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(modelo.replace("__DADOS_JSON__", dados), encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
