# Ganho da busca híbrida — resultado (spec 0014)

**Data:** 2026-10-23 · **Branch:** `medicao-hibrida` · **Veredito:** não adotar

Critério, `k = 60` e profundidade 100 congelados antes da medição (`cf08892`); julgamento cego
de 65 itens (37 inéditos + 28 âncoras) commitado antes de rodar `medir` (`da1b1a0`); previsão do
Luiz registrada na base antes de medir.

## Resultado (n = 14 perguntas, um anotador, IC95% por bootstrap sobre as perguntas)

| Busca | P@10 | MRR | Revocação relativa ao pool |
|---|---|---|---|
| Densa (busca do produto) | 0,71 [0,55; 0,86] | 0,79 [0,60; 0,95] | 0,37 [0,27; 0,47] |
| Híbrida (RRF, k = 60) | 0,64 [0,46; 0,81] | 0,77 [0,57; 0,94] | 0,30 [0,22; 0,37] |
| TF-IDF | 0,58 [0,41; 0,74] | 0,78 [0,57; 0,95] | 0,28 [0,20; 0,37] |

Diferença pareada híbrida − densa: P@10 −0,08 [−0,19; +0,04]; MRR −0,02 [−0,19; +0,15].

| Item do critério | Valor | Passa |
|---|---|---|
| Ganho de MRR ≥ +0,03 | −0,017 | não |
| Ganho de P@10 ≥ 0 | −0,079 | não |
| Nenhuma pergunta perde > 0,2 de P@10 | pior −0,5 (P03) | não |
| Custo extra ≤ 1 s | 0,47 s | sim |

P@10 por pergunta (densa → híbrida): P03 0,9 → 0,4; P04 1,0 → 0,6; P05 0,9 → 0,7; P13 0,3 → 0,1;
P02 0,4 → 0,3; P09 0,6 → 0,5; P11 1,0 → 0,9; P12 0,6 → 0,5. Sobem: P07 0,6 → 1,0; P08 0,7 → 0,9.
Iguais: P01, P06, P10, P14 (P14 é 0 nas três buscas).

A densa e o TF-IDF reproduzem a ADR 0002 (densa 0,72/0,79 no pooling; TF-IDF 0,58/0,78 idêntico,
140/140 textos do top-10 em comum). **Isto também remede as 14 perguntas na busca do produto:**
P@10 0,71 [0,55; 0,86], que substitui a ressalva de "9 perguntas não remedidas".

## Robustez

- **Âncoras:** 4 discordâncias em 28 (14%; IC95% de Wilson ~6% a 31%), contra 1 em 10 na spec 0009.
  Duas em P03 (1 → 0, relatos de "recebi menos do que comprei", que o critério da pergunta exclui),
  uma em P02 (0 → 1), uma em P12 (0 → 1). O rótulo de setembro prevalece. Usar o rótulo novo
  nas âncoras não muda o veredito (P@10 −0,07; MRR −0,02; pior −0,5).
- **Melhor caso:** mesmo se os 37 inéditos fossem todos relevantes, a híbrida não passaria
  (MRR +0,024 < 0,03; P03 ainda perde 0,4). O veredito não depende do julgamento novo.

## Mecanismo

O RRF com `k = 60` tem curva achatada: estar em 13º numa lista e 61º na outra vale mais que
estar em 1º numa lista só (`1/73 + 1/121 = 0,022 > 1/61 = 0,016`). Ele premia **consenso**,
e o consenso entre as duas buscas aqui é o vocabulário genérico que ambas compartilham:

- **P09** (elogio à entrega): "ótima compra e entrega" é 1º na densa e não aparece no TF-IDF;
  "demora na entrega" está em 13º e 61º. A fusão põe reclamações no topo (RR 1,0 → 0,2).
- **P13** (taxa): o TF-IDF acerta sozinho (0,7) com textos que contêm "taxa", ausentes do
  top-100 da densa. A fusão prefere "falta de consideração com o cliente", que está no meio das
  duas listas por causa de "cliente". Resultado 0,1: pior que as duas buscas isoladas.
- **P03** (produto que não comprou): textos de "não recebimento" sobem por estarem nas duas
  listas, sem responder à pergunta.

As buscas erram em perguntas diferentes (ADR 0002), e justamente por isso a fusão por consenso
apaga o acerto exclusivo de cada uma em vez de somá-lo.

## Decisão e limites

- A busca do produto continua densa. Nenhum arquivo do hash muda; E-A, E-B e P15 seguem válidas.
- Variantes (k menor, pesos, usar TF-IDF só quando a pergunta tem termo raro) foram pensadas
  **depois** de ver o resultado. Testá-las nas mesmas 14 perguntas seria ajustar ao gabarito:
  exigem perguntas novas, separadas, antes de qualquer alegação.
- n = 14, um anotador, revocação relativa ao pool; TF-IDF do pooling, não BM25.
