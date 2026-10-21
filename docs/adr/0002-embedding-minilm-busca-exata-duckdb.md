# ADR-0002: Embedding MiniLM multilíngue e busca exata em DuckDB com filtro por metadado

**Data**: 2026-09-25
**Status**: Accepted
**Proposto por**: Luiz Maibashi (direção aprovada em 2026-09-25)
**Contexto**: Recuperação do RAG de Voice of Customer (Olist)

---

## 1. Contexto

O enunciado deixa livre a escolha de modelo de embedding, banco vetorial e técnica de recuperação,
mas exige justificar, exige "armazenamento e indexação" e diz que será avaliada "principalmente a
capacidade da solução de recuperar informações relevantes". O desafio adicional pede filtros por
nota, período, entrega e categoria.

**Tamanho do problema:** 36.453 textos distintos (ADR-0001), 384 dimensões por vetor, cerca de 56 MB.

**Medição com gabarito humano** (`data/eval/`):
- 14 perguntas de gestor escritas pelo Luiz (`perguntas.csv`), 4 delas de frequência.
- Pooling: top-10 de MiniLM, E5 e TF-IDF por pergunta, juntos e sem repetição (`src/eval/pool_candidatos.py`).
- 393 candidatas julgadas às cegas pelo Luiz (`julgamento.csv`), 242 relevantes.
- P09 e P12 rejulgadas com critério explícito depois de uma instrução errada de rotulagem
  (a regra "vale se é sobre o tema" apagava a polaridade de P09).

Resultado (n = 14 perguntas, IC95% por bootstrap sobre as perguntas):

| Busca | Precisão@10 | Revocação@10 (relativa ao pool) | MRR |
|---|---|---|---|
| MiniLM (`paraphrase-multilingual-MiniLM-L12-v2`) | 0,72 [0,55; 0,87] | 0,41 [0,31; 0,50] | 0,79 [0,60; 0,95] |
| E5 (`intfloat/multilingual-e5-small`) | 0,59 [0,41; 0,76] | 0,37 [0,27; 0,50] | 0,79 [0,59; 0,95] |
| TF-IDF | 0,58 [0,41; 0,74] | 0,32 [0,23; 0,40] | 0,78 [0,57; 0,95] |

Diferença pareada de precisão MiniLM − E5: +0,14 [−0,06; +0,34]. Nenhuma diferença é conclusiva.

As três buscas erram em perguntas diferentes: P04 (foto do site) MiniLM 1,0 contra E5 0,2;
P13 (taxa) TF-IDF 0,7 contra MiniLM 0,3; P09 (elogio à entrega) TF-IDF 1,0 contra 0,7 dos embeddings.

## 2. Decisão

1. **Embedding: MiniLM multilíngue.** Melhor estimativa de precisão e cossenos mais espalhados
   (par sem relação 0,05, par parecido 0,21), o que facilita calibrar o corte de recusa.
   O E5 comprime tudo perto de 0,8 a 0,9.
2. **Busca exata, sem índice aproximado.** Com 36 mil vetores, comparar a pergunta com todos custa
   dezenas de milissegundos e nunca perde resultado por aproximação.
3. **Armazenamento e consulta em DuckDB.** Vetores `FLOAT[384]` e metadados na mesma tabela; a busca
   é SQL com `array_cosine_similarity`, e o filtro por metadado vira `WHERE`
   (ex.: `nota >= 4` para elogios). Embutido, sem servidor, reproduzível com `pip install`.
4. **Referência em NumPy** (produto escalar + ordenação), usada em teste: o DuckDB tem que devolver os
   mesmos scores do top-10, com tolerância para empates.
5. **Busca híbrida com TF-IDF fica como candidata**, a medir no mesmo gabarito antes de adotar.

**Verificado em 2026-09-25:** DuckDB 1.5.2, 1 pergunta, top-10 idêntico ao NumPy, 49 ms, filtro
`nota >= 4` funcionando. Uma pergunta só: a comparação completa vira teste.

**Se não fizermos:** um banco vetorial dedicado acrescenta dependência e servidor para um problema de
escala que não existe aqui; NumPy puro resolve a busca, mas não demonstra armazenamento nem SQL.

**Se fizermos:** recuperação exata e rápida, filtros do desafio adicional em SQL, e o padrão é o mesmo
do pgvector (vetor e metadado na mesma tabela, busca por `ORDER BY` de similaridade).

## 3. Consequências

**Positivas**
- O filtro por nota resolve a armadilha de polaridade melhor que qualquer troca de modelo:
  "entrega rápida" × "entrega lenta" tem cosseno 0,76 no MiniLM.
- Trocar de modelo custa só regenerar o cache de embeddings (`data/processed/emb_*.npy`).
- SQL na recuperação conversa com a lacuna de SQL registrada na frente de carreira.

**Negativas**
- A escolha do modelo não tem significância estatística. É decisão com base na estimativa, reversível.
- Busca exata cresce linearmente: acima de ~1 milhão de documentos ou com vários usuários
  simultâneos, migrar para índice aproximado (HNSW) ou pgvector.
- Avaliador pode esperar ver um "banco vetorial" nominal; a justificativa com números cobre isso no vídeo.

## 4. Alternativas descartadas

| Opção | Vantagem | Por que foi rejeitada |
|---|---|---|
| E5 multilíngue | Modelo mais recente | Precisão estimada menor; cossenos comprimidos dificultam o corte de recusa |
| TF-IDF sozinho | Sem modelo, explicável | Só casa palavra igual; revocação estimada mais baixa |
| Chroma | Nome conhecido, filtro por metadado | Não treina SQL; mais uma dependência para o mesmo resultado |
| FAISS | Padrão de busca vetorial | Sem filtro por metadado nativo; índice aproximado desnecessário nessa escala |
| pgvector (Postgres) | Padrão de mercado | Exige servidor; atrapalha reproduzir o projeto |
| Só NumPy | Mínimo possível | Não demonstra armazenamento nem filtro em SQL |

## 5. Impacto e validação

**Métricas de sucesso**
- Teste: top-10 do DuckDB igual ao do NumPy (scores com tolerância) em todas as perguntas do gabarito.
- ~~Precisão@10 do MiniLM com filtro por metadado maior que sem filtro nas perguntas com polaridade (P09, P10).~~
  Mal formulada: P10 já estava em 1,0 sem filtro (efeito teto). Substituída em 2026-10-21 pela
  regra da spec 0009 (ganho ≥ +0,2 onde há espaço, sem perda nas demais). **Resultado**
  (`reports/ganho_filtros_20261021.md`, n = 5): P09 0,6 → 1,0 com `nota >= 4`; P02 0,4 → 0,6 com
  `situacao_entrega = 'nao_entregue'`; P01, P10 e P11 mantidas em 1,0. Filtro de nota quase não
  perde relevante; filtro de entrega deixa de fora relatos de pedidos marcados de outro jeito.
  Na busca do produto, P09 sem filtro é 0,6, não 0,7: o pooling vetorizou só a primeira grafia de
  textos que diferem por maiúscula, e o MiniLM diferencia maiúsculas.
- Latência de busca abaixo de 200 ms por pergunta.

**Limitações da medição**
- n = 14 perguntas e um único anotador.
- Revocação relativa ao pool: avaliação relevante que nenhuma das três buscas achou não entra no gabarito.
- Nenhuma pergunta terminou sem resposta (P14 tem 1 relevante). Antes de calibrar a recusa, é preciso
  acrescentar 3 ou 4 perguntas sem resposta conferidas no corpus.

**Cenários de regressão**
- Trocar o modelo sem regenerar o cache: o script de pooling compara o tamanho, mas não o nome do modelo.
- Empates de score (textos quase iguais) trocando a ordem do top-10 entre NumPy e DuckDB.

## 6. Referências

- `data/eval/perguntas.csv`, `data/eval/julgamento.csv`, `data/eval/pool_origem.csv`
- `src/eval/pool_candidatos.py`
- ADR-0001 (corpus e `freq_texto`)
