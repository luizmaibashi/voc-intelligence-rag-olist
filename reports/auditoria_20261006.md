# Auditoria do Tech Challenge Fase 4 — 2026-10-06

## Veredito

Código e registros podem ser commitados e enviados ao remoto privado após os
checks abaixo. Isso não libera a demo: E05 (HTTP 504) e E13 (ReadTimeout) seguem
sem saída julgável. A avaliação de geração não mede retrieval nem generalização.
A publicação do repositório continua em etapa própria.

## Escopo e fontes

Baseline do diff: `origin/main` = `37ac02b`; HEAD inicial: `b228f22`.
Revisão dos quatro commits pendentes, incluindo o congelamento P09 de 01/10,
e do trabalho de 06/10 ainda no working tree. Revisão focada de código e suas
dependências diretas; leitura de specs/ADRs/relatórios modificados. Não foi
uma auditoria integral de dependências ou de todo o histórico do repositório.

- Busca/cache: `indice.py`, `pool_candidatos.py`, `calibrar_recusa.py`, testes,
  spec 0005 e relatório de integridade.
- Geração: `responder.py`, `provedor_gemini.py`, executor, testes, manifesto,
  specs 0001/0004/0006 e ADR-0006.
- P09: spec 0003, ADR-0005 e relatório de amostra. Preservado o congelamento:
  liderança prazo/rapidez liberada por Luiz; ranking completo bloqueado.
  Não houve reavaliação estatística de P09 nesta auditoria.
- Evidência primária: duas capturas JSONL de execução, agora copiadas sem alteração
  dos registros para `geracao_20261006_evidencias.json`, com hashes dos originais.
- Revisão independente: perfil `sonnet-medium`; orquestrador revisou o diff,
  conferiu fonte/saídas e executou a suíte completa. Sem API nesta auditoria.

## Achados e correções

| Prioridade | Cenário reproduzido | Causa e correção | Evidência |
|---|---|---|---|
| P2 | `sem_evidencia` com ID inventado ou elemento não-string era aceito | O ramo de recusa antecedia a validação de IDs. Validar todos os IDs antes de decidir recusa; lista vazia ou IDs válidos continuam aceitos | `src/rag/responder.py:50`; 4 regressões negativas e 2 controles válidos em `tests/test_responder.py` |
| P2 | `k=1.5` virava 2 resultados; bool/notas fracionárias eram aceitos; `atrasadoo` virava busca vazia e recusa | Comparações de bounds não validavam tipo/domínio. Exigir inteiros sem bool, notas 1–5 e situação do corpus antes do SQL | `src/retrieval/indice.py:38`; 16 entradas inválidas, 3 situações válidas e pipeline sem chamada de geração |
| P2 | Saídas estocásticas julgadas estavam só na `.venv` | Evidência não regenerável precisa sobreviver à troca de máquina. Preservar registros originais e julgamento em JSON revisado versionado | `reports/geracao_20261006_evidencias.json` |
| P3 | Spec/bridge ainda diziam rodada/revisão pendentes; AGENTS dizia nenhuma avaliação liberada | Consolidar estado atual e apontar evidência, distinguindo história de contrato operacional | Spec 0006, AGENTS e bridge; lote restrito E01–E20 |

Os dois defeitos de contrato são preexistentes, não erros observados no lote
real. Correções têm escopo de quatro arquivos Python/testes. Modelo, prompt,
schema, autorização e política sem retry/fallback foram preservados.
Hipóteses consideradas: checagem de entrada ausente (confirmada), comportamento
SQL sem validação (coerção confirmada), mutação na geração/deduplicação (não
necessária para reproduzir). Fixtures determinísticas, dados sintéticos e
cliente falso separaram esses caminhos. Nenhum dado real ou pool foi regenerado.

## Histórico e alcance

O `git blame` localiza executor/hash em `b228f22`; o diff de hoje não removeu
barreira de revisão de contexto, parametrização SQL ou validação do cache.
Citação e filtro foram reforçados por esta auditoria.

Chamadores diretos de produção (busca textual em `src`, sem testes):

| Função | Chamadores diretos | Impacto |
|---|---:|---|
| `buscar` | 1 (`executar_rag`) | Domínio inválido passa a erro visível no pipeline, sem gerar resposta |
| `responder` | 2 (`executar_rag`, executor de avaliação) | ID inválido em recusa passa a `erro_geracao` |
| `embeddings_docs` | 2 (pool e calibração) | Identidade do cache mantém seus consumidores alinhados; sem mudança nesta revisão |

Entrada desconhecida no manifesto, caso ausente, hash diferente ou saída
existente falham antes de criar cliente. O hash identifica payload/configuração,
mas não prova consentimento e não inclui o código de validação da aplicação.
Cenário de injeção: comentário manda inventar reembolso em 30 dias; E19 recusou.
Isso evidencia resistência neste caso, sem garantia geral contra prompt injection.

## Checks

- Suíte antes das correções desta auditoria: **148 testes passaram**.
- Regressões focais antes do fix: **17 falharam, 36 passaram**.
- Focal depois do fix: **53 passaram**.
- Suíte completa final na `.venv`: **174 passaram**, FutureWarning como erro,
  basetemp novo sob pasta pai existente; sem API/download de modelo.
- `pip check`: nenhuma incompatibilidade de requirements.
- `git diff --check`: sem erro de whitespace.
- Conferência externa do remoto: privado, `main`, GitHub
  `luizmaibashi/voc-intelligence-rag-olist`; fetch concluído.
- Varredura dos 4 commits pendentes: 66 blobs únicos, nenhum padrão de chave
  Google/GitHub, chave privada ou valor da credencial atual encontrado. A mesma
  checagem foi aplicada aos arquivos novos/candidatos antes de staging.
  Regex e comparação literal não comprovam ausência de todo dado sensível.
- Textos revisados: comentários genéricos de produto/entrega; aliases no envio.
  IDs originais Olist só no mapa local/versionado já previsto; nunca no payload.

Logs de teste ficam na `.venv` ignorada. O teste novo exerce falhas do domínio,
não compara uma implementação com uma cópia dela. A cobertura do executor
registrada anteriormente não foi medida de novo; esta auditoria não declara
nova porcentagem de cobertura.

## Resultado da geração e revisão humana

Previsão de Luiz, antes das chamadas: 15 utilizáveis e 5 falhas, com preocupação
nos relatos mistos. Primeira tentativa: 19 ConnectError e E20 local. A segunda
foi execução explícita com acesso externo, sem retry automático por caso.

| Origem na rodada 02 | Utilizáveis confirmados por Luiz | Falhas de serviço |
|---|---:|---:|
| Contexto real | 16 | 2 (E05 e E13) |
| Sintético | 1 (E19) | 0 |
| Controle local | 1 (E20) | 0 |

Julgamentos foram confirmações em blocos apresentados pelo agente; parte das
recusas foi apresentada em resumo, sem leitura cega independente. Notas por
caso preservam a confirmação e não inventam anotações livres do usuário.
E17 negou elogio com citação; E18 preservou preço bom, demora percebida e prazo
cumprido. Nenhuma falha de conteúdo foi apontada nas saídas disponíveis.
18 casos com contexto real reutilizam 16 avaliações distintas. Não reportar
uma taxa geral misturando serviço, conteúdo, sintético e controle.

Os registros capturados usam código `b228f22` com manifesto E17 ajustado; as
correções desta auditoria são posteriores. Não apresentar a rodada como uma
avaliação já executada com o novo código. Arquivos originais preservados.

## Próximo passo

1. Nova previsão para reavaliar E05/E13; rodada separada e arquivo novo, mantendo
   histórico e julgamento humano. Não alterar timeout/modelo por tentativa sem
   decisão explícita e evidência.
2. Após resolver o gate de geração, testar o fluxo da spec 0004 com busca,
   filtros efetivos, fontes e contagem. Contextos recuperados adicionais exigem
   revisão/liberação antes de envio; a aprovação do lote não libera o corpus.
3. Entrada reproduzível/README, revisão antes de tornar público e vídeo até 7 min.

Caos Funcional: sem arquivos novos na raiz, dependência nova, `.env`, debug ou
código morto introduzido. JSON revisado é evidência estocástica, não saída
regenerável. `data/eval/gabarito.csv` untracked preexistente foi preservado e
fica fora do commit. Mudanças de outras frentes da base não entram neste push.

## Registro de commit

Correções de contrato: `7691d2b` (quatro arquivos de código/testes).
O hook commit-msg não iniciou dentro do sandbox Windows; o mesmo commit
foi concluído fora do sandbox com o hook normal, sem desativá-lo.

## Alerta de dependência observado no push

Em 2026-10-06, o GitHub informou o alerta aberto GHSA-rrmf-rvhw-rf47 /
CVE-2025-3000 para `torch==2.12.1`, afetado segundo o intervalo <=2.12.1.
Metadados do GitHub classificam como low; a descrição histórica usa a palavra
critical. Não inferir segurança apenas pela classificação. Patch indicado: 2.13.0.
Fonte primária: https://github.com/advisories/GHSA-rrmf-rvhw-rf47;
alerta do repo: https://github.com/luizmaibashi/voc-intelligence-rag-olist/security/dependabot/1.

Superfície informada: corrupção de memória via `torch.jit.script`, ataque local.
Busca direta em src/tests não encontrou TorchScript, torch.load ou
trust_remote_code; o projeto consome SentenceTransformer.encode. Isso não prova
inacessibilidade transitiva na biblioteca. O alerta permanece aberto e o
requirements não foi alterado sem verificar compatibilidade Windows/Python 3.13,
SentenceTransformers e identidade dos embeddings. Não há bloqueador de outra
dependência demonstrado; compatibilidade do patch ainda não foi testada.

Gatilho de revisão: antes da publicação/demo com entrada livre, validar torch
2.13.0 em ambiente separado, pip check e suíte completa, conferir implicações no
cache e atualizar o pin se compatível. Sem upgrade ad hoc no ambiente julgado.
