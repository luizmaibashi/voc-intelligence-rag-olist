# Recursos — fontes de ensino e verificação

## Lição0001

- [Introduction to Information Retrieval — avaliação de resultados ordenados](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html):top-k e precisão@k; seleção por ranking não é desenho amostral representativo.
- ../spec/0002-frequencia-atrasos.md: definição da população e contagem do TC4.
- ../adr/0001-corpus-limpeza-minima-sem-chunking.md: documento por avaliação, limpeza e metadados.
- ../../reports/conferencia_corpus_real_20261007.md: captura de busca e contagem4.339/40.303,10,77%,IC95%[10,47%;11,07%]. Consultar somente trecho necessário.

## Observabilidade e avaliação — aulas futuras

- [OpenTelemetry — observability primer](https://opentelemetry.io/docs/concepts/observability-primer/): logs,métricas,traces e diagnóstico por telemetria. Fonte consultada07/10/2026; não implica adoção da biblioteca.
- ../spec/0006-avaliacao-geracao.md: critérios de qualidade, julgamentos, falhas de serviço e conciliação do gate.
- ../../src/rag/tentativas.py: registros atuais de tentativas; observabilidade existente é parcial, não monitoramento completo de produção.

## Enquadramento

- ../../[IAST] - Tech Challenge - Fase 4.pdf,páginas6–10: requisitos e entregáveis.
- [DHL2026](https://group.dhl.com/en/media-relations/press-releases/2026/dhl-ecommerce-trends-report-2026-old-rules-do-not-apply-in-the-age-of-ai.html): contexto setorial,não validação da nossa solução.
- [Zendesk — Surveys dashboard](https://support.zendesk.com/hc/en-us/articles/7043759414042-Accessing-and-viewing-the-Surveys-dashboard): funcionalidades existentes,não benchmark de eficácia.

Fontes externas adicionais são verificadas antes da aula pertinente. Não extrapolar dados históricos para operação atual.

## Lição 0002 — logit, softmax e temperatura

- Workshop Anwar Hermuche (17/10/2026): `raw/04_Agentic_Architectures/-raw-29_mentoria_anwar_arquitetura_ia/extracao_parte1.md` (base da Base_de_Conhecimento), blocos 2–3. Transcrição automática; citar linha.
- [Thinking Machines — Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) (Horace He, 10/09/2025): temperatura 0 não garante determinismo; causa principal é a variação do tamanho do lote. 80 respostas distintas em 1.000 no Qwen3-235B. Consultada 18/10/2026.
- [Google — Gemini API, prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies): afirma que temperatura 0 é determinística; recomenda manter os parâmetros padrão nos "modelos Gemini 3 anteriores", e o 3.6+ ignora valores customizados. Não lista o 3.1-flash-lite. Consultada 18/10/2026.
- [Goodfellow et al. — Deep Learning, cap. 6](https://www.deeplearningbook.org/contents/mlp.html): softmax.
- `../../src/rag/provedor_gemini.py:50`: `temperature=0` no TC4.
