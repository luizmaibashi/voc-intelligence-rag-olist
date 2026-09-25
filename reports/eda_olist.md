# EDA: avaliações Olist

Gerado por `src/eda/01_eda_reviews.py`. n = 99.224 avaliações.

## 1. Duplicatas

- `review_id` repetido: 814 de 99.224 (0,8%; IC95% 0,8% a 0,9%)
- Linha inteira repetida: 0
- `order_id` com mais de uma avaliação: 551 de 99.224 (0,6%; IC95% 0,5% a 0,6%)
- Dos `review_id` repetidos, com a mesma mensagem em todas as cópias: 789 de 789
- Textos idênticos (entre avaliações com texto): 7.113 de 40.950 (17,4%; IC95% 17,0% a 17,7%)
- 10 textos mais repetidos:

  - `muito bom`: 472
  - `bom`: 342
  - `recomendo`: 234
  - `otimo`: 227
  - `ótimo`: 197
  - `excelente`: 158
  - `ok`: 149
  - `tudo ok`: 93
  - `boa`: 91
  - `ótimo produto`: 81

## 2. Colunas constantes

- nenhuma

## 3. Sentinelas

- `review_score` fora de 1 a 5: 0
- Distribuição de nota: {1: 11424, 2: 3151, 3: 8179, 4: 19142, 5: 57328}

## 4. Ausência mascarada no texto

- Textos que são só `['-', '.', '..', '...', 'a', 'nada', 'nao', 'não', 'ok', 'sim', 'x']`: 243 de 40.950 (0,6%; IC95% 0,5% a 0,7%)
- Comentários com 1 ou 2 palavras: 5.645 de 40.950 (13,8%; IC95% 13,5% a 14,1%)

## 5. Outliers relacionais

- Resposta registrada antes da criação da avaliação: 0
- Avaliação criada antes da compra: 64 de 99.224 (0,1%; IC95% 0,1% a 0,1%)

## 6. Nulos por coluna

- `review_comment_title`: 87.656 de 99.224 (88,3%; IC95% 88,1% a 88,5%)
- `review_comment_message`: 58.247 de 99.224 (58,7%; IC95% 58,4% a 59,0%)
- `order_approved_at`: 156 de 99.224 (0,2%; IC95% 0,1% a 0,2%)
- `order_delivered_carrier_date`: 1.756 de 99.224 (1,8%; IC95% 1,7% a 1,9%)
- `order_delivered_customer_date`: 2.865 de 99.224 (2,9%; IC95% 2,8% a 3,0%)

## 7. Redundância

- Tem título: 11.566 de 99.224 (11,7%; IC95% 11,5% a 11,9%); tem título e não tem mensagem: 1737

## 8. Relação com a nota

- Nota média, entregue no prazo: 4,29 (n=88.658; IC95% 4,29 a 4,30)
- Nota média, entregue com atraso: 2,57 (n=7.701; IC95% 2,53 a 2,60)
- Nota média, não entregue: 1,76 (n=2.865; IC95% 1,71 a 1,81)
- Status do pedido entre notas 1: {'delivered': 9406, 'shipped': 644, 'unavailable': 463, 'canceled': 422, 'processing': 256}

## 9. A ausência de texto prevê a nota?

- Nota média com texto: 3,67 (n=40.950; IC95% 3,65 a 3,68)
- Nota média sem texto: 4,38 (n=58.274; IC95% 4,37 a 4,39)
- Nota 1, escreveu comentário: 8.744 de 11.424 (76,5%; IC95% 75,8% a 77,3%)
- Nota 2, escreveu comentário: 2.145 de 3.151 (68,1%; IC95% 66,4% a 69,7%)
- Nota 3, escreveu comentário: 3.556 de 8.179 (43,5%; IC95% 42,4% a 44,6%)
- Nota 4, escreveu comentário: 5.970 de 19.142 (31,2%; IC95% 30,5% a 31,8%)
- Nota 5, escreveu comentário: 20.535 de 57.328 (35,8%; IC95% 35,4% a 36,2%)

## Perfil do texto (avaliações com comentário)

- Palavras por comentário: p10=2, mediana=9, p90=28, máx=45
- Com quebra de linha dentro do texto: 2.710 de 40.950 (6,6%; IC95% 6,4% a 6,9%)
