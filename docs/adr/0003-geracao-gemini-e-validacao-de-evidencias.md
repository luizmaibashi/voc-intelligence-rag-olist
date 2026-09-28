# ADR-0003: Geração Gemini com contrato de evidências

**Data:** 2026-09-28
**Status:** Accepted para protótipo; uso com avaliações reais depende de revisão de PII
**Contexto:** RAG de avaliações Olist, Tech Challenge Fase 4

## Contexto

O enunciado exige resposta gerada por modelo de linguagem, ligada a avaliações
identificáveis, e recusa quando falta evidência. A busca MiniLM/DuckDB já foi
validada contra NumPy nas 14 perguntas do gabarito. O score top-1 das quatro
perguntas sem resposta (0,603–0,778) se sobrepõe ao das positivas
(0,635–0,813); um limiar único não resolve suficiência factual.

## Decisão

Usar `gemini-3.5-flash-lite` como gerador inicial, atrás da interface de
`src/rag/responder.py`. O adaptador pede saída estruturada com `status`, `texto`
e `review_ids`. O núcleo valida estado, texto e IDs contra o contexto. Falhas da
API, saída malformada e citação inexistente usam `erro_geracao`; ausência real
de evidência usa `sem_evidencia`. Comentários são dados não confiáveis;
instrução do sistema manda ignorar comandos neles e citar somente fatos
diretamente sustentados.

O modelo foi escolhido pelo custo de experimento e facilidade de substituição,
não por qualidade já demonstrada. Em 2026-09-28, o preço padrão publicado para
Gemini 3.5 Flash-Lite era US$ 0,30 por milhão de tokens de entrada e US$ 2,50
por milhão de saída: https://ai.google.dev/gemini-api/docs/pricing. A API
estruturada do SDK está documentada em
https://ai.google.dev/gemini-api/docs/generate-content/structured-output.

**Estado da integração em 2026-09-28:** `gemini-2.5-flash-lite` devolveu 404
para esta conta (acesso limitado a usuários antigos). `gemini-3.5-flash-lite`
devolveu 503 por alta demanda tanto em Generate Content quanto em Interactions
API; `gemini-3.1-flash-lite` também devolveu 503. A Interactions API foi testada
em `.venv` com `google-genai` 2.25.0, sem alterar Python global. Nenhum dos
dois casos sintéticos recebeu resposta de conteúdo; qualidade ainda não medida.
Disponibilidade atual dos modelos: https://ai.google.dev/gemini-api/docs/models.

## Consequências e riscos

- Custo e latência por pergunta passam a depender da API. Falha de geração
  produz erro visível sem expor detalhes da exceção nem contaminar a métrica de recusa.
- Um ID válido **não prova** que a afirmação está sustentada pelo comentário.
  P15–P18 e exemplos adversariais precisam de revisão de conteúdo, não só testes
  estruturais. Não alegar taxa de acerto sem `n` e incerteza.
- A documentação de preços distingue nível gratuito e pago e informa política
  diferente de uso dos dados. Não enviar avaliações reais à API antes de revisar
  PII e o nível de serviço; o adaptador exige `contexto_revisado=True` para
  habilitar o envio. Testes iniciais usam textos sintéticos.
- Perguntas de frequência exigem contagem sobre o corpus inteiro. O gerador
  recebe o resultado da contagem em etapa própria; top-k não estima frequência.

## Alternativas

| Opção | Resultado |
|---|---|
| Corte por cosseno | Rejeitado: scores positivos e negativos se sobrepõem. |
| Modelo local | Evita envio externo; maior custo de instalação e inferência para a entrega individual. Pode substituir o adaptador. |
| Gemini 3.5 Flash-Lite | Escolhido para protótipo pelo custo baixo; qualidade ainda depende da avaliação. |

## Falsificação

Se o modelo inventar prazo oficial em P15/P17, agregado em P16/P18, ou afirmar
algo que a avaliação citada não diz, a estratégia falhou mesmo que o JSON e o
ID sejam válidos. Reavaliar prompt, modelo ou verificador antes de expor o RAG.
