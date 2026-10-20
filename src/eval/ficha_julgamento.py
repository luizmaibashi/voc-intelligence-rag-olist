"""Prepara a ficha; suporte das frases é decisão humana do Luiz, não deste script."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MANIFESTO = RAIZ / "data/eval/geracao_casos.json"
MOTIVOS = {"TROCA", "EXTRAPOLA", "COMPOSTA", "SEM_BASE"}


def _jsonl(caminho: Path) -> list[dict]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines()
            if linha.strip()]


def gerar(capturas: list[Path], saida: Path, manifesto: Path = MANIFESTO) -> list[dict]:
    """Usa o caso da captura mais recente por UTC; empates seguem a ordem de entrada."""
    casos_manifesto = {c["id"]: c for c in json.loads(manifesto.read_text(encoding="utf-8"))["casos"]}
    recentes: dict[str, tuple[datetime, int, dict]] = {}
    for indice, captura in enumerate(capturas):
        registros = _jsonl(captura)
        cabecalho = next((r for r in registros if r.get("tipo") == "cabecalho"), None)
        utc = datetime.fromisoformat(cabecalho["utc"]) if cabecalho else datetime.min.replace(tzinfo=timezone.utc)
        if utc.tzinfo is None:
            raise ValueError(f"Cabeçalho sem fuso UTC: {captura}")
        for registro in registros:
            if registro.get("tipo") == "caso":
                cid = registro["id"]
                if cid not in casos_manifesto:
                    raise ValueError(f"ID ausente do manifesto: {cid}")
                if cid not in recentes or (utc, indice) >= recentes[cid][:2]:
                    recentes[cid] = (utc, indice, registro)
    linhas = []
    for cid, (_, _, registro) in recentes.items():
        caso = casos_manifesto[cid]
        status = registro.get("resposta_aplicacao", {}).get("status")
        base = {"id": cid, "status": status, "status_esperados": caso["status_esperados"]}
        classe = registro.get("classe_operacional")
        if cid == "E20" or classe in {"falha_servico", "falha_integracao", "falha_contrato", "truncamento_observado"} or status not in {"respondida", "sem_evidencia"}:
            linhas.append({**base, "tipo": "nao_julgavel", "classe": "controle_local" if cid == "E20" else (classe or "saida_invalida")})
        elif status == "sem_evidencia":
            linhas.append({**base, "tipo": "sem_evidencia", "julgamento_caso": None})
        else:
            textos = {e["review_id"]: e["texto"] for e in caso["evidencias"]}
            afirmacoes = registro["resposta_aplicacao"].get("afirmacoes", [])
            if not afirmacoes:
                raise ValueError(f"Respondida sem afirmações: {cid}")
            for ordem, afirmacao in enumerate(afirmacoes, 1):
                ids = afirmacao["review_ids"]
                if not ids or any(rid not in textos for rid in ids):
                    raise ValueError(f"Fonte inválida na afirmação {cid}/{ordem}")
                linhas.append({**base, "tipo": "frase", "ordem": ordem,
                               "frase": afirmacao["frase"], "review_ids": ids,
                               "avaliacoes": [{"review_id": rid, "texto": textos[rid]} for rid in ids],
                               "julgamento": None, "motivo": None, "nota": ""})
    with saida.open("x", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
    return linhas


def resumir(linhas: list[dict], ids_esperados: set[str] | None = None) -> dict:
    """Computa o resultado explícito por caso; ausência de ficha permanece pendente."""
    por_caso: dict[str, list[dict]] = defaultdict(list)
    for linha in linhas:
        por_caso[linha["id"]].append(linha)
    aprovados, julgados, pendentes, reprovados = [], [], [], []
    for cid, grupo in por_caso.items():
        tipos = {l["tipo"] for l in grupo}
        if len(tipos) != 1:
            raise ValueError(f"Tipos misturados no caso {cid}")
        tipo = grupo[0]["tipo"]
        if tipo == "nao_julgavel":
            pendentes.append(cid)
            continue
        if tipo == "frase":
            if any(l["julgamento"] is None for l in grupo):
                pendentes.append(cid)
                continue
            passou = all(l["julgamento"] == "S" for l in grupo) and "respondida" in grupo[0]["status_esperados"]
            razao = "NS" if any(l["julgamento"] == "NS" for l in grupo) else "status_incompativel"
        elif tipo == "sem_evidencia":
            if grupo[0]["julgamento_caso"] is None:
                pendentes.append(cid)
                continue
            passou = grupo[0]["julgamento_caso"] == "S" and "sem_evidencia" in grupo[0]["status_esperados"]
            razao = "recusa_indevida" if "respondida" in grupo[0]["status_esperados"] else "recusa_reprovada"
        else:
            raise ValueError(f"Tipo desconhecido: {tipo}")
        julgados.append(cid)
        (aprovados if passou else reprovados).append({"id": cid, "motivo": "aprovado" if passou else razao})
    pendentes.extend(sorted((ids_esperados or set()) - por_caso.keys()))
    return {"aprovados": len(aprovados), "n_julgados": len(julgados),
            "pendentes": pendentes, "resultados": aprovados + reprovados}


def validar(caminho: Path, manifesto: Path = MANIFESTO) -> dict:
    linhas = _jsonl(caminho)
    if not linhas:
        raise ValueError("Ficha vazia; nenhum caso pode ser aprovado por omissão")
    casos_manifesto = {c["id"]: c for c in json.loads(manifesto.read_text(encoding="utf-8"))["casos"]}
    ordens: set[tuple[str, int]] = set()
    for linha in linhas:
        cid = linha.get("id")
        if cid not in casos_manifesto or linha.get("status_esperados") != casos_manifesto[cid]["status_esperados"]:
            raise ValueError(f"Caso ou status esperado fora do manifesto: {cid}")
        tipo = linha.get("tipo")
        if tipo == "frase":
            chave = (cid, linha["ordem"])
            if chave in ordens:
                raise ValueError(f"Frase duplicada: {cid}/{linha['ordem']}")
            ordens.add(chave)
            referencia = f"{linha['id']}/{linha['ordem']}: {linha['frase']}"
            julgamento = linha.get("julgamento")
            motivo = linha.get("motivo")
            if julgamento not in {"S", "NS"}:
                raise ValueError(f"Frase sem julgamento válido: {referencia}")
            if julgamento == "NS" and motivo not in MOTIVOS:
                raise ValueError(f"NS exige motivo válido: {referencia}")
            if julgamento == "S" and motivo is not None:
                raise ValueError(f"S proíbe motivo: {referencia}")
        elif tipo == "sem_evidencia":
            if linha.get("julgamento_caso") not in {"S", "NS"}:
                raise ValueError(f"Recusa sem julgamento válido: {linha.get('id')}")
        elif tipo != "nao_julgavel":
            raise ValueError(f"Tipo desconhecido: {tipo}")
    return resumir(linhas, set(casos_manifesto))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--gerar", action="store_true")
    modo.add_argument("--validar", type=Path)
    parser.add_argument("--capturas", nargs="+", type=Path)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args(argv)
    if args.gerar:
        if not args.capturas or args.saida is None:
            parser.error("--gerar exige --capturas e --saida")
        linhas = gerar(args.capturas, args.saida)
        print(f"Ficha gerada: {len(linhas)} linhas em {args.saida}")
    else:
        resumo = validar(args.validar)
        print(f"{resumo['aprovados']}/{resumo['n_julgados']} aprovados; pendentes: {', '.join(resumo['pendentes']) or 'nenhum'}")
        for resultado in resumo["resultados"]:
            print(f"{resultado['id']}: {resultado['motivo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
