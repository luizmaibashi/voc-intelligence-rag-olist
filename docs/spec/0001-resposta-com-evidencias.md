# Spec 0001 — Resposta fundamentada e recusa

**Status:** rascunho para implementação. **Dono da aprovação:** Luiz Maibashi.

## Objetivo

Responder perguntas sobre avaliações da Olist citando `review_id` verificáveis e
recusar pedidos cujo fato não esteja nos comentários. O enunciado exige os dois
comportamentos (páginas 7–8). Um score alto de embedding, sozinho, não prova que
o comentário contém a resposta: nas 14 perguntas com relevante no pool o top-1
variou de 0,635 a 0,813; em quatro perguntas sem resposta, de 0,603 a 0,778.

## Escopo da próxima implementação

- Receber pergunta e avaliações recuperadas com `review_id`, texto e metadados.
- Ligar embedding da pergunta, busca exata DuckDB e geração numa função testável;
  filtros de nota e entrega são aplicados antes de construir o contexto.
- Produzir resposta estruturada: status `respondida`, `sem_evidencia` ou
  `erro_geracao`, texto, IDs das avaliações usadas e motivo quando houver.
- Exigir que a resposta use apenas fatos presentes nas avaliações fornecidas.
- Validar mecanicamente que cada ID citado pertence ao contexto recuperado.
- Tratar falha da API, resposta vazia, saída malformada e citação inventada como
  `erro_geracao` visível. Reservar `sem_evidencia` para falta de suporte factual.
- O adaptador externo exige marcação explícita de contexto revisado antes de
  enviar avaliações à API; a marcação é responsabilidade do chamador.
- Testar P15–P18 como negativas e perguntas positivas específicas do gabarito.

Fora desta peça: perguntas de frequência sobre o corpus inteiro. Elas exigem
contagem por tema; top-k não estima frequência. A integração com esse caminho
será especificada separadamente.

## Critérios de aceitação

1. P15–P18 não recebem prazo, percentual ou valor inventado; o sistema explica
   a falta de evidência.
2. Pergunta respondível recebe ao menos um `review_id` presente no contexto.
3. ID inventado e resposta malformada retornam `erro_geracao`; contexto vazio
   retorna `sem_evidencia`. Nenhum desses casos vira resposta afirmativa.
4. O teste usa exemplos com comentário tematicamente semelhante que não contém
   o fato solicitado, além de exemplos com resposta explícita.
5. Registrar acertos e erros com `n`; com 18 perguntas, os resultados são
   exploratórios e não sustentam afirmação geral de confiabilidade.

## Riscos e decisões pendentes

- A escolha do modelo de linguagem e do provedor depende de custo, acesso e
  execução local. A interface de geração deve permitir substituição sem mudar
  as regras de validação.
- Citação válida não garante que a frase citada sustenta a afirmação. A revisão
  humana de exemplos e um teste adversarial de suficiência são necessários.
- As quatro negativas têm rótulo por limite do corpus, mas o conjunto ainda é
  pequeno. Evitar calibrar um limiar definitivo com ele.
