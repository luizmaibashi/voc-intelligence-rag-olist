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

Evidência de compreensão imediata, com feedback ao longo da conversa:
- Separou busca de comentários e contagem por datas; definiu numerador/denominador após correção.
- Distinguiu elogio ao produto de elogio à entrega; preservou crítica e elogio num mesmo relato.
- Reconheceu que citação válida não torna afirmação sem suporte verdadeira; não inferiu causa de item faltante.
- Separou `sem_evidencia` de `erro_geracao`, preservou a primeira falha quando retry recupera e rejeitou resposta que inventa prazo.
- Escolheu contagem estruturada para atraso; separou percepção “demorou muito” da classificação por datas.
- Identificou investigar tamanho do prazo prometido quando clientes reclamam de demora apesar de entrega pontual; sugeriu comparar dados dos que reclamaram e contar prazos prometidos/cumpridos. Identificou que RAG agrega contexto dos relatos, sem inferir falha de rastreamento não mencionada.

**Limites:** respostas dadas após ensino e correção na mesma sequência não provam retenção independente. Lição0001 foi aplicada a vários exemplos; aula sobre causalidade/valor ainda aberta. Não marcar domínio nem `spaced_review.py --mark` por este checkpoint. Retomar depois com exemplo novo e rever em outro dia.

**Projeto/execução:** plano em `../planejamento/PLANO_APRENDIZADO_E_VALOR.md`. Gate somente da demo curada liberado; CLI ainda não integra geração livre. Sem nova API, mudança de modelo, corpus, cache, pool, gabarito, votos ou P09 durante o ensino. Próximo bloco após a pergunta: fechar distinção descrição × hipótese causal, depois avançar para embeddings/cosseno e evals conforme plano.
