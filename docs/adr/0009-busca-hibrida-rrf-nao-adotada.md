# ADR 0009: Busca híbrida por RRF medida e não adotada

**Status:** aceita · **Data:** 2026-10-23 · **Relaciona:** ADR 0002 (item 5), spec 0014

## Contexto

A ADR 0002 deixou a busca híbrida com TF-IDF "como candidata, a medir no mesmo gabarito antes
de adotar", porque MiniLM e TF-IDF erram em perguntas diferentes (P13, P09). A spec 0014 fixou
antes da medição: RRF com `k = 60`, profundidade 100, julgamento cego dos inéditos e um
critério de adoção com quatro itens.

## Decisão

A busca do produto continua só densa (MiniLM + DuckDB). A híbrida não passa em três dos quatro
itens: P@10 0,71 → 0,64, MRR 0,79 → 0,77 e P03 perde 0,5 (n = 14; detalhe em
`reports/ganho_hibrida_20261023.md`). O veredito se mantém mesmo no melhor caso de julgamento.

## Por quê

O RRF com `k = 60` premia o consenso entre as listas. Aqui o consenso é o vocabulário genérico
("cliente", "entrega", "recebimento"), e o acerto exclusivo de cada busca (o elogio que só a
densa acha em P09, a "taxa" que só o TF-IDF acha em P13) fica abaixo dele. Complementaridade
sozinha não basta para a fusão por posição ajudar.

## Alternativas consideradas

| Alternativa | Situação |
|---|---|
| RRF com `k` menor ou pesos por busca | Não testada: escolher o `k` olhando estas 14 perguntas seria ajustar ao gabarito |
| Roteamento (TF-IDF só quando a pergunta tem termo raro) | Hipótese pós-medição; exige perguntas novas |
| BM25 em vez de TF-IDF | Não testado; traria documentos sem julgamento |
| Reranker sobre a densa | Pós-entrega; reordena sem depender de consenso |

## Consequências

- Nenhuma mudança nos arquivos do hash; as liberações da spec 0012 seguem válidas.
- A frase "híbrida é o próximo passo" sai do discurso: o próximo passo é testar uma variante
  com perguntas separadas, ou um reranker.
- A remedição deu a P@10 da busca do produto nas 14 perguntas: 0,71 [0,55; 0,86].
