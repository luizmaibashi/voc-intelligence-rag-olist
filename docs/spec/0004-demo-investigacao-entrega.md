# Spec 0004 — Demo de investigação da experiência de entrega

**Data:** 2026-10-06. **Dono:** Luiz Maibashi.
**Status:** narrativa aprovada; entrada local/ensaio sintético implementados em
07/10. Execução e validação com busca real e gerador seguem pendentes.

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

## Entrada local mínima — contrato 2026-10-07

Luiz confirmou escopo e previu que testes e demo local funcionariam. Objetivo:
permitir reprodução e conferência de busca/fontes/contagem antes de API. Dono
da aprovação da demo e de publicação: Luiz; gate de geração segue bloqueado.

- Arquivos: requirements.txt (statsmodels usado pela EDA), src/demo.py,
  tests/test_demo.py, tests/test_eda.py, esta spec, README.md inicial,
  reports/demo_local_20261007.md e somente frente TC4/linha no Bridge.
- CLI `python -m src.demo`: ações `buscar`, `contar`, `ensaio-sintetico`.
  `buscar` exige pergunta, usa MiniLM local, índice DuckDB em memória e corpus
  completo. Conserva filtros antes da deduplicação e exibe IDs/textos/score,
  filtros efetivos e modo local. Não gera resposta nem envia comentários.
- Encoder carregado offline, sem baixar pesos automaticamente. Sem uso do
  cache antigo de pooling, cujo manifesto não está presente nesta máquina;
  vetores da busca gerados em memória, sem modificar arquivos históricos.
  Custo da primeira execução deve ser descrito, sem prometer latência medida.
- `contar` chama contar_atrasos no corpus completo independentemente de top-k;
  exibe população, denominador/período/IC e viés de quem comenta.
- `ensaio-sintetico` usa somente três avaliações inventadas, encoder MiniLM
  local e gerador falso identificado. Mostra busca, resposta citada, fontes,
  contagem e recusa P15. Respostas fixas só nesse ensaio; não avaliamos LLM.
- Entrada malformada/filtro inválido/arquivo ou modelo ausente falha visivelmente
  com código de saída não zero. Nada lê credencial ou cria cliente Gemini.
- Testes com encoder/gerador falsos: filtros, texto repetido com metadado
  diferente, fontes correspondentes, contagem independente, erros, ausência
  de rede e proteção de saídas. Reproduzir importação EDA sem executar main
  nem sobrescrever reports/eda_olist.md. Smoke local sintético com MiniLM real.
- Modelo, payloads E01–E20, políticas de tentativas, P09, gabarito/pool e corpus
  preservados. Sem publicação, upgrade Torch ou API nesta etapa. Busca real
  poderá servir à curadoria; qualquer geração futura requer liberação dos
  textos efetivamente recuperados e previsão, em contrato próprio.

## Referências da narrativa

Entrada local implementada em 07/10 após escopo confirmado. Statsmodels0.14.6
declarado/instalado; importação EDA corrigida sem executar main. Suíte final:
243 testes passaram; ensaio sintético com MiniLM real offline concluiu busca,
fontes, contagem e recusa simulada. Não mede Gemini ou retrieval real do corpus.
Evidências e limites: `../../reports/demo_local_20261007.md`. README inicial
documenta comandos. Gate da demo real permanece bloqueado por E05.

- `0001-resposta-com-evidencias.md`: resposta, citações e recusa.
- `0002-frequencia-atrasos.md`: população elegível e contrato da contagem.
- `../../data/eval/perguntas.csv`: P01 e P15–P18.
- `../adr/0001-corpus-limpeza-minima-sem-chunking.md`: unidade de análise.
