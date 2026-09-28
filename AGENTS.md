# Contexto do projeto — Tech Challenge Fase 4

Voice of Customer Intelligence com avaliações históricas da Olist. A entrega é um
repositório público e vídeo de até 7 minutos para a FIAP. O corpus em
`data/processed/corpus_reviews.parquet` é regenerável e fica fora do Git.

## Termos do domínio

- **Avaliação com comentário:** linha de `montar_corpus`, identificada por
  `review_id`, após excluir textos vazios ou ausência mascarada.
- **Entrega atrasada:** `situacao_entrega == "atrasado"`, calculada em
  `src/preprocessing/corpus.py` pela data real posterior à estimada.
- **Pedido entregue:** `situacao_entrega` em `{"atrasado", "no_prazo"}`.
- **Frequência:** contagem no corpus elegível inteiro, com numerador,
  denominador e período. `freq_texto` mede repetição literal de texto;
  top-k de busca não mede frequência temática.

## Ponteiros de decisão

- Ao mudar o corpus ou a unidade de contagem, leia `docs/adr/0001-corpus-limpeza-minima-sem-chunking.md`.
- Ao responder frequência de atraso, leia `docs/spec/0002-frequencia-atrasos.md` e
  `docs/adr/0004-contagem-atrasos.md`.
- Ao mudar geração e recusa do RAG, leia `docs/spec/0001-resposta-com-evidencias.md`.

Avaliações têm texto livre: revise dados pessoais e o nível de serviço antes
de qualquer envio externo. A chave Gemini atual está no nível gratuito;
avaliações reais ainda não foram liberadas para envio nesta frente.
