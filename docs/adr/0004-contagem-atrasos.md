# ADR-0004: Contar atraso no corpus elegível inteiro

**Data:** 2026-09-28. **Status:** Accepted para a primeira pergunta de frequência.
**Proposto por:** Luiz Maibashi.

## Contexto e decisão

O RAG recupera top-k para citar experiências, mas top-k não estima quantas
avaliações relatam um tema. Para a primeira demonstração quantitativa, usar o
metadado `situacao_entrega` no corpus processado: uma linha por `review_id`
com comentário. Contar atrasadas entre as avaliações de pedidos entregues e
exibir numerador, denominador, período de compra e IC95% de Wilson.

O ganho é uma resposta auditável e sem custo de API, útil ao vídeo da FIAP e à
habilidade de definir unidade, população e denominador. Implementação em
`src/analytics/frequencia.py`, sem alterar a busca ou o gerador.

## Alternativas e limites

| Caminho | Decisão |
|---|---|
| Contar resultados top-10 do RAG | Rejeitado: seleção por similaridade não representa o corpus. |
| Contar `freq_texto` | Rejeitado: mede frases idênticas, não entregas atrasadas. |
| Classificar motivos no texto | Adiado: exige taxonomia e avaliação dos rótulos antes de estimar frequência. |

O denominador exclui avaliações sem comentário e pedidos não entregues.
Portanto, o resultado não é taxa de atraso de todos os pedidos. O metadado
depende da estimativa e da data efetiva de entrega; mudanças em sua definição
exigem revalidar esta contagem.

## Falsificação

`contar_atrasos` deve bater com a contagem independente do Pandas no mesmo
corpus. Qualquer saída que omita denominador ou período, ou trate pedidos não
entregues como entregas no prazo, invalida esta via de frequência.
