# Spec 0011 — Filtros opcionais de categoria e período de compra

**Data:** 2026-10-23. **Status:** implementada localmente, pendente revisão de Luiz
antes de commit/publicação; contrato escrito antes do código.
**Dono da decisão de publicação/merge:** Luiz Maibashi.

## Objetivo e valor

Permitir que o gestor delimite uma investigação por categoria de produto e
período de compra, duas dimensões citadas no desafio adicional do enunciado
(p. 8–9). O filtro reduz evidências fora do recorte antes do ranking vetorial.

## Escopo

- Adicionar `--categoria`, `--compra-de` e `--compra-ate` às ações `buscar` e
  `responder`. Os limites de data são inclusivos, em `AAAA-MM-DD` e sobre
  `data_compra`, nunca `data_avaliacao`.
- Categoria corresponde a um token completo da coluna `categorias` separada
  por `|`; `moveis` não casa com `moveis_escritorio`. Um pedido com várias
  categorias pertence a cada uma delas.
- Filtros são opcionais, escolhidos pelo usuário. Sem eles, a busca histórica
  preserva ordem e resultados. Zero candidatos resulta em recusa local, sem API.
- A prévia mostra filtros efetivos; seu hash muda quando pergunta, filtros ou
  evidências mudam. Não alterar corpus, embeddings, prompt, gabarito ou capturas.

## Aceitação e riscos

1. Teste local prova categoria exata, pedido multicategoria, início e fim
   inclusivos, interseção de filtros e recusa sem candidato.
2. Entrada inválida (`AAAA-MM-DD` impossível, início após fim, categoria vazia
   ou com delimitador) falha visivelmente antes de gerar.
3. Comparação sem filtros confirma a mesma ordem de fontes dos fixtures
   anteriores. Testes não chamam API.
4. A avaliação histórica 20/20 vale apenas para a configuração julgada; os
   recortes novos precisam de avaliação própria antes de qualquer alegação de
   qualidade, e de revisão de contexto antes de envio externo.

O trabalho altera `src/retrieval/indice.py`, `src/demo.py`,
`src/rag/responder.py`, os testes correspondentes e `README.md`. O usuário
aprovou esse escopo na conversa em 2026-10-23.

## Verificação local em 2026-10-23

- Suíte completa antes da correção de compatibilidade: **340 testes passaram**.
- Após revisão independente do Luna, busca sem filtro voltou a aceitar corpus
  sem `data_compra`; um índice sem datas recusa filtro temporal visivelmente.
  A bateria final focada passou com **74 testes**. Nenhum teste chamou o Gemini.
- Revisão do diff identificou e corrigiu a exigência indevida de `data_compra`
  para busca histórica sem filtro. Ganho de qualidade de recuperação com os
  filtros novos **não foi medido**; o relatório existente mede só nota/situação.
- As prévias E-A, E-B e P15 foram regeneradas sem API. IDs, ordem e textos
  coincidiram com a liberação de 21/10 pela reconstrução dos três hashes
  históricos. Os hashes novos estão em
  [`reports/previas_demo_0011_20261023.md`](../../reports/previas_demo_0011_20261023.md)
  e ainda dependem de liberação de Luiz antes de qualquer envio.
