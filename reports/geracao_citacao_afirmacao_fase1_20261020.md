# Rodada de citação por afirmação — fase 1, reavaliação de 20/10 UTC

**Configuração:** `google-genai 1.75.0` (`PYTHONPATH=.venv/sdk175`), hash `203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`, até duas tentativas transitórias, teto 20/dia UTC. **Escopo autorizado:** uma reavaliação de E02, E03, E04, E06–E12 (`--reavaliar-falhas-locais`) e primeira execução de E14, E15, E18. Captura de origem preservada: `reports/geracao_citacao_afirmacao_fase1_20261019.jsonl` (SHA-256 `44c87c8f…a199`).

## Previsões de Luiz para esta fase (registradas 2026-10-20T13:25Z, antes de qualquer envio do dia)

| Pergunta | Previsão |
|---|---|
| Casos julgáveis dos 13 | 10 |
| Falhas de contrato entre julgáveis (`N_pareado`) | 2 |
| Chamadas gastas no dia | 16 (primeira resposta foi 1, fora do domínio 13–20; corrigida após explicação de que 10 julgáveis implicam 3 falhas de serviço × 2 tentativas) |
| `sem_evidencia` | 1 |

Previsões do lote completo, passadas ao CLI: 17/20 sustentados, `N=3`.

## Pré-checagem sem API (13:10–13:25Z)

- `main` = `origin/main` em `9b4123e`; hash recalculado com SDK 1.75.0: `203ec…fae3`. O Python do sistema sem `PYTHONPATH` usa SDK 1.73.1 (hash `ab83…`, não liberado); `.venv/Scripts/python.exe` não existe neste PC.
- Ledger: 10 envios e 10 resultados `falha_servico` (2 tentativas) em 19/10 UTC para os 10 IDs; nada para E14/E15/E18; `chamadas_no_dia` = 0/20.
- O avaliador retorna 0 mesmo com `falha_servico` e não interrompe após `ConnectError` seguidos: E1 roda só E02 e o avanço depende de checagem da captura.

## Sequência

P2 (SDK/hash) → P3 (cota) → P4 (DNS/TLS) → E1 (E02) → CHK → P3 → E2 (9 restantes) → CHK → P3 → E3 (E14, E15, E18) → CHK → P3.

## Resultado

**E1 (E02, ~13:35Z):** P2 ok (SDK 1.75.0, hash `203ec…`), cota 0/20, `DNS_OK 16`, `TLS_OK TLSv1.3`. E02 sem saída: tentativa 1 `ServerError 504` após 24,5 s; tentativa 2 `ServerError 503` após 0,95 s (espera planejada 2 s). Classe `falha_servico`, cota 2/20. Diferente de 19/10: a conexão chegou ao servidor do Gemini (`gemini-3.1-flash-lite`), que respondeu indisponível. A evidência aponta indisponibilidade do provedor, não rede local. E02 consumiu seu único reenvio autorizado e segue **pendente**; resolvê-lo exige nova decisão de Luiz. Captura: `reports/geracao_citacao_afirmacao_f1_e1_e02_20261020.jsonl`. E2/E3 não executados.

**Canário E03 (13:56Z):** 1 tentativa, 20,9 s, saída do provedor, `respondida`, classe `respondida_pendente_julgamento`. Cota 3/20. Captura: `reports/geracao_citacao_afirmacao_f1_canario_e03_20261020T1356.jsonl`. Restante dos 10 liberado em lotes de 4 (E04, E06–E08) e 4 (E09–E12), com parada se algum caso ficar sem saída.

**Lote A (14:08Z, E04, E06, E07, E08):** 4/4 com saída, todos `respondida`; E07 teve `503` na 1ª tentativa e saída na 2ª. Cota 8/20. Captura: `reports/geracao_citacao_afirmacao_f1_e04-e06-e07-e08_20261020T1408.jsonl`.

**Lote B (14:20Z, E09–E12):** 4/4 com saída na 1ª tentativa, todos `respondida`. Cota 12/20. Captura: `reports/geracao_citacao_afirmacao_f1_e09-e10-e11-e12_20261020T1420.jsonl`.

**Lote C (14:21Z, E14, E15, E18, primeira execução):** E14 e E15 `sem_evidencia` válidas, status compatível com o esperado (classe `recusa`). E18 sem saída: `ReadTimeout` (25,0 s) e depois `503` (22,1 s), `falha_servico`. Cota final do dia **16/20**. Captura: `reports/geracao_citacao_afirmacao_f1_e14-e15-e18_20261020T1421.jsonl`.

## Fechamento da fase 1 (20/10 UTC)

| Classe | IDs | n |
|---|---|---|
| `respondida`, pendente de julgamento frase a frase | E03, E04, E06, E07, E08, E09, E10, E11, E12 | 9 |
| `sem_evidencia` válida, status esperado compatível | E14, E15 | 2 |
| Falha de serviço pendente (sem saída) | E02 (504/503, reenvio autorizado esgotado), E18 (timeout/503, primeira execução) | 2 |
| Falha de contrato | — | 0 |

- **Falhas de contrato:** `N = 0/11` julgáveis, IC95% Wilson **[0%; 25,9%]**. Casos escolhidos intencionalmente; não estima confiabilidade geral.
- **Pareado com a baseline (rodada 04, `B_pareado = 0`):** `N_pareado = 0`, `n_pareado = 11`; excluídos E02 e E18 (falha de serviço). Limiar de abandono (`N_pareado ≥ 3`) **não atingido**. Como só restam 2 casos pareáveis pendentes, `N_pareado ≤ 2` em qualquer desfecho: o limiar já não pode ser atingido na fase 1.
- **Fase 1 incompleta:** 11/13 concluídos. O avaliador bloqueia os sete da fase 2 enquanto os 13 pareáveis não estiverem concluídos (`avaliar_geracao.py:248`). E02 e E18 não têm reenvio disponível no mecanismo atual; resolvê-los exige decisão de Luiz e mudança autorizada. Falha de serviço pendente em 25/10 deixa o gate não aprovado.
- **Sem julgamento semântico:** “julgável” não significa sustentado. As 9 `respondida` têm 1 afirmação cada; suporte e adequação das recusas ficam para o julgamento de Luiz.
- **Integridade:** captura de 19/10 preservada (SHA-256 `44c87c8f5ad60531…`); ledger apenas acrescido; hash do lote inalterado.

### Previsão × resultado

| Pergunta | Previsão | Resultado |
|---|---|---|
| Julgáveis dos 13 | 10 | 11 |
| `N_pareado` | 2 | 0 |
| Chamadas gastas | 16 | 16 |
| `sem_evidencia` | 1 | 2 (ambas esperadas) |

Observação: as 3 falhas de serviço implícitas na previsão viraram 2 pendentes e 1 transitória recuperada (E07). Todas as falhas de hoje vieram do provedor (`503`/`504`/timeout), com DNS e TLS ok.
