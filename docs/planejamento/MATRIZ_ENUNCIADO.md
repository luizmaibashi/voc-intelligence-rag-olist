# Matriz enunciado → implementação → evidência → lacuna

Fonte: `[IAST] - Tech Challenge - Fase 4.pdf`, páginas 6–10. Estado em 2026-10-16,
commit `7ea1322`. Legenda: ✅ atende · 🟡 parcial · ❌ falta.

## Requisitos obrigatórios

| # | Requisito (enunciado) | Implementação | Evidência | Status | Lacuna |
|---|---|---|---|---|---|
| 1a | Seleção dos dados | `src/preprocessing/corpus.py` | ADR 0001, `reports/eda_olist.md` | ✅ | — |
| 1b | Limpeza e preparação | Limpeza mínima, sem chunking | ADR 0001 | ✅ | — |
| 1c | Valores ausentes | Sem comentário fica fora; categoria ausente vira `sem_categoria` | ADR 0001 §7 | ✅ | Explicar no README |
| 1d | Organização dos documentos | 1 avaliação = 1 documento + metadados | ADR 0001 | ✅ | — |
| 1e | Embeddings | MiniLM multilíngue | ADR 0002 (n=14, P@10 0,72 [0,55; 0,87]) | ✅ | — |
| 1f | Armazenamento/indexação | DuckDB busca exata + cache amarrado ao encoder | ADR 0002, spec 0005 | ✅ | — |
| 2a | Transformação da pergunta | Pergunta → embedding direto | ADR 0002 | 🟡 | Justificar no README por que não há reescrita (custo × ganho não medido) |
| 2b | Recuperação semântica | `src/retrieval` | Testes; ADR 0002 | ✅ | — |
| 2c | Seleção dos mais relevantes | top-k + filtros nota/situação + deduplicação | spec 0005 | ✅ | — |
| 2d | Contexto enviado ao LLM | `src/rag`, prévia do CLI (spec 0007) | `reports/demo_cli_20261017.md` | ✅ | — |
| 2e | Geração da resposta final | `--acao responder` (spec 0007, `4e96977`) | `reports/demo_cli_20261017.md` (2 respostas reais, suporte aprovado) | ✅ | Citação por resposta, não por afirmação (limite no README) |
| 3 | Respostas com evidências rastreáveis | Citações validadas; rejeita citação inventada | ADR 0003, spec 0001/0006 | ✅ | Citação válida ≠ frase com suporte (limite declarado) |
| 4a | Sem avaliações relevantes | Status `sem_evidencia` | spec 0006, P15 | ✅ | — |
| 4b | Evidência insuficiente | Recusa calibrada (`calibrar_recusa.py`) | P15/recusa julgados | ✅ | — |
| 4c | Fora do escopo | Pergunta de política oficial → recusa | Ensaio sintético, E05 | ✅ | — |
| E1 | Repo GitHub **público** | Remoto privado | — | ❌ | Publicar após revisar dados/segredos |
| E1 | README completo (10 itens) | README atualizado 2026-10-17 | Exemplo real, reprodução Kaggle + SHA | 🟡 | Revisar os 10 itens antes de publicar |
| E2 | Vídeo ≤ 7 min | — | — | ❌ | Roteiro + gravação |

## Desafio adicional (não obrigatório)

| Metadado | Status | Observação |
|---|---|---|
| Nota | ✅ filtro | Ganho de P@10 com filtro em P09/P10 (ADR 0002) |
| Informação de entrega | ✅ filtro `situacao_entrega` + contagem SQL (ADR 0004) | 4.339/40.303 = 10,77%, IC95% [10,47%; 11,07%] |
| Período, categoria | ❌ não é filtro da entrada | Fora do mínimo; só se sobrar prazo |

## Mínima entrega defensável

Bloqueante para a nota: ~~2e~~ (feito em 2026-10-17), **E1 público + revisão
final do README**, **E2 vídeo**. O resto já tem
evidência; é questão de expor no README e no vídeo.

## Baseline barato (hipótese de tarefa)

Tarefa: gestor investiga problemas de entrega com exemplos auditáveis e contagem
definida. Alternativa mais barata: SQL/pandas (filtro de nota/situação) + busca
por palavra-chave (TF-IDF) e leitura manual.

Já medido no mesmo gabarito (ADR 0002, n=14): TF-IDF P@10 0,58 [0,41; 0,74] ×
MiniLM 0,72 [0,55; 0,87]; ICs se sobrepõem, diferença não conclusiva. A contagem
já é SQL puro (sem RAG). Conclusão provisória: o ganho do RAG está em **síntese
com citação** sobre o top-k, não na recuperação nem na frequência. Validação com
usuário real: pendente.
