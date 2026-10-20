# Missão — compreender e defender o TC4

Luiz quer dominar o que foi construído, explicar decisões e desenvolver uma solução reproduzível para uma dor empresarial, respeitando o enunciado e a entrega de01/11/2026.

## Critérios confirmados em07/10/2026

- A solução de menor custo total que atende aos requisitos de qualidade e segurança fica. Custo inclui implantação, operação, revisão humana e manutenção.
- Maior complexidade só entra como hipótese testável de ganho; exige baseline, previsão, custo incremental e critério de abandono definidos antes do experimento.
- SQL/BI podem vencer em tarefas de contagem; busca simples pode bastar; RAG se justifica quando a tarefa exige recuperar e explicar texto com evidências. Não retirar RAG obrigatório do Tech Challenge: usar cada técnica na tarefa adequada.
- Observabilidade e evals integram o ciclo do projeto quando ajudam a diagnosticar ou controlar uma falha real. “Evolves” interpretado provisoriamente como evals, sujeito à correção do Luiz.
- Cobrir o ciclo: problema → dados/permissões → preparação/qualidade → baseline → modelagem/recuperação/geração → avaliação → reprodução/entrega → operação/monitoramento → melhoria ou retirada. Cobertura não significa implementar infraestrutura de produção inteira antes da entrega.
- Tecnologias não entram por popularidade. Aplicabilidade empresarial continua hipótese até validar usuário/tarefa e medir ganho.

## Ensino

Explicação simples antes de pergunta; uma por vez; feedback e aplicação nova. Sem confundir aceite de artefato com domínio. Revisitaremos depois; domínio formal exige2acertos+7dias conforme regra da base.

## Estado do aprendizado

- Lição0001: primeira resposta recebida. Luiz identificou a generalização indevida dos dez resultados; confundiu corpus com amostra e recuperação com medição/calibração da população. Feedback corretivo: corpus é coleção preparada, top-k é seleção por relevância/filtros, frequência exige população/denominador. Compreensão parcial; aplicação nova pendente, retenção não avaliada.
- Próximas aulas: embeddings/polaridade; avaliação de busca; suporte/citação; recusa; testes/API/retry; estatística; arquitetura; observabilidade/evals; valor e ciclo de dados.
- Plano de referência: ../planejamento/PLANO_APRENDIZADO_E_VALOR.md.

### Lição0001 — aplicação ao denominador (07/10/2026)

Luiz excluiu corretamente pedidos ainda não entregues porque a população da pergunta contém somente pedidos entregues com avaliação escrita. Acerto imediato após explicação; não promove domínio nem intervalo de revisão. Próxima verificação: distinguir numerador (atrasados) de denominador (todos os entregues elegíveis, atrasados+no prazo). Lacunas iniciais sobre corpus/amostra e busca/calibração ainda precisam de nova aplicação.

### Lição0001 — top-k e viés de seleção (07/10/2026)

Após feedback, Luiz distinguiu numerador/denominador e reconheceu que ampliar resultados selecionados por atraso não resolve o viés; apontou falta do total elegível. Antes, confundiu diversidade de reclamações com representatividade. Ajuste ainda necessário: resultados podem conter tipos diferentes; frequência exige contar todos os atrasados e todos os entregues elegíveis, não usar100 recuperados como numerador completo. Compreensão imediata em evolução, com auxílio; retenção não avaliada.

## Checkpoint de pausa — 09/10/2026

**Aula pausada a pedido de Luiz.** Última pergunta apresentada, sem resposta:
“Como você apresentaria, na mesma análise, o número de pedidos com prazo longo e os comentários sobre demora sem afirmar que um causou o outro?” Retomar exatamente por ela, uma pergunta por vez; não antecipar resposta ou avançar de tema.

**Limite de tempo decidido depois da pausa:** concluir o bloco intensivo até
12/10, com no máximo duas sessões de 45 minutos. Após isso, revisões de até
10 minutos incorporadas às tarefas do projeto. Esta pergunta serve para fechar
a distinção descrição × hipótese causal; não iniciar um questionário sem fim.
A prioridade passa para matriz do enunciado, demo reproduzível, avaliação,
README e vídeo. Prazo interno 31/10, 01/11 de reserva; entrega antes de 02/11.
Retenção futura não é gate da entrega acadêmica.

Evidência de compreensão imediata, com feedback ao longo da conversa:
- Separou busca de comentários e contagem por datas; definiu numerador/denominador após correção.
- Distinguiu elogio ao produto de elogio à entrega; preservou crítica e elogio num mesmo relato.
- Reconheceu que citação válida não torna afirmação sem suporte verdadeira; não inferiu causa de item faltante.
- Separou `sem_evidencia` de `erro_geracao`, preservou a primeira falha quando retry recupera e rejeitou resposta que inventa prazo.
- Escolheu contagem estruturada para atraso; separou percepção “demorou muito” da classificação por datas.
- Identificou investigar tamanho do prazo prometido quando clientes reclamam de demora apesar de entrega pontual; sugeriu comparar dados dos que reclamaram e contar prazos prometidos/cumpridos. Identificou que RAG agrega contexto dos relatos, sem inferir falha de rastreamento não mencionada.

**Limites:** respostas dadas após ensino e correção na mesma sequência não provam retenção independente. Lição0001 foi aplicada a vários exemplos; aula sobre causalidade/valor ainda aberta. Não marcar domínio nem `spaced_review.py --mark` por este checkpoint. Retomar depois com exemplo novo e rever em outro dia.

**Projeto/execução:** plano em `../planejamento/PLANO_APRENDIZADO_E_VALOR.md`. Gate somente da demo curada liberado; CLI ainda não integra geração livre. Sem nova API, mudança de modelo, corpus, cache, pool, gabarito, votos ou P09 durante o ensino. Próximo bloco após a pergunta: fechar distinção descrição × hipótese causal, depois avançar para embeddings/cosseno e evals conforme plano.

### Lição 0002 — logit, softmax e temperatura (18/10/2026)

Origem: workshop Anwar Hermuche (17/10), ancorada em `temperature=0` de `src/rag/provedor_gemini.py:50`. Luiz leu a lição antes das perguntas de recuperação e não fez a previsão numérica do Galo (o valor calculado, 98%, ficou visível na conversa).
- Corrigido: "T é a criatividade" (é consequência da distribuição, L535); "T=1 = criatividade alta" (T=1 é a distribuição nativa); "perto de 0 sobra um segundo semelhante" (o segundo também vai a ~0, salvo empate).
- Corrigido: confundiu **reprodutibilidade** (hash + registro, spec 0007) com **qualidade** (acerto no gate E01–E20); "85%" sem `n` e intervalo.
- Parcial: identificou a oscilação do servidor; faltou o sinal (as duas maiores notas quase empatadas) e a causa medida (tamanho do lote, não latência).
- Acertou a escolha T 1→0,5 = "muito mais que o dobro"; o porquê saiu parcial ("exponencial" certo, "opção mais próxima" errado). Explicado: a diferença dobra no expoente, então a vantagem é elevada ao quadrado (55× → 2.981×).
- Estado: compreensão imediata em evolução, com ajuda. Retenção não testada. **Próxima verificação, sem aviso:** "a banca pergunta se é reproduzível: resposta em duas frases".
- Pós-entrega (não mexer antes de 31/10): a doc do Gemini recomenda o padrão de temperatura nos "Gemini 3 anteriores"; não confirma se isso vale para o 3.1-flash-lite.

### Retenção da lição 0002 — sem aviso (18/10/2026)

"A banca pergunta se é reproduzível: duas frases." Luiz, sem ajuda: não promete texto idêntico; T=0 reduz a variação, mas o servidor ainda pode mudá-la; garante auditabilidade (hash + registro) e a qualidade é medida à parte no gate. **Acerto**: separou reprodutibilidade, auditabilidade e qualidade, que tinha confundido na aula. Não nomeou a causa (tamanho do lote), aceitável em duas frases. Mesmo dia da aula: recuperação imediata, não retenção de longo prazo. Sem `--mark`.

### Lição 0003 — saída estruturada: formato × verdade (18/10/2026)

Âncoras: `SCHEMA_RESPOSTA` (`src/rag/provedor_gemini.py:9-17`) e `src/rag/responder.py:50`; workshop L1814/L1815/L1826; doc Gemini Structured output.
- Previu certo que `responder()` devolve `respondida` para citação que não sustenta a frase. Porquê saiu vago ("as avaliações se encaixam no formato"); corrigido: o que passa é a *resposta*, por duas barreiras (schema e id no contexto), e nenhuma checa suporte.
- Na opção "por afirmação", acertou que continua sem garantir que a citação sustenta a frase; **não viu o ganho** (rastreabilidade, auditoria par a par). Explicado com exemplo r1/r2/r3.
- Pediu explicação do que muda entre as opções (dica sob demanda, não conta como erro).
- **Decisão (zona de julgamento):** mudar para citação por afirmação porque quer mostrar auditar/localizar erro/agir no ponto exato. Desafiado: compra auditabilidade, não correção; vira experimento com baseline (tag `cfg-citacao-por-resposta`), custo (engenharia + ~20+ chamadas + rejulgamento dele) e abandono: **se até 25/10 o gate E01–E20 novo não estiver julgado e aprovado, a entrega volta para a tag**. Luiz aceitou. Revoga conscientemente "nada muda código antes de 31/10". Execução no Codex: `../planejamento/BRIEF_CODEX_citacao_por_afirmacao.md`.
- Estado: compreensão imediata com ajuda; retenção não testada. **Próxima verificação, sem aviso:** "uma resposta citou só ids do contexto: o que isso prova e o que não prova?".
- Próxima aula do plano: classificador como gate e custo fixo × variável (sintese_parte1 §"aula antes da prova", item 3).

### Previsões para a rodada da spec 0008 (18/10/2026, antes de qualquer chamada)

- Baseline (registrado pelo Codex na spec 0008): Luiz previu ~4 falhas de contrato; observado **0/13** julgáveis na rodada 04 (IC95% Wilson 0%–22,8%). Superestimou falha de formato: o schema cumpre o que garante.
- Configuração nova: **17/20** casos com todas as afirmações sustentadas; **N = 3** falhas de contrato.
- A previsão `N = 3` cobre os 20 casos; não prevê em quais IDs as falhas ocorrerão. Se as três aparecerem nos 13 pareáveis, a primeira fase aciona abandono; caso contrário, aplica-se a parada total em cinco na segunda fase. A previsão não substitui o resultado nem o julgamento do gate.

### Fase 1 julgada × previsões (20/10/2026)

- Julgamento de Luiz, frase a frase (`reports/ficha_julgamento_fase1_20261020.jsonl`, `012d0f1`): **13/13** casos aprovados (IC95% Wilson 77,2%–100%); 12/12 frases S; 2/2 recusas adequadas (E14, E15); `N = 0/13` falhas de contrato.
- Previsões: 9/9 S nos casos originais, acertou. Reenvio de E02 "volta com saída julgável", acertou (16:25Z, antes de rodar). E18 sem previsão. `N = 3` previsto para os 20 casos; 0 nos 13 pareáveis. Pergunta da sabatina pós-gate: por que esperava 3?
- Em E18/1 hesitou porque a frase omite a demora. Explicado: suporte se julga **por frase**, completude **por caso**; separar elogio e crítica em duas afirmações é o que a spec pede. Manteve S.

### Lição 0002 — retenção (20/10/2026)

Pergunta sem aviso: "a banca pergunta se é reproduzível: duas frases". **Falhou.** Respondeu formato × verdade e auditoria frase a frase (auditabilidade, lição 0003), não reprodutibilidade. É a mesma confusão de 18/10 (lá com qualidade). Pista parcial no resumo anterior da conversa. Ensinado o trio reproduzível (hash + registro, spec 0007:39-50; `temperature=0` ≠ texto idêntico, ADR 0008:23) × qualidade (gate) × auditável (citação por afirmação). **Próxima verificação ≥ 22/10, com formulação nova.**

### Lição 0004 — classificador como gate, custo fixo × variável (20/10/2026)

Lição em `licoes/0004-classificador-gate-custo-fixo-variavel.html`. Previsão do equilíbrio (`F < v·N·b`) respondida certa, mas com texto idêntico ao feedback do botão: não conta como evidência. **Pendente, retomar por ela:** aplicação nova com `v` = R$ 0,05 (gate se paga? quanto? novo `N*`? por que modelo mais caro torna o gate mais atraente?). Gabarito: economia R$ 2.000 − R$ 1.500 = +R$ 500/mês; `N*` = 75 mil. Retenção não testada.
