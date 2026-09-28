# P09 — análise da rodada humana 3

**Data:** 2026-09-28. **Status:** diagnóstico; não é teste independente.

## Evidência e decisão

- Luiz revisou 25 avaliações. O CSV original de decisões e notas livres está
  localmente em `Downloads/p09_decisoes_rodada3.csv`; a cópia
  `data/eval/p09_decisoes_rodada3_diagnostico.csv` guarda apenas IDs, temas,
  voto, previsão e decisão, sem comentário ou nota livre.
- Após o ajuste de `elogio_geral`, 20 dos 25 casos tinham pelo menos um
  desacordo entre voto original e regra. Na primeira comparação houve 7
  marcações ausentes de prazo, 10 de integridade, 12 de pedido correto, 12 de
  elogio geral e 1 de texto misto; houve 1 marcação excedente de integridade.
- O CSV de decisões tem 110 linhas de tema: 96 com `sim` ou `nao`, 4 com
  `incerto` e 10 sem decisão. As dez em branco eram votos originais incertos.
  Em 17 das 25 avaliações, os quatro temas receberam `sim` nas decisões.

## Causa dos desacordos

Luiz usou inicialmente uma inferência ampla: quando o cliente apenas elogia,
considerou boa a experiência em todos os aspectos, mesmo sem menção no texto.
Isso responde a uma hipótese de satisfação geral; P09 pergunta **quais
aspectos foram elogiados**. Após discussão, Luiz decidiu separar as duas
leituras: P09 conta somente aspectos citados; satisfação inferida não altera
os quatro temas. Elogio apenas ao produto não vira elogio à entrega.

Nas marcações positivas que a regra deixou de fazer sob a rubrica inicial,
nenhum padrão daquele tema foi acionado pelo texto. Isso é compatível tanto
com lacuna de cobertura lexical quanto com a inferência ampla nos votos.
Como os votos não distinguem essas duas causas de forma confiável, esta
rodada não mede precisão, revocação ou ordem dos temas sob a rubrica final.
Alterar expressões regulares para concordar com esses votos seria ajustar o
classificador ao alvo errado.

## Nova avaliação

`data/eval/p09_amostra_independente_ids.csv` fixa 50 IDs sorteados com
`seed=20260929`, sem reposição, entre as 41.789 avaliações elegíveis após
excluir 385 IDs presentes nos CSVs P09 anteriores. O formulário local
`data/processed/p09_amostra_independente_local.html` contém os textos e não
mostra a previsão da regra. Exporta apenas ID, cinco rótulos e nota opcional.
O HTML está fora do Git por conter comentários brutos.
Antes de rotular ou comparar a amostra, Luiz previu **15 dos 50 casos** com ao
menos um aspecto elogiado no texto que a regra atual deixará de marcar.

Após os votos, comparar por tema com a regra congelada, inspecionar
desacordos, calcular matriz de confusão e intervalos com `n` explícito.
Temas raros podem exigir nova amostra; os 50 casos, sozinhos, não liberam
ranking nem garantem precisão suficiente para cada tema.
