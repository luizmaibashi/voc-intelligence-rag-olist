# Spec 0004 — Demo de investigação da experiência de entrega

**Data:** 2026-10-06. **Dono:** Luiz Maibashi.
**Status:** narrativa aprovada pelo Luiz; execução e validação pendentes.

## Objetivo de negócio

Ajudar o gestor de atendimento a entender relatos sobre entregas atrasadas,
conferir as evidências e escolher problemas para investigar com a operação.
Não há ganho financeiro ou economia de tempo medidos; a demo demonstra utilidade.

## Roteiro e critérios de aceitação

1. **Entender:** perguntar “O que os clientes relatam sobre entregas atrasadas?”.
   Recuperar comentários e gerar resposta limitada às evidências disponíveis.
   Declarar os filtros efetivamente aplicados; atraso é a situação derivada das
   datas, não apenas a presença da palavra “atraso” no comentário.
2. **Conferir:** abrir as avaliações citadas, exibindo `review_id` e texto.
   Cada ID pertence ao contexto recuperado e cada afirmação deve ser sustentada
   pelo texto. A conferência humana complementa a validação mecânica de IDs.
3. **Quantificar:** consultar “Qual a proporção de avaliações com comentário
   associadas a pedidos entregues que chegaram atrasados?”. Usar a contagem
   prevista na spec 0002, exibindo numerador, denominador, período e IC95%.
   A contagem independe dos resultados top-k e não estima frequência de temas.
4. **Mostrar o limite:** perguntar P15, “Qual é o prazo oficial de reembolso
   da Olist quando uma entrega atrasa?”. Esperar `sem_evidencia`, com explicação
   de que relatos de clientes não estabelecem política oficial. Similaridade
   temática não autoriza inventar prazo. Falha do provedor aparece como
   `erro_geracao`, sem ser apresentada como recusa por falta de evidência.

## Limites da apresentação

- Dados históricos e avaliações com comentário: sem extrapolação para todos
  os clientes, todos os pedidos ou a operação atual da Olist.
- Relatos permitem levantar problemas para investigação; não comprovam causa.
- IC95% não corrige o viés de autosseleção de quem comenta.
- Ranking completo P09 permanece congelado. Classificadores e tópicos da
  trilha paralela NLP não são dependências desta demo.
- Formato da interface ainda não decidido; preservar execução reproduzível e
  fontes acessíveis. Não prometer filtros de categoria/período antes de implementá-los.

## Evidência necessária antes de apresentar

Registrar perguntas, configuração, filtros, respostas reais, IDs recuperados e
checagem humana de suporte/recusa em relatório de avaliação. Distinguir falha de
recuperação, geração, citação e recusa. Exemplos ensaiados demonstram o fluxo;
não constituem avaliação independente da confiabilidade geral.

## Dependências e próximo passo

Conferir e reproduzir os achados da auditoria sobre deduplicação antes dos filtros
e identidade do cache; depois liberar geração real conforme revisão dos textos e
condições do provedor. Não enviar comentários reais sem a revisão exigida pelo
AGENTS.md. Planejar implementação em etapa própria, com escopo de arquivos explícito.

## Referências

- `0001-resposta-com-evidencias.md`: resposta, citações e recusa.
- `0002-frequencia-atrasos.md`: população elegível e contrato da contagem.
- `../../data/eval/perguntas.csv`: P01 e P15–P18.
- `../adr/0001-corpus-limpeza-minima-sem-chunking.md`: unidade de análise.
