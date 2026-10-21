# Ganho dos filtros de metadados na recuperação — 2026-10-21

Execução da `docs/spec/0009-ganho-filtros-metadados.md`, aprovada por Luiz em
2026-10-21. A previsão foi registrada e commitada (40d7f28) antes de qualquer
julgamento novo. Busca local, sem Gemini e sem envio externo.

## Resposta em uma frase

Nas duas perguntas em que o embedding se confunde, o filtro escolhido lendo a
pergunta subiu a precisão: P09 (elogio à entrega) de 0,6 para 1,0 com `nota >= 4`
e P02 (pedido que nunca chega) de 0,4 para 0,6 com `situacao_entrega = 'nao_entregue'`.
Nas três que já acertavam tudo, não houve perda. É o desfecho A da spec: n = 5
perguntas, evidência de caso, sem significância estatística.

## Resultado

Precisão@10 do MiniLM pela busca do produto (`indice.buscar`), mesma função nos dois braços:

| Pergunta | Filtro | Sem filtro | Com filtro | Δ | Leitura | Previsão do Luiz |
|---|---|---|---|---|---|---|
| P01 — reclamações sobre atraso | `atrasado` | 1,0 | 1,0 | 0,0 | neutro (teto) | 1,0 ✓ |
| P02 — pedido nunca chega | `nao_entregue` | 0,4 | 0,6 | +0,2 | ganho | 0,7 (errou por 0,1) |
| P09 — elogios à entrega | `nota >= 4` | 0,6 | 1,0 | +0,4 | ganho | 1,0 ✓ |
| P10 — clientes satisfeitos | `nota >= 4` | 1,0 | 1,0 | 0,0 | neutro (teto) | 1,0 ✓ |
| P11 — pontos das notas ruins | `nota <= 2` | 1,0 | 1,0 | 0,0 | neutro (teto) | 1,0 ✓ |

Diferença pareada média: +0,12 [+0,00; +0,28], n = 5, IC por bootstrap sobre as
perguntas. Com 5 perguntas o IC é só descritivo, como a spec avisou antes de rodar.
Desfecho previsto (A) confirmado; 4 dos 5 números previstos acertaram em cheio.

**Variantes exploratórias** (sem peso na decisão): P09 com `no_prazo` chegou a 0,8,
abaixo do filtro de nota; P01 com `nota <= 2` ficou em 1,0.

## O mecanismo, avaliação por avaliação

P09 sem filtro, nota e julgamento do top-10 em ordem: 5✓ 1✗ 5✓ 1✗ 1✗ 5✓ 5✓ 5✓ 2✗ 1✓.
Os quatro erros são reclamações com nota 1 ou 2 ("Demora na entrega", "Solicito
entrega da mercadoria"): o embedding acha "entrega" e ignora a polaridade, o mesmo
problema do cosseno 0,76 entre "entrega rápida" e "entrega lenta". Com `nota >= 4`
as 10 são elogio.

P02 com filtro: os 6 acertos são relatos de nota 1 de pedido não recebido. Os 4 erros
seguem no top-10 porque o pedido está marcado como não entregue, mas o texto fala de
atraso ou de atendimento, não de pedido que nunca chegou (ex.: "muita demora na
entrega", "Nao entrega o pedido no prazo certo").

Para o gestor: o filtro de metadado não substitui o embedding, completa. O embedding
acha o assunto, a nota garante o lado (elogio ou reclamação).

## Custo do filtro que P@10 não mostra

Distribuição dos relevantes do pool de setembro dentro do recorte de cada filtro
(o anexo da spec, aberto só depois da previsão):

| Pergunta | Filtro | Relevantes conhecidos dentro do recorte |
|---|---|---|
| P01 | `atrasado` | 17 de 30 |
| P02 | `nao_entregue` | 4 de 14 |
| P09 | `nota >= 4` | 23 de 24 |
| P10 | `nota >= 4` | 23 de 23 |
| P11 | `nota <= 2` | 15 de 19 |

Os filtros de nota quase não perdem relato relevante. Os filtros de situação de
entrega perdem muito: 10 dos 14 relatos de "não chegou" conhecidos estão em pedidos
marcados atrasado ou no prazo, e 13 das 30 reclamações de atraso estão fora de
`atrasado`. A situação registrada no sistema e o que o cliente relata divergem.
Recomendação: usar filtro de nota para polaridade; usar filtro de entrega para
recortar a população ("só pedidos atrasados"), sabendo que deixa relatos de fora.

## Controles

- **Âncoras:** 10 avaliações já julgadas em setembro entraram embaralhadas na
  planilha. Luiz discordou de si mesmo em 1 de 10 (P11, "Quando eu receber dou
  notas melhor": 1 em setembro, 0 agora). Abaixo do limite de 2 da spec; o critério
  não mudou de forma relevante.
- **Julgamento cego:** formulário local (`src/eval/gerar_formulario_filtros.py`)
  sem indicação de braço nem situação de entrega; a nota ficou visível como no
  julgamento original. 18 avaliações inéditas + 10 âncoras = 28 julgamentos.
- **Linha de base do produto ≠ linha de base do pooling.** A busca do produto sem
  filtro não repete o top-10 julgado em setembro em P01 (2 avaliações) e P09 (1).
  Causa: o tokenizador do MiniLM diferencia maiúsculas, o pooling vetorizou só a
  primeira grafia de cada texto e o produto encontra a variante com score maior
  ("demora na entrega" acima de "Demora na entrega"). Efeito: P09 sem filtro é 0,6
  na busca do produto, não 0,7. Os números acima usam a busca do produto nos dois
  braços. O 0,72 do ADR-0002 continua sendo a medida da busca do pooling; as outras
  9 perguntas não foram remedidas na busca do produto.

## Riscos verificados

- n = 5 perguntas e um único anotador; nenhum número aqui sustenta "o filtro melhora
  a recuperação em geral". Sustenta: "nas perguntas com polaridade, o filtro de nota
  tirou as reclamações do top-10 de elogios".
- O efeito no P@10 global é pequeno por construção: no máximo +0,06 nas 14 perguntas.
  Não usar o número global para defender os filtros.
- Filtros foram escolhidos pela regra da spec antes de rodar; o filtro do CLI é manual,
  então o resultado mede "gestor que escolhe o filtro óbvio", não filtro automático.
- Revocação relativa ao pool sobe com filtro só porque o pool cresceu com as
  inéditas; não comparar revocação entre braços.
- Origem dos dados: Olist público, proveniência em `reports/proveniencia_olist.md`.
  Textos de avaliação ficaram locais; o formulário está em `data/processed/` (fora do Git).

## Reprodução

```bash
python -m src.eval.ganho_filtros origem    # top-10 dos braços -> data/eval/filtros_origem.csv
python -m src.eval.ganho_filtros planilha  # planilha cega -> data/eval/julgamento_filtros.csv
python -m src.eval.gerar_formulario_filtros
python -m src.eval.ganho_filtros medir
```

## Texto proposto para README e vídeo (não aplicado aqui)

README, seção de recuperação: "Filtros de metadados: em P09 (elogios à entrega) o
filtro `nota >= 4` levou a Precisão@10 de 0,6 para 1,0, porque o embedding não separa
elogio de reclamação (cosseno 0,76 entre 'entrega rápida' e 'entrega lenta'). Em P02,
`situacao_entrega = 'nao_entregue'` foi de 0,4 para 0,6. Nas três perguntas que já
estavam em 1,0, nada mudou. n = 5 perguntas, sem significância estatística. O filtro
de entrega deixa de fora relatos de pedidos marcados de outro jeito no sistema."

Vídeo: uma linha no slide de recuperação, com o par P09 antes/depois (0,6 → 1,0).
