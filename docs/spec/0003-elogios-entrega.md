# Spec 0003 — Baseline de elogios à entrega (P09)

**Status:** congelado em 2026-10-01 (ver critério 6). **Dono da decisão de publicar resultado:** Luiz Maibashi.

## Objetivo

Preparar classificação explicável de temas para P09, preservando elogios em
avaliações mistas. A primeira triagem de 100 comentários, feita pelo agente e
calibrada por Luiz em dois casos limítrofes, encontrou 33 elogios provisórios:
28 mencionam prazo/rapidez, 3 integridade, 5 pedido correto e 2 elogio geral.
Temas se sobrepõem; esta amostra não mede a distribuição do corpus.

## Escopo e contrato

- Entrada: texto de uma avaliação. Saída: conjunto dos quatro temas e indicador
  de texto misto. Texto vazio ou não textual falha visivelmente.
- `prazo_rapidez`: rapidez, antecipação ou cumprimento do prazo informado.
- `integridade`: produto chegou intacto ou em boas condições.
- `pedido_correto`: entrega correspondeu ao pedido ou chegou completa.
- `elogio_geral`: avaliação positiva explícita da entrega como um todo. Pode
  coexistir com um atributo específico no mesmo comentário; não é um rótulo
  residual para todo comentário positivo.
- Os quatro temas de P09 registram **aspectos elogiados no texto**. Um elogio
  geral à entrega não preenche automaticamente prazo, integridade e pedido
  correto; elogio só ao produto também não cria tema de entrega.
- A inferência de que uma avaliação apenas positiva sugere boa experiência é
  uma leitura separada, não uma contagem de aspectos elogiados para P09. Texto
  misto exige preservar, separadamente, os pontos positivos e negativos.
- A nota da avaliação pode sinalizar satisfação geral, mas não substitui o
  texto para rotular aspectos de P09. Exemplo: cinco estrelas com apenas
  "entrega rápida" marca `prazo_rapidez`, sem preencher `integridade`,
  `pedido_correto` ou `elogio_geral`. Este último exige avaliação positiva
  da entrega como um todo no texto.
- Negação da afirmação positiva no mesmo trecho não cria elogio. Se houver
  trecho positivo e outro negativo, manter tema positivo e marcar `misto`.
- Regras locais e determinísticas, sem envio de avaliação para API.

Fora do escopo desta peça: afirmar quais temas lideram em todo o corpus,
atribuir reclamação a produto específico e resolver P05, P08 ou P11.

## Critérios de aceitação e gate seguinte

1. Casos sintéticos de elogio, reclamação, negação e texto misto têm testes.
2. Uma avaliação pode receber vários temas; contagens por tema não devem ser
   somadas como número de avaliações únicas.
3. Antes de publicar ranking do corpus, rotular amostra nova e independente
   com revisão humana; registrar matriz de confusão, `n`, precisão e revocação
   por tema, com incerteza. Fazer error analysis dos erros, então fixar o gate
   de qualidade do ranking. A triagem que orientou as regras não vale como teste.
4. Na revisão humana da rodada 3, Luiz decidiu que "entrega excelente e rápida"
   recebe `elogio_geral` e `prazo_rapidez`. Essa rodada diagnosticou a divergência
   entre rubrica e código; após o ajuste, ela não serve como teste independente.
5. A rodada 3 também revelou outra divergência de rubrica: Luiz inicialmente
   marcou todos os aspectos como bons quando a avaliação só elogiava. Após
   discutir a pergunta P09, decidiu contar nela apenas os aspectos citados e
   manter a inferência de boa experiência separada. Seus votos originais
   permanecem como evidência diagnóstica, não como gabarito para medir P09.
6. **Gate em 2026-10-01:** liberada a afirmação de que prazo/rapidez é o
   aspecto mais elogiado (piso de 9.724 pela regra, com faixa corrigida).
   Ordem do 2º ao 4º lugar segue bloqueada. Evidência e limites em
   `reports/p09_resultado_amostra_independente.md`, seção "Decisão de
   congelamento".

## Riscos

Grafias livres, ironia e negação distante podem escapar às regras. O rótulo
`misto` detecta coexistência de elogio e reclamação no texto; não atribui causa.
Os comentários são subconjunto selecionado dos pedidos, de 2016–2018.
