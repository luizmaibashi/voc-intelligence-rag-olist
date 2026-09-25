# ADR-0001: Corpus com limpeza mínima, um documento por avaliação e repetidos tratados na busca

**Data**: 2026-09-25
**Status**: Accepted
**Proposto por**: Luiz Maibashi (revisado e aprovado em 2026-09-25)
**Contexto**: Base de conhecimento do RAG de Voice of Customer (Olist)

---

## 1. Contexto

O enunciado exige justificar seleção, limpeza, tratamento de ausentes e organização dos documentos.
A EDA (`reports/eda_olist.md`) mediu o que a base realmente é:

- 99.224 avaliações; 41,3% com comentário (IC95% 41,0% a 41,6%).
- Comentário mediano de 9 palavras (p90 = 28; máximo 208 caracteres, indício de limite no formulário).
- 17,4% dos textos com comentário são idênticos a outro (`muito bom` aparece 472 vezes).
- Quem comenta tem nota média 3,67 contra 4,38 de quem não comenta: a base super-representa insatisfeitos.
- 789 `review_id` repetidos, todos com a mesma mensagem (mesma avaliação ligada a mais de um pedido).
- Em 1.737 avaliações o título é o único texto.

**Restrição:** o embedding de um RAG é gerado por modelo contextual, que lê a frase inteira.

## 2. Decisão

Implementada em `src/preprocessing/corpus.py` (`montar_corpus`), com 16 testes em `tests/test_corpus.py`.

1. **Limpeza mínima.** Só normaliza espaços e quebras de linha. Mantém stopwords, negação, acento, caixa e erro de digitação.
2. **Título e mensagem juntos** num único texto, sem duplicar pontuação.
3. **Descarta** avaliação sem texto e texto que é só ausência disfarçada (`.`, `-`, `ok`, `não`, `sim` e similares).
4. **Uma linha por `review_id`.** Mantém a primeira cópia das duplicatas.
5. **Sem chunking.** Cada avaliação é um documento inteiro.
6. **Repetidos ficam no corpus**, com a coluna `freq_texto`. A junção de textos iguais acontece na etapa de busca.
7. **Metadados para filtro:** nota, datas, `situacao_entrega` (no prazo, atrasado, não entregue), `dias_atraso` e categorias do pedido (várias separadas por `|`, ausente vira `sem_categoria`).

**Se não fizermos:** limpeza clássica apagaria a negação ("não chegou" vira "chegou") e inverteria o sentido de reclamações.
Sem tratar repetidos, uma pergunta sobre elogios traria dez "muito bom" no top-k, sem valor como evidência.
Juntar repetidos já no corpus apagaria nota e entrega de cada cópia, que são os filtros mais fortes da base.

**Se fizermos:** corpus de 42.174 documentos (36.453 textos distintos, sem diferenciar maiúsculas), com os metadados preservados.

## 3. Consequências

**Positivas**
- O texto chega ao modelo de embedding como o cliente escreveu.
- A frequência de cada texto continua disponível para responder perguntas de "mais comum".
- O atraso vira filtro: nota média 4,29 no prazo (n = 88.658) contra 2,57 com atraso (n = 7.701).

**Negativas**
- A busca precisa de um passo a mais para juntar textos iguais. Sem ele, o problema do top-k repetido continua.
- Comentários de 1 ou 2 palavras (13,8%) ficam no corpus e carregam pouca informação.
- Descartar `não`/`sim` isolados perde um sinal fraco em notas extremas.

## 4. Alternativas descartadas

| Opção | Vantagem | Por que foi rejeitada |
|---|---|---|
| Limpeza clássica (stopwords, stemming, minúsculas) | Padrão de TF-IDF | Destrói negação e contexto que o embedding usa. Fica só para o baseline TF-IDF |
| Chunking por tamanho fixo | Padrão de tutorial de RAG | Documento mediano tem 9 palavras; não há o que quebrar |
| Juntar textos idênticos no corpus | Índice menor | Apaga nota, entrega e categoria de cada cópia |
| Descartar comentários curtos | Menos ruído | "Não recebi" tem 2 palavras e é evidência forte |

## 5. Impacto e validação

**Métricas de sucesso** (medidas na etapa de avaliação do RAG):
- Top-k de perguntas sobre elogios sem textos repetidos depois da junção na busca.
- Respostas sobre entrega recuperam avaliações com `situacao_entrega` coerente com a pergunta.

**Cenários de regressão**
- Mudança no corpus que remova `freq_texto` ou `situacao_entrega` quebra os filtros da busca.
- Nova regra de limpeza que remova negação: coberta pelo teste de preservação de negação.

## 6. Referências

- `reports/eda_olist.md`, `reports/proveniencia_olist.md`
- Base de Conhecimento: `wiki/concepts/01_data_and_mlops/Pre_Processamento_Texto_e_Normalizacao.md`
- Aula de estatística sobre viés de seleção: `raw/pos_tech/fase1_Business understanding and data analysis/03_estatistica_essencial/Aula_01_EXTRACAO_GEMINI.md`
