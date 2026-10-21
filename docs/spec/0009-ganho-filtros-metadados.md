# Spec 0009 — Ganho dos filtros de metadados na recuperação

**Data:** 2026-10-21. **Status:** aprovada por Luiz em 2026-10-21; aguardando previsão (seção 4) antes de medir.
**Dono da aprovação:** Luiz Maibashi. **Prazo da entrega:** 2026-10-31.

## Pergunta de negócio

O desafio adicional (enunciado, p. 9) pede justificar como os metadados contribuem
para a qualidade da recuperação. O ADR-0002 §5 prometeu uma métrica, "Precisão@10
do MiniLM com filtro maior que sem filtro em P09 e P10", que nunca foi medida.
Esta spec decide se vale medir, como medir e o que se pode afirmar com o resultado.

Motivo técnico: o MiniLM dá cosseno 0,76 entre "entrega rápida" e "entrega lenta",
ou seja, não separa elogio de reclamação. O filtro de nota é a correção proposta.

## O que já se sabe (linha de base, sem filtro)

MiniLM no gabarito atual: P@10 0,72 [0,55; 0,87], MRR 0,79, n = 14, IC por
bootstrap sobre as perguntas. Por pergunta (`metricas.avaliar` sobre `pool_origem.csv`):

| P01 | P02 | P03 | P04 | P05 | P06 | P07 | P08 | P09 | P10 | P11 | P12 | P13 | P14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1,0 | 0,4 | 0,9 | 1,0 | 0,9 | 1,0 | 0,6 | 0,7 | 0,7 | 1,0 | 1,0 | 0,6 | 0,3 | 0,0 |

**Efeito teto.** P10 já está em 1,0 sem filtro: a métrica do ADR-0002 ("maior que
sem filtro em P09 e P10") é impossível de cumprir em P10. A métrica foi mal
formulada; esta spec a substitui (ver regra de decisão).

**Efeito máximo no número global.** Mesmo que o filtro leve P02 e P09 a 1,0
(+0,6 e +0,3), a média das 14 sobe no máximo (0,6 + 0,3) / 14 ≈ 0,06, de 0,72
para cerca de 0,79, dentro do IC atual. O ganho dos filtros nunca vai aparecer
no número global; ele só pode ser mostrado pergunta a pergunta.

## 1. Perguntas com filtro aplicável (congelado antes de rodar)

**Regra de aplicabilidade:** filtro só entra quando o texto da pergunta nomeia a
polaridade (elogio, satisfação, nota ruim) ou a situação da entrega (atraso, não
chegou). Assim o filtro é o que um gestor escolheria lendo a pergunta, não um
ajuste feito depois de ver o resultado. No CLI o filtro é escolhido pelo usuário
(`--nota-min`, `--nota-max`, `--situacao-entrega`); a medição avalia "gestor que
escolhe o filtro óbvio", não inferência automática de filtro.

| Pergunta | Dimensão nomeada | Filtro primário | P@10 sem filtro | Papel |
|---|---|---|---|---|
| P01 — reclamações sobre atraso | entrega | `situacao_entrega = 'atrasado'` | 1,0 | não-regressão |
| P02 — pedido nunca chega | entrega | `situacao_entrega = 'nao_entregue'` | 0,4 | ganho possível |
| P09 — o que mais elogiam na entrega | polaridade | `nota >= 4` | 0,7 | ganho possível |
| P10 — clientes satisfeitos com o produto | polaridade | `nota >= 4` | 1,0 | não-regressão |
| P11 — maior ponto das notas ruins | polaridade | `nota <= 2` | 1,0 | não-regressão |

**Fora, com motivo:**
- P08 nomeia a nota, mas a nota é a resposta pedida ("como é a nota..."). Filtrar
  por nota responderia a pergunta por construção.
- P03 a P07 descrevem problemas, mas não nomeiam nota nem situação de entrega.
  Aplicar `nota <= 2` nelas seria palpite do agente sobre a intenção do gestor.
- P12 a P14 são candidatas a sem resposta; filtro não muda isso.
- P15 a P18 (sem resposta) ficam fora do pooling por desenho.

**Variantes exploratórias** (rodadas e relatadas, sem peso na decisão):
P09 com `situacao_entrega = 'no_prazo'`; P01 com `nota <= 2`. Custam julgamento
extra; ver seção 5. Luiz decide se entram.

Notas de corte: Olist usa 1 a 5; 4 e 5 são satisfação, 1 e 2 insatisfação, 3 neutro
e fica fora dos dois lados.

## 2. O problema do pool

O gabarito só tem as avaliações que MiniLM, E5 ou TF-IDF trouxeram **sem filtro**.
O top-10 filtrado puxa avaliações mais abaixo no ranking, que ninguém julgou.

**Contagem (feita em 2026-10-21, busca local, sem olhar relevância):**

Script descartável no scratchpad do agente: `buscar` do produto sobre o corpus
completo (42.174 avaliações), vetores MiniLM gerados localmente, inéditas contadas
por texto em minúsculas contra `julgamento.csv` da mesma pergunta.

Conferência do braço sem filtro: as 14 perguntas reproduzem o top-10 julgado do
MiniLM (0 inéditas por texto; `review_id` igual em 139 de 140 posições, a diferença
em P11 é texto repetido com outro representante).

| Pergunta | Filtro | Inéditas no top-10 |
|---|---|---|
| P01 | `situacao_entrega = 'atrasado'` | 4 |
| P02 | `situacao_entrega = 'nao_entregue'` | 6 |
| P09 | `nota >= 4` | 4 |
| P10 | `nota >= 4` | 0 |
| P11 | `nota <= 2` | 2 |
| **Primário** | | **16** |
| P09 (exploratória) | `situacao_entrega = 'no_prazo'` | 2 |
| P01 (exploratória) | `nota <= 2` | 2 |

P10 com filtro cai inteiro em avaliações já julgadas: mede sem julgamento novo.

**Como o Luiz julga às cegas:**
1. Planilha nova `data/eval/julgamento_filtros.csv`, mesmo formato de
   `julgamento.csv` (pergunta, texto, nota, `freq_texto`, coluna `relevante`).
   Não mostra qual busca trouxe a avaliação nem se veio do braço com filtro.
2. Junto das inéditas entram 2 avaliações já julgadas por pergunta (âncoras, 10 no
   total), embaralhadas. Se o Luiz discordar de si mesmo em mais de 2 das 10, o
   critério mudou desde setembro e o resultado sai com essa ressalva.
3. Mesmo critério do julgamento original; P09 segue a definição de elogio à
   entrega do `AGENTS.md` (texto misto preserva o elogio).
4. A nota fica visível, como no julgamento original, para manter o critério
   comparável. Risco: no braço filtrado toda nota é 4 ou 5 em P09; com nota à vista,
   o Luiz pode tender a marcar elogio. As âncoras ajudam a detectar, não eliminam.

**Chave de junção:** texto em minúsculas por pergunta, não `review_id`. A busca do
produto filtra antes de agrupar textos iguais (spec 0005), então o representante
de um texto repetido pode ter `review_id` diferente do que foi julgado.

## 3. Comparação pareada

- **Mesma função nos dois braços:** `src.retrieval.indice.buscar`, com e sem filtro,
  sobre o corpus completo. Primeiro confirmar que o braço sem filtro reproduz o
  top-10 julgado do MiniLM (comparação por texto); divergência é relatada antes de
  qualquer número.
- **Métrica:** P@10 por pergunta, diferença pareada (com filtro − sem filtro).
- **Relato:** tabela das 5 perguntas com os dois valores e a diferença. Média das
  diferenças com IC por bootstrap (`ic_diferenca_pareada`) entra só como descrição.

**Limite dito antes de rodar.** Com n = 5 perguntas, e só 2 com espaço para subir,
o bootstrap tem poucas reamostras distintas e o IC não sustenta afirmação de
superioridade. Nem um P@10 global de 0,85 provaria nada sobre 0,72. O que a
medição pode mostrar é o mecanismo, por pergunta: "em P09, sem filtro, k das 10
avaliações eram reclamação; com filtro, j". Isso é evidência de caso, não estatística.

**O que P@10 não vê.** O filtro tira do alcance relevantes fora do recorte (ex.:
reclamação de atraso em pedido marcado "no prazo"). P@10 não penaliza essa perda.
A revocação relativa ao pool conhecido entra como segunda coluna, com a ressalva de
que o pool foi montado sem filtro.

## 4. Regra de decisão (escrita antes da medição)

Por pergunta: **ganho** se Δ ≥ +0,2 (2 avaliações a mais); **neutro** se
|Δ| ≤ 0,1; **perda** se Δ ≤ −0,2.

| Desfecho | Condição | Leitura |
|---|---|---|
| A — filtro ajuda | ganho em P02 ou P09, nenhuma perda nas 5 | filtro corrige o que o embedding não separa, sem custo nas demais |
| B — filtro neutro | nenhum ganho, nenhuma perda | filtro não muda precisão no gabarito; vale como recorte de população |
| C — filtro atrapalha | perda em alguma das 5 | filtro primário errado para aquela pergunta; não recomendar como padrão |

Desfecho misto (ganho em uma, perda em outra) conta como C para o README: o
resultado não autoriza recomendar filtro como padrão.

**Previsão do Luiz (preencher antes de rodar):**

| | P01 | P02 | P09 | P10 | P11 | Desfecho (A/B/C) |
|---|---|---|---|---|---|---|
| P@10 com filtro previsto | 1,0 | 0,7 | 1,0 | 1,0 | 1,0 | A |

Registrada por Luiz em 2026-10-21 10:57 (-03), antes de abrir o anexo e de
qualquer julgamento novo. Desfecho deduzido pela regra: ganho previsto em P02
(+0,3) e P09 (+0,3), teto mantido nas demais. A primeira formulação ("melhora em
todos") foi trocada por números porque P01, P10 e P11 já estão em 1,0.

A medição só roda com esta tabela preenchida e commitada.

## 5. Custo e saída em cada desfecho

**Custo estimado**
- Julgamento: 16 inéditas (primário) + 10 âncoras = 26; com as exploratórias, até 30. A ~20 s por avaliação, 10 a 15 min do Luiz.
- Código: script de avaliação em `src/eval/` (reusa `buscar` e `metricas`) e um teste
  sintético da junção por texto: 1,5 a 2 h.
- Rodar, conferir e escrever relatório em `reports/`: 1 h.
- Atualizar ADR-0002 §5 com a métrica nova e o resultado: 30 min.
- Total: cerca de 4 h (meio dia), dentro do orçamento de 1 a 2 dias. Sem Gemini, sem envio externo.

**README e vídeo**

| Desfecho | README (seção de recuperação) | Vídeo (≤ 7 min) |
|---|---|---|
| A | tabela das 5 perguntas; frase "o filtro de nota corrige polaridade que o embedding não separa (cosseno 0,76), n = 5, sem significância" | uma linha no slide de recuperação, com o par P09 antes/depois |
| B | "filtros não mudaram a precisão nas 5 perguntas aplicáveis; servem para restringir a população (ex.: só atrasados), não para ranquear melhor" | nada novo; manter o que está |
| C | relatar a perda por pergunta e o motivo; filtro fica opcional no CLI | nada novo |

Em todos: ADR-0002 §5 passa a citar a métrica desta spec e o resultado; a promessa
antiga (P09 e P10) fica registrada como mal formulada por efeito teto.

**Se não medir:** o README não pode afirmar que os filtros melhoram a recuperação,
só que existem e como funcionam. A justificativa pedida no enunciado fica no
argumento do cosseno 0,76, sem número de recuperação.

## Anexo — abrir só depois de registrar a previsão

Distribuição de metadados dos relevantes já julgados, feita pelo agente depois de
congelar os filtros da seção 1. Antecipa parte do resultado; ler antes da previsão
contamina a previsão.

Relevantes e não relevantes já julgados (pool sem filtro) dentro do recorte de cada filtro:

| Pergunta | Filtro | Relevantes dentro / total | Não relevantes dentro / total |
|---|---|---|---|
| P01 | `atrasado` | 17 / 30 | 0 / 0 |
| P02 | `nao_entregue` | 4 / 14 | 3 / 15 |
| P09 | `nota >= 4` | 23 / 24 | 0 / 6 |
| P10 | `nota >= 4` | 23 / 23 | 0 / 4 |
| P11 | `nota <= 2` | 15 / 19 | 0 / 9 |

Leitura: o filtro de nota em P09 tira do recorte os 6 não relevantes conhecidos, que
são todos nota 1 ou 2. Em P02, 10 dos 14 relatos relevantes de pedido que não chegou
estão em pedidos marcados atrasado ou no prazo: a situação `nao_entregue` cobre mal
o que o cliente chama de "nunca chegou". Em P01, 13 das 30 reclamações de atraso
estão fora do filtro `atrasado` (7 no prazo, 6 não entregue): custo de revocação.
