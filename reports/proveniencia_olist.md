# Proveniência: Brazilian E-Commerce Public Dataset by Olist

Registrado em 2026-09-25. Resposta do Luiz às três perguntas do gate: **"não sei"**.
As evidências abaixo foram verificadas em fonte e ficam separadas da resposta dele.

## Fonte

- Resposta do Luiz: não sei.
- Evidência: o enunciado do Tech Challenge Fase 4 (p. 5) indica o Kaggle,
  `https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data`, publicado pela conta `olistbr`.
- Lacuna: não verificamos como a Olist extraiu nem anonimizou os dados antes de publicar.

## Timestamp da fonte

- Resposta do Luiz: não sei.
- Evidência (Kaggle, `kaggle datasets list`, 2026-09-25): última atualização da página em 2021-10-01.
- Evidência (medido nos CSVs): compras de 2016-09-04 a 2018-10-17; avaliações de 2016-10-02 a 2018-08-31.
- Consequência: base histórica e parada há cerca de 8 anos. Serve para demonstrar o método,
  não para afirmar como os clientes da Olist se sentem hoje. Isso vai para o README como limitação.

## Rastro de extração

- Resposta do Luiz: não sei.
- Evidência: baixado em 2026-09-25 com
  `kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip`
  (9 CSVs, 42,6 MB compactado).
