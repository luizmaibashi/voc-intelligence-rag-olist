# Latência observada nas capturas da rodada 04

**Previsão de Luiz antes da medição (2026-10-23):** mediana de tentativa
bem-sucedida entre 2 e 5 segundos.

**Fonte e método:** `reports/geracao_20261006_evidencias.json`, campo
`rodadas[3].registros_originais` (rodada 04 da configuração entregue).
Selecionamos `tipo = tentativa` e `erro_integracao = null`; calculamos a
mediana de `duracao_ms` em Python (`statistics.median`). A operação não fez
novas chamadas de API. A captura contém 25 tentativas: 18 concluídas sem
erro de integração e 7 com erro. E20 é controle local e não tem chamada.

| Indicador | Observado |
|---|---:|
| Mediana das 18 tentativas sem erro | **5.319,5 ms (5,32 s)** |
| Mínimo e máximo nessas 18 | 925 ms e 18.297 ms |
| Mediana das 25 tentativas, incluindo erros | 5.954 ms |

A mediana sem erro ficou **0,32 s acima** do limite superior previsto. Isto
mede somente a chamada ao gerador conforme `src/rag/tentativas.py`; não inclui
carregar pesos, gerar vetores, buscar, revisar a prévia, espera entre tentativas
ou tempo total percebido pelo usuário. Casos foram escolhidos para avaliação,
não amostrados de tráfego real. O intervalo mínimo–máximo mostra dispersão
observada, não intervalo de confiança ou SLA. As capturas não registram tokens;
portanto, não permitem calcular custo por resposta.
