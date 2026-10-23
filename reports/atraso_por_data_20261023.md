# Atraso por data e conferência das prévias

**Data:** 2026-10-23. **Regra:** entrega real após o dia estimado.
Corpus regenerado localmente com `python -X utf8 -m src.preprocessing.corpus`.

| Regra | Atrasadas | População entregue | Proporção | IC95% Wilson |
|---|---:|---:|---:|---|
| Horário, histórica | 4.339 | 40.303 | 10,77% | 10,47% a 11,07% |
| Data, atual | 3.813 | 40.303 | 9,46% | 9,18% a 9,75% |

O corpus tem 42.174 avaliações com comentário: 3.813 `atrasado`, 36.490
`no_prazo` e 1.871 `nao_entregue`. Período de compra dos entregues:
2016-09-15 a 2018-08-29. Os 526 casos reclassificados foram entregues no dia
prometido; `dias_atraso` e textos não mudaram. A população é de avaliações com
comentário, não de todos os pedidos.

## P01, sem novo julgamento

Cruzei os 30 `review_id` relevantes de P01 em `data/eval/julgamento.csv` com
o corpus regenerado: **15/30** dentro do filtro `atrasado`, contra 17/30
com a regra por horário. Dos demais, 9 são `no_prazo` e 6 `nao_entregue`.
Essa recontagem não é nova avaliação de P@10 nem novo julgamento humano.

## Trava das evidências

Após normalizar LF/CRLF em `digest_codigo()` e regenerar o corpus, executei
E-A, E-B e P15 com as perguntas literais e os filtros `--nota-max 2
--situacao-entrega atrasado --k 10`, sem `--executar`, no SDK 1.75.0. Os
JSON locais estão em `.venv/previa_{ea,eb,p15}_0012.json` (fora do Git).
Todos retornaram `previa_sem_api` e dez evidências.

| Caso | SHA-256 do contexto ordenado `{review_id, texto}` | Igual à referência 0011? | Novo hash da prévia |
|---|---|---|---|
| E-A | `b5a7476cb2e542bb8ee3d7868e6ea791f3f8b9ba37ebc513fc8fef67da69777e` | Sim | `28fb0e20214f31f163156580e6a1f3fddfcd18c6fa71fc890e5a607506b40a88` |
| E-B | `32f3b9da3ff5eea8b9558a1a999e2fef0ed689330adb6a1571439369374ae3a4` | Sim | `72ea2402264ac2f80a6a7c3ea043a10de4b72209b6eddb07f53b2c1435bf68ec` |
| P15 | `180e5e1745fc207995bb5fcb47bab1edb11a9defe6a02ea89ac6db504a1e0d3a` | Sim | `c53daa6570b52c72f4a9b289b7ae87d21be989beac77b7af34f9c729a8684e24` |

O fingerprint é SHA-256 do JSON canônico da lista ordenada de pares
`review_id`/`texto`, conforme `_canonico` em `src/eval/avaliar_geracao.py`.
**3/3 contextos idênticos.** Os hashes novos resultam do digest de código
normalizado; não constituem liberação para envio. Luiz deve ler as prévias e
liberar explicitamente antes de qualquer chamada real.

## Riscos verificados

Não houve chamada à API nem edição de embeddings, prompts, gabarito ou
capturas. O corpus é regenerável e permanece fora do Git. Relatórios datados
anteriores registram corretamente a regra antiga; não descrevem a regra atual.
Na auditoria PAVC: (1) entrega com estimativa ausente seria classificada
`no_prazo` pela expressão atual; há **0** desses pedidos no CSV usado, e
outra versão dos dados exigiria validar essa ausência; (2) o recorte P01
perdeu duas evidências julgadas, quantificadas acima; (3) o hash normalizado
protege só contra LF/CRLF, não contra alterações reais de código ou ambiente.
