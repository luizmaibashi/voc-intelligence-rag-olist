# Spec 0008 — Contrato de citação por afirmação

**Data:** 2026-10-18. **Status:** contrato aprovado por Luiz em 18/10/2026, com revisão 2 e quatro ajustes; implementação local e testes sem API concluídos, diff pendente de revisão humana. **Dono do julgamento e do merge:** Luiz Maibashi. **Decisão:** ADR 0008. **Baseline imutável:** tag `cfg-citacao-por-resposta` (`fe652b6`).

## Objetivo e hipótese

O gestor deve conseguir abrir a fonte de cada afirmação da resposta, localizar erro e decidir correção no ponto exato. Hipótese: a auditoria por par frase–fonte custa menos que conferir uma resposta com lista global de IDs. Esta mudança não promete resposta mais correta. O ganho de tempo/ROI não foi medido.

## Contrato proposto

Saída do provedor: `status` em `{respondida, sem_evidencia}`, `limitacao` (string) e `afirmacoes` (lista de objetos `{frase: string, review_ids: list[str]}`). Não há `review_ids` global nem `texto` livre na configuração nova.

| Estado | `limitacao` do provedor | `afirmacoes` | Texto exibido pela aplicação |
|---|---|---|---|
| `respondida` | Ignorada: registrada no JSONL, nunca exibida, não gera erro | Uma ou mais, na ordem de leitura | Concatenação das `frase` validadas, sem síntese livre adicional |
| `sem_evidencia` | Explicação livre opcional, registrada, nunca exibida como fato | Lista vazia | Mensagem local fixa: “As avaliações recuperadas não sustentam a resposta solicitada.” |

O schema não expressa obrigatoriedade condicional por estado. Rejeitar `respondida` por um campo não exibido consumiria cota sem melhorar a auditoria; instrução para deixá-lo vazio não é garantia.

Para `respondida`, cada `frase` deve ser string não vazia após `strip`, cada lista `review_ids` deve ter **ao menos um** ID string não vazio, e todos os IDs devem pertencer ao contexto recuperado. ID duplicado dentro de uma frase é normalizado sem alterar a ordem; frases iguais não são fundidas automaticamente. Qualquer par inválido invalida a **resposta inteira** como `erro_geracao`, sem exibir parcialmente uma afirmação. Contexto vazio continua `sem_evidencia`; falha da API, JSON/estado/estrutura inválidos continuam `erro_geracao`. Uma `sem_evidencia` com afirmações vira `erro_geracao`. `responder()` valida presença e vínculo estrutural, **não** verifica suporte semântico.

A instrução pede **uma alegação verificável por item**. Isso não é garantia: se uma frase contiver mais de uma alegação e qualquer parte não tiver suporte, Luiz a julga não sustentada.

A resposta de aplicação expõe `status`, `texto` montado, `afirmacoes` validadas e, se necessário para localizar fontes no CLI, uma lista derivada de IDs únicos. Essa lista derivada não é campo de entrada nem critério de aprovação factual. CLI e JSONL exibem/registram cada frase com seus IDs e textos integrais correspondentes, `limitacao` bruta, tentativas, motivo de término quando disponível e hash. Históricos da configuração anterior permanecem legíveis sem conversão retroativa.

O JSON por afirmação pode exceder `max_output_tokens=512`. Registrar `finish_reason` ou equivalente quando o SDK devolver esse dado. JSON inválido só é classificado como **truncamento observado** quando o motivo de término sustentar essa conclusão; sem motivo disponível, registrar JSON inválido com motivo indisponível. Falha anterior à resposta também admite motivo indisponível. Em teste com cliente falso, registrar o tamanho de uma saída típica de 3–5 afirmações. Alterar o limite exige decisão explícita de Luiz e novo hash.

## Escopo e compatibilidade

Alterar `SCHEMA_RESPOSTA` e `INSTRUCAO` em `src/rag/provedor_gemini.py`; validação e representação em `src/rag/responder.py`; apresentação e registro em `src/demo.py`; integração do avaliador E01–E20 em `src/eval/avaliar_geracao.py`. O executor histórico `src/eval/reavaliar_e05.py` continua preso ao hash antigo e deve bloquear replay no contrato novo; uma reavaliação focal nova pode usar o avaliador com `--ids E05`, preservando manifesto/hash completos e saída nova. Atualizar testes desses pontos e documentação contratual necessária. `src/rag/liberacao.py` já inclui schema/instrução por `configuracao_execucao()` e digests no hash; teste deve demonstrar que um hash da tag baseline falha para a configuração nova antes de cliente/API.

Fora do escopo: trocar MiniLM, DuckDB, Gemini, temperatura, política de repetição, corpus, filtros, numerador/denominador da contagem, aumentar teto diário ou enviar comentários novos. Nenhum payload real será enviado só porque esta spec foi aprovada: cada contexto/configuração precisa da prévia, revisão de PII e liberação explícita conforme `AGENTS.md` e spec 0007.

## Falhas e parada antecipada

| Classe | Exemplos | Entra na parada? |
|---|---|---|
| Serviço | HTTP transitório, timeout ou rede após a política atual de até duas tentativas | Não; impede julgamento até reavaliação |
| Contrato | JSON inválido, truncamento observado, estado/estrutura inválidos, ID fora do contexto ou par inválido | Sim |
| Recusa | `sem_evidencia` válida | Não; exige julgamento de adequação |
| Controle local | E20 | Não; julgado separadamente |

Falha de contrato não aciona repetição. **Antes de qualquer chamada nova**, levantar `B` nas primeiras tentativas históricas de E01–E20 cujo schema **e** instrução sejam iguais aos da tag `cfg-citacao-por-resposta`. Identificar as capturas, hashes e contrato usados. Se nenhuma rodada bater integralmente, declarar cada diferença e a limitação da comparação; não escolher silenciosamente uma rodada aproximada. Casos sem saída por falha de serviço saem do denominador: reportar `B/n_julgáveis`, com `n_julgáveis` definido e os casos excluídos listados. Não misturar o controle local E20 com falhas externas de contrato.

**Baseline apurado em 18/10, após previsão de Luiz de cerca de 4 falhas:** `reports/geracao_20261006_evidencias.json`, `rodadas[3]` (rodada 04; hash `8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0`). Comparei `schema` e `prompt` do cabeçalho aos literais de `src/rag/provedor_gemini.py` na tag via `git show`: ambos idênticos. A rodada 04 também usa a política de até duas tentativas da tag; a contagem considera **só a primeira**. E01, E05, E13, E16, E17 e E19 tiveram falha de serviço nessa tentativa e saem do denominador; E20 é controle local. Nos demais E02–E04, E06–E12, E14, E15 e E18, `B = 0/13` falhas estruturais (IC95% Wilson **[0%; 22,8%]**). São casos escolhidos intencionalmente, não estimativa de confiabilidade geral. A regra pareada `B_pareado + 3` se aplica apenas a esses 13 IDs que também tiverem saída julgável nova; como todos tinham contrato válido no baseline, `B_pareado = 0` em qualquer subconjunto deles. Uma falha de serviço nova retira o caso do pareamento até resolução autorizada.

Na primeira passada nova, executar **primeiro** `--ids E02,E03,E04,E06,E07,E08,E09,E10,E11,E12,E14,E15,E18`. Concluir os 13 casos dessa fase, ainda que a cota de 20 chamadas/dia UTC obrigue a continuar no dia seguinte; até lá, nenhum dos outros sete pode ser enviado. Ao concluir, se `N_pareado ≥ 3`, parar, registrar abandono na ADR e usar a tag baseline. Se `N_pareado < 3`, executar `E01,E05,E13,E16,E17,E19,E20`, com parada total em cinco falhas de contrato. Falha de serviço não conta como falha de contrato, mas continua pendente para o gate. Reportar `N` e os **13 casos atribuídos** na primeira fase; para proporção e IC95%, usar `N/n_julgáveis` e listar falhas de serviço excluídas, sem chamar uma fase parcial de `n=13`. A comparação pareada usa somente casos julgáveis em ambas as configurações; informar `B_pareado`, `N_pareado`, `n_pareado` e exclusões. Os limiares são tolerância operacional definida antes da medição, não teste de significância; os casos foram escolhidos intencionalmente.

## Avaliação e critérios de aceite

1. Testes locais com cliente falso: resposta com duas frases e fontes distintas; ID inventado apenas na segunda; frase vazia; lista vazia; ID duplicado; `sem_evidencia` sem afirmações e com afirmação indevida; `limitacao` preenchida em `respondida` (aceita, não exibida); JSON truncado com e sem motivo disponível; falha do serviço; saída malformada. Teste estrutural declara que não prova suporte semântico.
2. Prévia não instancia cliente nem lê credencial. Hash antigo bloqueia novo envio. Teto 20/dia UTC e até duas tentativas por pergunta apenas para serviço transitório permanecem; registros preservam chamada, pares frase–IDs, `limitacao` e motivo de término quando disponível, sem sobrescrever capturas antigas.
3. Suíte existente continua passando após atualização deliberada dos testes de contrato; saídas históricas da tag são preservadas. Diff revisado antes de commit/merge.
4. **Previsões de Luiz registradas em 18/10/2026, antes de qualquer chamada da configuração nova:** 17/20 casos terão todas as afirmações sustentadas; `N=3` falhas de contrato. O lote E01–E20 é julgado caso a caso: em `respondida`, Luiz marca cada frase como sustentada/não sustentada pelos IDs específicos; recusa, falha de serviço e controle local seguem categorias distintas. Um caso com qualquer frase sem suporte não passa. **Regra fixada por Luiz em 19/10/2026, antes de qualquer resultado da configuração nova:** recusa (`sem_evidencia`) em caso com `respondida` esperada não passa, por perda de cobertura, como E17 e a spec 0006; é registrada separadamente de afirmação sem suporte. A avaliação curada isola geração; não mede retrieval ponta a ponta.
5. Gate novo só é aprovado quando **20/20 casos têm resultado resolvido e julgamento explícito de Luiz**, sem frase sem suporte, preservando erros e tentativas. Falha de serviço é pendência, não reprovação semântica; só uma reavaliação autorizada pode resolvê-la. A régua por frase é mais estrita que a do baseline: não comparar diretamente os gates como “melhor” ou “pior”. Relatório separa contexto real, sintético e controle local; toda proporção traz numerador, `n`, intervalo e ressalva de seleção intencional. Formato, ID válido ou status do provedor não aprovam caso.
6. Até **25/10/2026**, ou o gate novo foi aprovado e ADR/README/roteiro registram o resultado, ou a ADR registra abandono e a entrega usa a tag baseline. **Qualquer falha de serviço ainda pendente nessa data deixa o gate não aprovado e aciona abandono pelo prazo; nada aprova por omissão.** Nenhuma alegação de “mais certa” em qualquer caminho.

## Cronograma e medição opcional

| Data | Etapa | Saída |
|---|---|---|
| 20/10 UTC | Primeira passada da fase 1: reavaliar dez falhas locais de 19/10 e executar E14/E15/E18; respeitar cota | Treze casos pareáveis julgáveis ou pendências explícitas; `N` e IC se definidos |
| 21/10 UTC | Fase 2, somente se `N < 3` nos pareáveis; respeitar cota | Sete casos restantes executados ou pendências explícitas |
| 22–23/10 | Julgamento frase a frase por Luiz | Resultado com `n` e IC quando houver proporção |
| 24–25/10 | Aprovação do gate ou abandono | ADR e configuração da entrega definidos |

Atraso consome a folga seguinte; não estender além de 25/10. Opcionalmente, Luiz cronometra o julgamento por caso novo e de uma amostra de capturas da tag. Relatar mediana por caso e `n`, além da diferença de tarefas e possível efeito de aprendizagem. Sem essa medição, a hipótese de auditoria mais barata permanece não comprovada. Antes de cronometrar, registrar a previsão de Luiz para o tempo, conforme a regra da base.

## Checkpoint de implementação local — 18/10/2026

- `provedor_gemini.py` envia schema/instrução novos e registra `finish_reason` quando disponível; JSON inválido só recebe rótulo de truncamento quando `MAX_TOKENS` foi observado.
- `responder.py` valida cada par e monta o texto apenas das frases; um par inválido derruba a resposta inteira. `demo.py` exibe fontes por frase e preserva a prévia com hash e o teto local.
- `avaliar_geracao.py` separa falhas operacionais, exige as duas previsões antes de criar cliente real, compartilha o teto diário local, aceita subconjuntos por `--ids` e conclui os 13 pareáveis antes de decidir a parada em três falhas; nos sete restantes, para em cinco falhas totais. O registro local acumula falhas entre arquivos/dias sob o mesmo hash e bloqueia reenvio acidental do mesmo caso. `reavaliar_e05.py` permanece histórico e rejeita o hash antigo sob o contrato novo; o avaliador com `--ids E05` atende reavaliação focal nova.
- Testes com cliente falso, sem rede: suíte completa com **262 testes aprovados** em 18/10 usando `google-genai 1.75.0` isolado (`python -m pytest -q -W error::FutureWarning --basetemp=.venv/pytest-tmp/full-sdk175`). Isso não prova suporte semântico, disponibilidade do Gemini nem aceitação do schema pela API.
- Na prévia de 18/10, antes das tentativas registradas em 19/10 UTC, não havia chamada nova ao Gemini. Previsões de Luiz registradas. Prévia gerada localmente em `google-genai 1.75.0`: hash do lote completo `203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`, com repetição transitória. Contexto exato dos 13 pareáveis foi separado em `.venv/previa_citacao_afirmacao_fase1_20261018.md` para revisão de PII; detector heurístico não sinalizou padrões. Luiz revisou e liberou o hash antes da tentativa de 19/10 UTC. Julgamento e gate permanecem pendentes.
- O hash provisório `ab83254779e21080b15c7b0bf339567e5c848698738e8d5a6ef814a5a9c59451` veio do SDK 1.73.1 e **não libera envio**. A execução real precisa manter o SDK 1.75.0 isolado; outra versão muda o hash.

## Reavaliação autorizada após bloqueio local de rede

Em 18/10 local (19/10 UTC), a primeira tentativa da fase 1 consumiu o teto local com dez casos sem saída por `ConnectError`. A captura original `reports/geracao_citacao_afirmacao_fase1_20261019.jsonl` permanece intacta; diagnóstico em `reports/geracao_citacao_afirmacao_fase1_20261019.md`. Luiz autorizou explicitamente **uma** reavaliação de E02, E03, E04, E06, E07, E08, E09, E10, E11 e E12 e a primeira execução de E14, E15, E18, sob o mesmo hash `203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`, mesmo contexto, SDK 1.75.0, política de duas tentativas transitórias e teto 20/dia UTC. Nenhum dos sete casos da fase 2 foi liberado para a janela de 20/10. **Execução exclusivamente manual por Luiz neste PC**, dentro de 20/10 UTC (até antes das 21:00 locais de 20/10); agendamentos cancelados, pois o PC fica desligado e o sandbox padrão bloqueou DNS. Este PC mantém o único ledger de cota.

Antes de qualquer chamada contada, no **mesmo perfil de rede e ambiente do envio**, resolver DNS e abrir TLS com `generativelanguage.googleapis.com:443`, sem chave e sem requisição à API; mostrar o resultado. Se falhar, não criar envio nem iniciar. O teste DNS/TLS no perfil elevado passou em 19/10 UTC (`DNS_OK 16 endereços`, `TLS_OK TLSv1.3`), mas deve ser repetido imediatamente antes do envio de 20/10.

O avaliador exige opção explícita `--reavaliar-falhas-locais` para os dez IDs autorizados, hash exato, uma única falha anterior no ledger e `ConnectError` sem saída na captura de origem. Grava nova captura sem sobrescrever a anterior, limita a **um** reenvio por ID e continua usando o ledger de cota. Casos sem saída continuam pendentes e não completam a fase pareável; somente o resultado mais recente por ID entra em `N` e no controle de conclusão. E14/E15/E18 seguem `--ids` normal, sem opção de reavaliação.

**Checkpoint autorizado antes de desligar o PC:** Luiz pediu commit e push do código, testes, spec 0008, ADR 0008, `docs/aprendizado/MISSAO.md` e captura/diagnóstico da fase 1 de 19/10 UTC, ainda parcial. O commit deve ser identificado como checkpoint, sem declarar a fase concluída nem o gate aprovado. Antes de commitar, conferir que o hash do lote depende apenas do manifesto e configuração (incluindo schema, instrução e SDK), sem SHA de commit; recalcular a prévia após o commit e só fazer push se permanecer `203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`. Se mudar, parar e avisar antes do push. Após a fase 1 completa, registrar `N`, casos julgáveis, exclusões e IC95% na ADR/relatórios e fazer novo commit/push dos resultados. Não enviar API pela outra máquina: o ledger local de 20/dia UTC não é compartilhado pelo Git.

## Reenvio autorizado de E02 e E18 por falha do provedor — 20/10/2026

Fase 1 de 20/10 UTC (`reports/geracao_citacao_afirmacao_fase1_20261020.md`): 11/13 pareáveis julgáveis, `N_pareado = 0`. E02 (504/503, reenvio de 19/10 esgotado) e E18 (`ReadTimeout`/503, primeira execução) ficaram sem saída, com DNS e TLS ok: indisponibilidade do provedor, não rede local. Com dois pendentes, `N_pareado ≤ 2` em qualquer desfecho; o limiar de abandono da fase 1 não pode mais ser atingido.

**Decisão de Luiz (2026-10-20T14:28Z, antes de qualquer resultado desses reenvios):** autoriza **um** reenvio adicional de E02 e de E18, sob o mesmo hash, contexto, SDK 1.75.0, política de duas tentativas e teto 20/dia UTC, antes dos sete da fase 2. **Ajuste de Luiz às 14:30Z, ainda antes de resultados:** o reenvio pode ocorrer já em 20/10 UTC, com a cota restante do dia (16/20 usadas; o avaliador reserva 2 por caso, então E02 e E18 cabem, no máximo 20/20); a fase 2 só a partir de 21/10 UTC (00:00Z = 21:00 locais de 20/10). A trava de `avaliar_geracao.py` que exige os 13 pareáveis concluídos antes da fase 2 permanece. Se E02 ou E18 continuar sem saída, segue pendente: nenhum terceiro reenvio está autorizado e falha pendente em 25/10 mantém o gate não aprovado. O mecanismo exige opção própria, IDs fixos, captura de origem conferida por SHA-256 e contagem exata de envios anteriores no ledger (E02 = 2, E18 = 1); a opção de 19/10 (`--reavaliar-falhas-locais`) não é reaproveitada.

## Riscos e pontos a revisar na aprovação

- **Acoplamento existente:** `review_ids` global aparece no CLI, avaliador, reavaliador E05 e testes. A nova estrutura exige revisão explícita desses consumidores; capturas antigas não devem ser reprocessadas como novas.
- **Recusa:** texto livre do modelo em `sem_evidencia` pode conter fato inventado; a mensagem local fixa preserva a regra atual.
- **Múltiplas alegações:** mitigadas por instrução de uma alegação por item, sem garantia; julgamento por frase cobre o restante.
- **Truncamento:** `finish_reason` só classifica truncamento se disponível e compatível; mudança de limite exige novo hash.
- **Custo:** lote real demanda dias de cota e tempo de julgamento; disponibilidade externa não é qualidade semântica. Não iniciar chamadas sem previsão e liberação do contexto.
