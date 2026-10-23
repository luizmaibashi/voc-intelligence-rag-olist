# Spec 0014 — Ganho da busca híbrida (MiniLM + TF-IDF por RRF)

**Status:** congelada antes da medição · **Data:** 2026-10-23 · **Branch:** `medicao-hibrida`
**Script:** `src/eval/ganho_hibrida.py` · **Testes:** `tests/test_ganho_hibrida.py`

## Problema

A busca do produto é só densa (MiniLM). Na ADR 0002 (n = 14, busca do pooling), as três
buscas erram em perguntas diferentes: P13 (taxa) TF-IDF 0,7 × MiniLM 0,3; P09 TF-IDF 1,0 × 0,7.
A ADR deixou a híbrida "como candidata, a medir no mesmo gabarito antes de adotar".
Esta spec mede; não altera a busca do produto nem nenhum arquivo coberto pelo hash de
liberação (`src/rag/liberacao.py:14`).

## Desenho

- **Perguntas:** P01–P14 de `data/eval/perguntas.csv` (`tipo != sem_resposta`), sem filtro.
- **Braços:**
  - `densa`: busca do produto (`indice.buscar`), mesmo cache e identidade de vetores do CLI
    (`data/processed/emb_busca_minilm.npy`, spec 0010), top-100.
  - `tfidf`: configuração do pooling (`TfidfVectorizer(strip_accents="unicode", lowercase=True)`,
    um documento por texto distinto em minúsculas), top-100 com score > 0.
  - `hibrida`: RRF sobre as duas listas, `score = Σ 1/(60 + posição)`, chave = texto em
    minúsculas, representante da densa quando o texto está nas duas; desempate por melhor
    posição e depois pelo texto.
- **k da fusão = 60** (artigo original). Profundidade 100: um texto em ~60º nas duas listas
  ainda pode entrar no top-10 da híbrida.
- **Julgamento:** textos inéditos do top-10 dos três braços (inédito = ainda não julgado na
  pergunta, em `julgamento.csv` ou `julgamento_filtros.csv`) + 2 âncoras de setembro por
  pergunta, embaralhados, sem braço. Formulário local cego (`formulario`). Rótulo de setembro
  prevalece; âncoras medem deriva do anotador.
- **Métricas (k = 10):** P@10, RR (MRR na média) e revocação relativa ao pool conhecido, por
  pergunta e braço; média com IC95% por bootstrap sobre as perguntas; diferença pareada
  híbrida − densa.
- **Latência:** tempo de consulta por braço (sem carga do modelo nem do índice) e tempo de
  ajuste do TF-IDF. No CLI cada pergunta é um processo, então o ajuste entra no custo extra.

## Critério de adoção (aprovado por Luiz em 2026-10-23, antes de medir)

A híbrida entra no produto só se **os quatro** passarem:

1. MRR médio pareado: híbrida ≥ densa + 0,03;
2. P@10 médio: híbrida ≥ densa;
3. nenhuma pergunta perde mais de 0,2 de P@10;
4. custo extra mediano (consulta TF-IDF + ajuste) ≤ 1 s na máquina da demo.

Com n = 14 o IC vai incluir zero: a adoção é aposta de engenharia com incerteza declarada,
não prova de superioridade. Além do critério, só adota antes da gravação se o branch de
adoção estiver auditado até 29/10; senão, a medição entra no vídeo e no README como
resultado, e a adoção fica para depois.

## Predição (Luiz registra antes de `medir`)

Em `docs/tc4/EVOLUCAO_PRODUTO_TC4.md` na base de conhecimento.

## Execução

```powershell
python -X utf8 -m src.eval.ganho_hibrida origem      # corpus + MiniLM; só na máquina de casa
python -X utf8 -m src.eval.ganho_hibrida planilha
python -X utf8 -m src.eval.ganho_hibrida formulario  # data/processed, fora do Git
# Luiz julga e baixa julgamento_hibrida.csv, que substitui data/eval/julgamento_hibrida.csv
python -X utf8 -m src.eval.ganho_hibrida medir       # só pandas/numpy
```

## Limites

- n = 14 perguntas, um anotador; IC descritivo.
- Revocação relativa ao pool: relevante que nenhum braço trouxe não conta.
- O TF-IDF do pooling não é um BM25; BM25 fica como variante se houver tempo.
- `hibrida_origem.csv` versiona textos de avaliações (mesma prática de `filtros_origem.csv`);
  varredura de PII heurística antes do commit.
