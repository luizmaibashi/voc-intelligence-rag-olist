# Votos de Luiz, fase 2 (2026-10-20 ~21:30 local)

- E01 S
- E05 S (nota: "anúncio" vem da pergunta, fonte diz só "foto"; não afirma anúncio enganoso)
- E13 S
- E16 S (voto inicial NS "não existe nada relacionado"; revisto para S após desafio do Claude: a razão apoia a recusa)
- E17 NS: recusa indevida; "muito demorada a entrega" sustentaria negativa citada. Baseline (spec 0006:235) respondeu E17 corretamente: regressão.
- E19 S
- E20 S (comentário inicial esperava retrieval de atraso; revisto após desafio: contexto vazio por desenho, eval isola geração)

Resultado: 19/20 aprovados (IC95% Wilson 76,4–99,1%); fase 2 6/7 (48,7–97,4%). Falhas de contrato: 0.
Previsão: 7/7 (errou por 1, E17), recusas 4/4 (acertou).

## Trilha da ficha oficial (2026-10-20)

Ficha: `reports/ficha_julgamento_oficial_20261020.jsonl` (21 linhas, sha256 `8d360399063d6fe45e78f2e46e399548870aa0d5c55c5744cf7569dc830d3646`).

1. `python -m src.eval.ficha_julgamento --gerar` com as 10 capturas de `COMANDO_FASE2_0008.md` (8 da fase 1 + `fase2_lote1`, `fase2_lote2`), saída temporária fora de `reports/`.
2. `python scripts/copiar_julgamentos.py reports/ficha_julgamento_fase1_20261020.jsonl <gerada> <copiada>`: `copiados 14/14` (13 casos, 14 frases); sem julgamento E01, E05, E13, E16, E17, E19, E20.
3. Votos acima aplicados só nos campos vazios: frases de E01/E05 `julgamento: "S"` (nota de E05 copiada daqui); `julgamento_caso` de E13/E16/E19 `S` e de E17 `NS`; `julgamento_controle` de E20 `S`. Nenhum julgamento copiado foi alterado.
4. `python -m src.eval.ficha_julgamento --validar reports/ficha_julgamento_oficial_20261020.jsonl` → `19/20 aprovados; pendentes: nenhum`, `E17: recusa_indevida`, `gate: aberto (pendentes: nenhum; reprovados: E17)`, **código 4**.
