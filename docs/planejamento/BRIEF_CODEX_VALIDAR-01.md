# Brief para execução: VALIDAR-01 (gate da ficha fecha na ferramenta)

> Decidido por Luiz em 20/10/2026, antes da fase 2. Fonte do problema: ensaio de consolidação feito pelo Claude
> com as capturas da fase 1 (ficha reconstruída idêntica byte a byte à `reports/ficha_julgamento_fase1_20261020.jsonl`).

## Problema

1. `python -m src.eval.ficha_julgamento --validar` imprime `13/13 aprovados; pendentes: E01, ...` e **sai com 0**. `main()` devolve 0 sempre (`src/eval/ficha_julgamento.py:152`). Um gate que olhe o código de saída aprova por omissão. Isso viola a guarda do AGENTS.md: "item novo ausente deve falhar ou avisar, nunca aprovar por omissão".
2. E20 (`controle_local`) nunca sai de pendente. `resumir()` (`:77`) põe todo `nao_julgavel` em pendentes, e a spec 0008:41 diz "julgado separadamente" sem mecanismo. Com o item 1 corrigido, o gate 20/20 seria impossível.
3. A cópia dos 13 julgamentos da fase 1 para a ficha nova vive num script fora do repo (scratchpad do Claude). A ficha final precisa de trilha reproduzível.

## Decisão de Luiz

E20 é **julgado na ficha**. A linha `nao_julgavel` com `classe == "controle_local"` ganha o campo `julgamento_controle` (`None` ao gerar; `"S"`/`"NS"` marcado por Luiz). Outras classes `nao_julgavel` (falha de serviço, falha de contrato, saída inválida) continuam pendentes e mantêm o gate aberto.

## Restrição dura: geração congelada

A fase 2 roda hoje às 21:00 com o código atual. **Não tocar** em `src/eval/avaliar_geracao.py`, `src/rag/`, `src/demo.py`, manifesto, prompt, schema ou `requirements.txt`. O escopo é só a ferramenta de ficha, que lê capturas e não participa da geração. Se precisar mexer em qualquer outro arquivo de `src/`, pare e reporte.

## Escopo (só estes arquivos)

- `tests/test_ficha_julgamento.py`: testes novos primeiro (RED).
- `src/eval/ficha_julgamento.py`: correção.
- `scripts/copiar_julgamentos.py` (novo): a partir do script do Claude, colado no fim deste brief.
- `tests/test_copiar_julgamentos.py` (novo).
- `docs/planejamento/COMANDO_FASE2_0008.md`: só o parágrafo "Depois:", para apontar para o script e o novo código de saída.

## Ordem (TDD: teste falhando antes da correção)

1. **RED.** Escreva e rode os testes abaixo, que devem **falhar** com o código atual. Cole no relatório a saída resumida mostrando a falha.
   - `main(["--validar", ficha])` devolve **4** quando há pendente (ficha só com E02 julgado e manifesto com E01/E02).
   - `main` devolve **4** quando todos estão julgados mas um caso foi reprovado (frase `NS` com motivo válido).
   - `main` devolve **0** só quando não há pendente e todos foram aprovados.
   - `gerar` cria a linha de E20 com `julgamento_controle: None`.
   - `validar` aceita `julgamento_controle` em `{"S","NS"}` ou `None`; outro valor levanta `ValueError`.
   - `resumir`: E20 com `julgamento_controle == "S"` conta como julgado e aprovado; com `"NS"`, julgado e reprovado (motivo `controle_reprovado`); com `None`, pendente.
   - `resumir`: `nao_julgavel` de outra classe (por exemplo `falha_servico`) continua pendente, mesmo que alguém escreva `julgamento_controle` na linha. Nesse caso, `validar` levanta erro: o campo só vale para `controle_local`.
   - Testes atuais que esperam E20 em pendentes (ex.: linhas ~146, ~170, ~210, ~225) mudam só onde a premissa mudou. Explique cada alteração no relatório. Não apague teste para fazer a suíte passar.
2. **GREEN.** Faça a correção mínima em `ficha_julgamento.py`:
   - código 0 = gate fechado (nenhum pendente e `aprovados == n_julgados == número de casos do manifesto`); código 4 = ficha válida com gate aberto. Erro de estrutura continua levantando exceção, como hoje;
   - confira que nenhum outro CLI do projeto já usa o código 4 (`git grep -n "return 4\|SystemExit(4)"`);
   - a saída impressa continua igual, com mais uma linha final: `gate: fechado` ou `gate: aberto (pendentes: ...; reprovados: ...)`.
3. **Script de cópia.** Leve `copiar_julgamentos.py` para `scripts/` sem mudar o comportamento e acrescente a regra de E20: linha `nao_julgavel`/`controle_local` copia `julgamento_controle` por `(id, None)`. Testes em `tests/test_copiar_julgamentos.py`:
   - cópia de frases por `(id, ordem)` e de recusa por `id` reproduz a ficha de origem byte a byte (fixture pequena);
   - frase diferente na mesma `(id, ordem)`: sai com código diferente de zero, mensagem com `PARE` e **sem criar** o arquivo de saída;
   - caso julgado ausente na ficha nova: mesmo comportamento;
   - saída já existente: recusa sobrescrever;
   - ids novos ficam sem julgamento e aparecem em `ids sem julgamento`.
4. **Ensaio real** (só leitura, sem API), na raiz do projeto com `$env:PYTHONPATH = '.venv/sdk175'`:
   - gere uma ficha com as 8 capturas da fase 1 listadas em `COMANDO_FASE2_0008.md` (`--saida` num caminho temporário fora de `reports/`);
   - copie os julgamentos de `reports/ficha_julgamento_fase1_20261020.jsonl` com o script novo;
   - compare com a ficha aprovada: precisa ser **idêntica**;
   - rode `--validar` sobre ela: esperado `13/13 aprovados`, pendentes E01, E05, E13, E16, E17, E19, E20, `gate: aberto` e **código 4**.
   - Não grave nada em `reports/`.
5. Suíte completa com o comando do README (basetemp novo). Informe passou/falhou e a contagem.

## Relatório (formato de README-01)

`TAREFA`, `ARQUIVOS` (`git show --stat HEAD`), `TESTES` (RED antes, GREEN depois, ensaio real com código de saída, suíte), `CRITÉRIO DE ACEITE`, `NÃO VERIFICADO`. Commit em Conventional Commits, **sem** `Co-Authored-By`; `git pull --rebase origin main` antes do push. Se o relógio passar das 21:00 antes do push, faça o push assim mesmo: o código desta tarefa não participa da geração, mas registre o horário no relatório.

## Pronto quando

`--validar` devolve 0 só com gate fechado; E20 é julgável na ficha; o script de cópia está em `scripts/` com teste; o ensaio real reproduz a ficha aprovada e devolve 4; nenhum arquivo de geração foi tocado.

## Anexo: script atual (scratchpad do Claude)

```python
"""Copia julgamentos da ficha antiga para a nova por (id, ordem), exigindo frase idêntica.

Uso: python copiar_julgamentos.py <ficha_antiga> <ficha_nova_sem_julgamento> <saida>
Sai com código 1 se alguma frase julgada não existir ou diferir na ficha nova.
"""
import json
import sys
from pathlib import Path

CAMPOS = {"frase": ("julgamento", "motivo", "nota"), "sem_evidencia": ("julgamento_caso",)}


def ler(caminho):
    return [json.loads(l) for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]


def chave(r):
    # frase: (id, ordem); recusa sem_evidencia: um registro por caso
    return (r["id"], r.get("ordem"))


antiga, nova, saida = sys.argv[1:4]
if Path(saida).exists():
    sys.exit(f"recuso sobrescrever {saida}")

julgados = {chave(r): r for r in ler(antiga)}
linhas = ler(nova)
por_chave = {chave(r): r for r in linhas}

erros = []
for k, velho in julgados.items():
    novo = por_chave.get(k)
    if novo is None:
        erros.append(f"{k}: ausente na ficha nova")
    elif velho["tipo"] not in CAMPOS:
        erros.append(f"{k}: tipo {velho['tipo']} sem regra de cópia")
    elif novo.get("tipo") != velho["tipo"] or novo.get("frase") != velho.get("frase"):
        erros.append(f"{k}: tipo/frase diferente\n  antiga: {velho['tipo']} {velho.get('frase')!r}\n  nova:   {novo.get('tipo')} {novo.get('frase')!r}")
if erros:
    sys.exit("PARE:\n" + "\n".join(erros))

copiados = 0
for r in linhas:
    velho = julgados.get(chave(r))
    if velho:
        for c in CAMPOS[velho["tipo"]]:
            r[c] = velho.get(c)
        copiados += 1

Path(saida).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in linhas), encoding="utf-8")
pendentes = sorted({r["id"] for r in linhas
                    if r["tipo"] in CAMPOS and r.get(CAMPOS[r["tipo"]][0]) is None})
print(f"copiados {copiados}/{len(julgados)}; linhas {len(linhas)}; ids sem julgamento: {','.join(pendentes) or '-'}")
```
