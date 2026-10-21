"""Copia julgamentos entre fichas por (id, ordem), exigindo frase idêntica."""
import json
import sys
from pathlib import Path

CAMPOS = {"frase": ("julgamento", "motivo", "nota"),
          "sem_evidencia": ("julgamento_caso",),
          "controle_local": ("julgamento_controle",)}


def ler(caminho):
    return [json.loads(l) for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]


def chave(r):
    return (r["id"], r.get("ordem"))


def regra(r):
    return "controle_local" if r["tipo"] == "nao_julgavel" and r.get("classe") == "controle_local" else r["tipo"]


def main(argv=None):
    antiga, nova, saida = (sys.argv[1:] if argv is None else argv)
    if Path(saida).exists():
        print(f"recuso sobrescrever {saida}", file=sys.stderr)
        return 1
    julgados = {chave(r): r for r in ler(antiga)
               if regra(r) in CAMPOS and r.get(CAMPOS[regra(r)][0]) is not None}
    linhas = ler(nova)
    por_chave = {chave(r): r for r in linhas}
    erros = []
    for k, velho in julgados.items():
        novo = por_chave.get(k)
        if novo is None:
            erros.append(f"{k}: ausente na ficha nova")
        elif regra(novo) != regra(velho) or novo.get("frase") != velho.get("frase"):
            erros.append(f"{k}: tipo/frase diferente\n  antiga: {velho['tipo']} {velho.get('frase')!r}\n  nova:   {novo.get('tipo')} {novo.get('frase')!r}")
    if erros:
        print("PARE:\n" + "\n".join(erros), file=sys.stderr)
        return 1
    copiados = 0
    for r in linhas:
        velho = julgados.get(chave(r))
        if velho:
            for c in CAMPOS[regra(velho)]:
                r[c] = velho.get(c)
            copiados += 1
    with Path(saida).open("x", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in linhas))
    pendentes = sorted({r["id"] for r in linhas
                        if regra(r) in CAMPOS and r.get(CAMPOS[regra(r)][0]) is None})
    print(f"copiados {copiados}/{len(julgados)}; linhas {len(linhas)}; ids sem julgamento: {','.join(pendentes) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
