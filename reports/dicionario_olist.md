# Dicionário do corpus Olist usado no TC4

**Fonte:** [proveniência](proveniencia_olist.md), [EDA](eda_olist.md),
`src/preprocessing/corpus.py` e [ADR 0001](../docs/adr/0001-corpus-limpeza-minima-sem-chunking.md).
O grão é **uma avaliação com comentário por `review_id`**. O corpus histórico tem
42.174 documentos; não representa todos os pedidos nem a operação atual.

## Colunas (pos-limpeza)

| Coluna | Origem e definição | Ausência e uso |
|---|---|---|
| `review_id` | Identificador da avaliação em `order_reviews`; duplicatas ficam com a primeira ocorrência. | Chave do documento e citação. |
| `order_id` | Pedido associado à avaliação. | Junta `orders` e categorias; avaliação e pedido não são o mesmo grão. |
| `texto` | Título e mensagem concatenados, com espaços normalizados. | Texto vazio ou ausência mascarada é excluído; negação e acento são preservados. |
| `nota` | `review_score`, de 1 a 5. | Filtro de polaridade; nota alta não prova elogio ao tema perguntado. |
| `data_avaliacao` | `review_creation_date`. | Data da avaliação, distinta da data da compra. |
| `data_compra` | `order_purchase_timestamp` em `orders`. | Período da compra; limite inclusivo quando usado como filtro. |
| `order_status` | Estado do pedido em `orders`. | Diagnóstico; não equivale à situação calculada da entrega. |
| `situacao_entrega` | Com data real de entrega ausente: `nao_entregue`; dia real posterior ao dia estimado: `atrasado`; demais casos: `no_prazo`. | Horário dentro do dia prometido não conta como atraso; `nao_entregue` agrega estados diversos, inclusive cancelamento e trânsito. |
| `dias_atraso` | Data real da entrega menos data estimada, em dias. | Pode ser negativo no prazo; nulo sem datas necessárias. |
| `categorias` | Categorias dos produtos do pedido, únicas e ordenadas, separadas por `|`. | Sem categoria vira `sem_categoria`; um pedido pode conter várias categorias. |
| `freq_texto` | Número de documentos com o mesmo `texto` após conversão para minúsculas. | Repetição literal, não frequência de tema. |

## Features criadas

`texto`, `situacao_entrega`, `dias_atraso`, `categorias` e `freq_texto` são
derivadas, conforme as definições acima. Os embeddings MiniLM são gerados a
partir de `texto`; não são coluna do Parquet do corpus.

## Conexao com objetivo de negocio

`texto` e `review_id` permitem responder com evidência verificável. `nota`,
`situacao_entrega`, `categorias` e `data_compra` recortam as avaliações antes
da busca. Para medir atrasos, a população elegível é a de avaliações com
comentário associadas a pedidos entregues (`atrasado` ou `no_prazo`):
3.813 de 40.303, 9,46% (IC95% de Wilson: 9,18% a 9,75%). Isso não é a
taxa de atraso de todos os pedidos da Olist. Top-k de similaridade não mede
prevalência de reclamação ou elogio.
