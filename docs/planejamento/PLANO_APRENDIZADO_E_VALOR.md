# Plano de aprendizado, validação de valor e entrega — TC4

**Data:** 2026-10-07 · **Dono:** Luiz Maibashi.
**Estado:** plano inicial; problema empresarial e expansão de escopo ainda não decididos.
**Entrega acadêmica registrada:** 2026-11-01, repositório público e vídeo de até7min.

## Missão e resultado esperado

Luiz quer compreender, explicar e defender o sistema que construiu; usar o Tech
Challenge para demonstrar capacidade de resolver uma dor empresarial relevante,
com evidências e reprodução. Prioridade: consolidação do entendimento. A
investigação de valor precede novas funcionalidades; a entrega acadêmica permanece
protegida. O projeto contribui para empregabilidade e aprendizado, enquanto a
possibilidade comercial precisa de validação própria.

“Melhor projeto de IA/dados hoje” não é um critério verificável. O alvo operacional
é: para um usuário e uma tarefa definidos, resolver melhor que uma alternativa
acessível, mostrar evidências do ganho, explicar limites e permitir reprodução.
Não assumir que quantidade de tecnologias ou aparência sofisticada implica valor.

## Diagnóstico inicial — o que sabemos e o que falta

### Evidência existente

- Corpus Olist histórico preparado, decisões documentadas e busca MiniLM/DuckDB.
- Comparação de recuperação com julgamento humano; geração/citações/recusa testadas.
- CLI local de busca/fontes/contagem e ensaio sintético;243 testes do checkpoint
  anterior, não nova bateria nesta etapa.
- Consulta real sobre atrasos com dez fontes e recusa P15 aprovadas por Luiz.
- Gate liberado exclusivamente para demonstração curada:19 aprovações históricas
  da rodada04 mais E05 aprovado em reavaliação isolada, sob mesmo contrato.
- Falhas anteriores preservadas; não são20acertos de uma única rodada.

### Evidência ainda ausente

- Usuário empresarial observado usando a solução e decisão concreta que ela melhora.
- Comparação com processo manual, SQL/BI ou ferramenta já utilizada pelo usuário.
- Economia de tempo, erro evitado, impacto operacional ou retorno financeiro medidos.
- Uso ponta a ponta pela entrada destinada ao usuário: CLI atual não integra geração.
- Reprodução por outra pessoa em ambiente limpo e operação com dados atuais de empresa.
- Retenção dos conceitos por Luiz; aprovação de respostas não prova domínio.

**Veredito inicial:** protótipo técnico com evidência de exemplos curados; valor
empresarial plausível, ainda não validado. Não é solução de produção comprovada.

## Sequência e critérios de passagem

### Etapa1 — consolidar entendimento (prioridade)

Formato por aula: explicar uma ideia com exemplo do TC4 → mostrar falha/limite →
Luiz responde uma pergunta de negócio → feedback → aplicação a um exemplo novo.
Uma pergunta por vez; aula antes da prova; sem exigir decorar biblioteca ou código.
Dica solicitada não vira erro. Resposta auxiliada não comprova retenção.

| Ordem | Conceito | Capacidade que Luiz demonstrará |
|---|---|---|
| 1 | Corpus, população, top-k e frequência | Explicar por que exemplos recuperados não estimam prevalência |
| 2 | Embeddings, similaridade/cosseno e polaridade | Reconhecer texto parecido que não responde ou contradiz a pergunta |
| 3 | Relevância, pooling e gabarito humano | Explicar como comparamos buscas e o limite do pool |
| 4 | Precisão@k, revocação e MRR | Escolher uma métrica conforme a falha que importa ao gestor |
| 5 | RAG, contexto, citação e suporte | Separar ID válido de afirmação sustentada |
| 6 | Recusa, alucinação e injeção em comentários | Diagnosticar quando responder, recusar ou tratar erro |
| 7 | Testes, mock, API real e retry | Explicar o que cada evidência prova e delimitar chamadas/custo |
| 8 | Autosseleção, denominador e intervalos | Interpretar a contagem sem generalizar aos clientes/operação atual |
| 9 | Decisões arquiteturais | Defender MiniLM, DuckDB, limpeza mínima e ausência de chunking |
| 10 | Produto, baseline, ROI e transferência | Explicar qual decisão mudaria e como testar ganho |

Fontes: código/specs/ADRs do projeto e documentação primária para conteúdos
adicionais. Recursos externos para ensino devem ser lidos antes de cada aula.
McNemar é aprofundamento posterior se a comparação de erros pareados justificar;
não acrescentar prova estatística sem necessidade.

Material de aula: workspace de ensino dentro de docs/aprendizado/, com MISSAO.md,
RECURSOS.md, lições HTML curtas e estado de respostas, criado em escopo próprio
antes da primeira lição. Este plano não cria dezenas de arquivos vazios.

Critério de aprendizagem: explicar com próprias palavras, diagnosticar um caso
novo e justificar um trade-off. Revisitar em sessões posteriores; domínio formal
da base exige2acertos+7dias, sem promover por autoavaliação. Entrega e aprendizado
têm registros separados; não declarar retenção pelo aceite do artefato.

### Etapa2 — verificar requisito acadêmico e limites da base

Produzir matriz: requisito do enunciado → implementação → evidência → lacuna.
Obrigatórios: base preparada e justificada; pipeline RAG; respostas com suporte;
perguntas sem evidência; repositório reproduzível; vídeo. Metadados são adicionais.

Resultado: mínima entrega defensável e lacunas obrigatórias, especialmente execução
ponta a ponta. Captura aprovada é evidência, não substituto de solução executável.
Dados2016–2018 demonstram método, não desempenho atual da Olist ou de uma empresa.

### Etapa3 — investigar dor empresarial e alternativas atuais

Pesquisa inicial, não validação final:

- DHL2026 pesquisa consumidores e negócios e destaca entrega/devolução como parte
  da experiência e do desafio de custos. É evidência de contexto do setor, não de
  demanda pela nossa ferramenta, nem prova específica de empresa brasileira.
- Zendesk documenta filtros, comentários, motivos, métricas e classificação de
  feedback. Logo, “IA resume reclamações” não demonstra novidade comercial.

Pesquisar e comparar também o processo manual, planilha/SQL/BI e soluções que o
usuário potencial realmente conhece. Não assumir ausência de concorrência pela
falta de informação. Separar capacidade anunciada por fornecedor de eficácia
observada por usuários; não concluir que limitação de um recurso vale para toda
a plataforma ou concorrência.

Resolver uma incógnita por vez:

| Investigação | Saída necessária |
|---|---|
| Usuário e rotina | Cargo, tarefa recorrente, frequência e decisão específica |
| Dor e consequência | Episódio recente, trabalho atual, atraso/erro/custo causado |
| Alternativas | Como resolve hoje; por que isso basta ou falha |
| Dados | Campos necessários, acesso, atualidade e permissão de uso |
| Teste de valor | Tarefa observável e baseline comparável |

Conversas: buscar inicialmente2–3 profissionais pertinentes, com roteiro preparado;
Luiz realiza ou autoriza explicitamente qualquer contato. Amostra exploratória,
não representativa. Ouvir episódios reais e observar processo/documento quando
possível; “eu usaria” e elogio de demo são sinais fracos. Sem acesso a usuário,
registrar validação empresarial pendente e usar avaliação por cenário, claramente
identificada, para a entrega acadêmica.

### Etapa4 — escolher uma tese de valor pequena e falsificável

Workshop com Luiz após as aulas e a investigação: quem sofre, qual decisão toma,
qual alternativa usa, qual número queremos melhorar, e o que faria abandonar a
ideia. Não pressupor produto nem comprador. A tese deve poder ser rejeitada.

Hipótese candidata, ainda não decidida: ajudar um gestor a montar uma investigação
de problemas de entrega com exemplos auditáveis e contagens definidas. Testar se
esse trabalho existe e merece prioridade antes de desenhar funcionalidades.

Saída desejada: uma tarefa de ponta a ponta e um relatório útil à decisão,
com fatos, evidências, limites e próximos itens a verificar; sem causa ou solução
operacional inventada. RAG localiza/explica exemplos; SQL calcula agregados;
classificação só entra se houver necessidade de frequência temática e avaliação
própria. P09 continua congelado.

Saídas alternativas legítimas: manter escopo atual; estreitar tarefa; descartar
hipótese. Projeto forte pode demonstrar uma decisão correta de não adicionar IA.

### Etapa5 — desenhar e implementar somente o incremento justificado

Antes de código: escopo de arquivos confirmado, spec com aceite, decisões e
trade-offs. Preservar corpus/caches/pool/gabarito/votos/P09 e padrão3.1/25s.
Contextos novos e medições exigem autorização/previsão conforme contrato.

Prioridade técnica provável: execução reproduzível do fluxo necessário ao usuário,
e não interface sofisticada ou agentes autônomos. A decisão final depende da tarefa.

Checklist de transferência para uma empresa: contrato de entrada/versionamento,
tratamento de dados pessoais, rastreabilidade, credenciais fora do repo, erros
visíveis, atualização de dados, custo/latência, monitoramento e responsabilidade
humana. Implementar o mínimo exigido pelo piloto; documentar o que fica fora.
Revisar alertaTorch e guarda de data prevista antes de exposição em escopo próprio.

### Etapa6 — medir qualidade e valor contra alternativa

Protocolar tarefas comparáveis: mesmo conjunto de dados, perguntas e critérios,
processo atual/baseline e solução. Registrar tempo, correção, suporte das afirmações,
reprodução, latência e custo quando pertinentes. Evitar confundir ganho no ensaio
com efeito causal empresarial; controlar ordem/aprendizado quando viável.

Luiz prevê resultados e define sucesso/falha antes da medição. Primeiro anotar
diagnósticos da qualidade; depois quantificar. Não fixar meta arbitrária de ganho
sem baseline e relevância para usuário. Proporções com n e intervalo; amostra
pequena/intencional e avaliador único declarados. Casos novos revisados separados
dos exemplos ensaiados. Não reutilizar aprovações como evidência independente.

ROI inicial: horas efetivamente poupadas × custo/hora documentado menos operação
e implantação. Não converter minutos em receita ou prometer redução de atraso,
churn ou reembolso sem medir esse efeito. Validação de disposição a pagar é outra
pergunta; não se deduz de ganho técnico.

Critério para avançar: ganho útil ou aprendizado verificável, qualidade suficiente
para a tarefa e reprodução. Se não houver ganho, reduzir/reformular e registrar.

### Etapa7 — documentação, reprodução, vídeo e publicação

Atualizar README/retomada conforme estado atual; instalação, execução, arquitetura,
decisões, exemplos, limites e evidências. Reproduzir em ambiente limpo com outra
pessoa quando possível. Separar requisitos satisfeitos de próximos passos.

Vídeo<=7min: dor e usuário → solução e decisões → tarefa completa → fontes e
contagem → recusa → evidência de qualidade/valor e limites. Luiz deve conseguir
explicar escolhas, não apenas narrar cliques.

Publicação/revisão de dados e credenciais, commit/push e entrega em etapa explícita.
Novo dado empresarial/piloto não é pré-requisito automático para o Tech Challenge.

## Controle de escopo e prazo

- Nenhuma expansão começa antes de entendimento, requisito e hipótese definidos.
- Antes de cada etapa, escolher uma pergunta, um artefato e critério de saída.
- Reservar a última semana antes de01/11 para reprodução/documentação/vídeo e
  entrega; antecipar congelamento se o calendário do Luiz exigir.
- Investigação sem sinal suficiente até o congelamento vira limitação/futuro,
  não atraso da entrega nem alegação de validação concluída.
- Contexto: relatório/checkpoint curto e esta frente do Bridge; sessões separadas
  para ensino, descoberta e implementação. Não carregar todo histórico a cada aula.
- Delegação somente para trabalho delimitado e auditável; julgamento/ensino do Luiz
  não delegado. Disponibilidade do modelo solicitado deve ser conferida antes.

## Fontes e recursos iniciais

- Enunciado local: ../../[IAST] - Tech Challenge - Fase 4.pdf,páginas6–10.
- Contrato da demo: ../spec/0004-demo-investigacao-entrega.md.
- Avaliação/gate: ../spec/0006-avaliacao-geracao.md e ../../reports/geracao_20261006_evidencias.json.
- Estado/evidência: ../../reports/conferencia_corpus_real_20261007.md,CHECKPOINT ATUAL.
- Decisões de corpus/busca: ../adr/0001-corpus-limpeza-minima-sem-chunking.md e ../adr/0002-embedding-minilm-busca-exata-duckdb.md.
- [DHL eCommerce Trends2026,fonte primária de pesquisa setorial](https://group.dhl.com/en/media-relations/press-releases/2026/dhl-ecommerce-trends-report-2026-old-rules-do-not-apply-in-the-age-of-ai.html).
- [Zendesk Surveys dashboard,documentação de funcionalidades existentes](https://support.zendesk.com/hc/en-us/articles/7043759414042-Accessing-and-viewing-the-Surveys-dashboard).

## Próximo passo imediato

Preparar a primeira aula: corpus/população/top-k/frequência, com exemplo do TC4,
uma pergunta por vez e registro separado de compreensão imediata e retenção.
Não iniciar expansão do código ou nova consulta à API.

## Refinamento confirmado — menor custo, observabilidade/evals e ciclo completo

Luiz confirmou o escopo do ensino e acrescentou: a entrega de menor custo total
que resolve a tarefa com qualidade fica; complexidade adicional só é testada pelo
retorno incremental. “Evolves” interpretado como evals, sujeito à correção.

Observabilidade: rastrear pergunta/contexto/configuração, etapas, duração, tokens
quando disponíveis, erro/tentativa e saída para localizar falha sem expor PII ou
credenciais. Logs atuais são evidência parcial; custo não é inferido sem uso/tarifa.
Evals: verificar relevância, suporte, citação, recusa e regressão em casos definidos,
com revisão humana e separação de serviço/conteúdo. Não adotar juiz LLM sem comparar
com julgamento humano. Nenhuma ferramenta/plataforma foi escolhida.

Ciclo coberto: problema → aquisição/permissões → qualidade/preparação → baseline →
recuperação/geração → avaliação → reprodução/entrega → operação/monitoramento →
melhoria ou retirada. Para cada etapa, declarar o que foi implementado, verificado,
apenas desenhado ou ficou fora; não apresentar protótipo como produção empresarial.

Toda extensão responde: qual falha/decisão justifica; qual alternativa barata;
qual métrica/prévia; custo de implantação/operação/manutenção; critério de reversão.
A comparação com SQL/BI não remove o RAG exigido pelo enunciado: delimita seu uso.
Sem novas dependências, API ou código do sistema nesta atualização.
