# Voice of Customer Intelligence com RAG

Projeto do Tech Challenge Fase 4 da FIAP. A proposta é ajudar um gestor de
atendimento a investigar relatos sobre entregas, conferir os comentários que
sustentam uma resposta e consultar uma contagem de atrasos com população definida.

O núcleo usa MiniLM multilíngue para embeddings, DuckDB para busca exata e
Gemini 3.1 Flash-Lite para geração com contexto revisado. O CLI oferece busca,
fontes, contagem e resposta gerada com citações; cada envio ao Gemini exige
prévia do contexto e liberação por hash ([spec 0007](docs/spec/0007-cli-resposta-gerada.md)).

O código está em [`src/`](src/) e os testes em [`tests/`](tests/).
`src/preprocessing/` prepara a base; `src/retrieval/` recupera avaliações;
`src/rag/` monta e valida a resposta; `src/demo.py` reúne as ações do CLI.

## Instalação

Python 3.13, PowerShell, comandos executados na raiz do projeto:

```powershell
py -3.13 -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements.txt
& .venv/Scripts/python.exe -m pip check
```

Os pacotes principais, inclusive google-genai 1.75.0, têm versões fixadas.
As dependências transitivas ainda não formam um lock completo. O lote de avaliação
e o envio de P15 em 21/10 usaram 1.75.0; os envios de E-A e E-B em 17/10 usaram
1.73.1. A partir de agora, a demo usa 1.75.0. Outra versão muda o hash da prévia.
Statsmodels 0.14.6 é declarado porque o script da EDA usa o intervalo de Wilson.

## Pesos do modelo

A entrada local carrega `paraphrase-multilingual-MiniLM-L12-v2` com
`local_files_only=True`. Não baixa pesos automaticamente. Se o modelo ainda
não estiver no cache, prepare-o com conexão antes de executar a demo:

```powershell
& .venv/Scripts/python.exe -X utf8 -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")'
```

Esse comando baixa o modelo; não envia comentários da Olist. Nome do modelo
não fixa uma revisão dos pesos remotos. O cache local em 20/10/2026 apontava
para `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, também registrada em
[relatório de integridade do cache](reports/integridade_busca_cache.md). Não há registro que
comprove essa revisão nas capturas de geração.

## Ensaio sintético local

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao ensaio-sintetico
```

Usa três comentários inventados, embeddings MiniLM, DuckDB e um gerador falso.
Mostra pergunta, filtros, fontes, resposta simulada com citações, contagem e
recusa de política oficial. A saída identifica a simulação. Esse ensaio verifica
a integração local; não avalia factualidade ou disponibilidade do Gemini.

## Corpus histórico local

Fonte: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(versão da página de 2021-10-01). Baixe e extraia os nove CSVs em `data/raw/`:

```powershell
curl.exe -L -o olist.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
(Get-FileHash olist.zip -Algorithm SHA256).Hash   # esperado: 967E41E04FC306FE604E2A693F488995A8B41E5047418F8A5C8E4ABD6DECA784
Expand-Archive olist.zip -DestinationPath data/raw
& .venv/Scripts/python.exe -X utf8 -m src.preprocessing.corpus
```

Conferência da reprodução (2026-10-17, máquina limpa): 42.174 documentos,
36.453 textos distintos, 4.339 atrasadas em n = 40.303 entregues
(10,77%; IC95% de Wilson [10,47%; 11,07%]) e 372/372 textos
do gabarito julgado idênticos. Hash diferente do zip indica outra versão da
base: trate como nova configuração. Detalhe em
[reports/demo_cli_20261017.md](reports/demo_cli_20261017.md).

Título e mensagem formam um documento por avaliação. A limpeza conserva
negação, acento e comentários curtos; elimina texto vazio e ausência mascarada.
Categoria ausente recebe `sem_categoria`; avaliações sem comentário ficam fora
do corpus elegível. Metadados de nota, entrega e categoria são preservados. Decisão completa na
[ADR 0001](docs/adr/0001-corpus-limpeza-minima-sem-chunking.md).

Esse comando gera `data/processed/corpus_reviews.parquet`; use em uma instalação
nova. Não regenere o corpus julgado sem tratar a mudança como nova configuração.
CSV bruto, corpus processado, PDF do enunciado e credenciais ficam fora do Git.

### Busca e conferência de fontes

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao buscar --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10
```

Exibe candidatos com ID, texto, nota, situação, score e filtros efetivamente
aplicados. Não gera resumo, não consulta API e não estima frequência de temas.
Os textos exibidos são para revisão local; não publique ou envie novos textos
sem revisar dados pessoais e autorização do contexto.

O índice é criado em memória. Os vetores do corpus completo são calculados nessa
execução, sem reutilizar ou substituir o cache histórico do pooling. A primeira
busca pode demorar; esta versão prioriza integridade e reprodução. Não foi
validada uma promessa de latência para a entrada completa.

A pergunta é convertida diretamente em embedding, sem reescrita: ainda não há
medição de ganho que justifique outra etapa, com custo, latência e possibilidade
de alterar o sentido da consulta. Os filtros e o top-k selecionam candidatos;
o texto integral e os IDs compõem o contexto revisado antes da geração.

### Resposta gerada com evidências

Dois passos por pergunta ([spec 0007](docs/spec/0007-cli-resposta-gerada.md)):

```powershell
# 1. Prévia: busca real, contexto exato, alerta de PII e hash. Não chama API.
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao responder --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10
# 2. Envio: após ler o contexto, repetir com o hash impresso.
$hash = 'cole-aqui-o-hash-impresso-na-previa'
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao responder --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10 --executar --aprovacao-sha256 $hash
```

O envio é bloqueado (código 3, sem API) se o hash não bater: qualquer mudança
em pergunta, filtros, contexto recuperado, configuração ou código exige nova
prévia. O alerta de PII é heurístico (e-mail, telefone, CPF/CNPJ, CEP) e não
substitui a leitura. Teto de 20 chamadas Gemini por dia UTC nesta máquina,
contado em `data/demo/execucoes.jsonl` (fora do Git), com cabeçalho gravado
antes da chamada. A saída traz status, texto, `review_id` citados e o texto
integral de cada fonte citada. Sem credencial, `--gerador falso` roda o mesmo
fluxo com resposta simulada e identificada. Frequência continua em `--acao contar`.

### Reprodução sem credencial e reprodução de capturas

Após instalar as dependências e preparar o corpus, rode a prévia e o gerador
falso com os mesmos filtros. O segundo comando não lê chave nem consome cota;
a resposta é simulada e não demonstra suporte factual do Gemini.

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao responder --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao responder --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10 --gerador falso
```

A prévia imprime contexto e SHA-256 do payload. Esse hash muda se mudarem
pergunta, filtros, ordem ou texto das evidências, configuração ou código; não
é uma credencial nem dispensa leitura humana do contexto antes de um envio.
As capturas da avaliação usam `google-genai==1.75.0` em `.venv/sdk175` com
`python` do sistema. Nesse ambiente já preparado, confira o hash do lote sem
chamar a API:

```powershell
$env:PYTHONPATH = '.venv/sdk175'
python -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json --repetir-transitorios
```

O hash do lote na configuração entregue, `cfg-citacao-por-resposta`, é
`8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0`.
Para reproduzi-lo, são necessários o mesmo SDK, manifesto, contexto e código;
outra versão do SDK gera outro hash. A política
de prévia, liberação e cota está na
[spec 0007](docs/spec/0007-cli-resposta-gerada.md).
As capturas da configuração por afirmação só são reproduzíveis na tag
`cfg-citacao-por-afirmacao-abandonada`.

Exemplo real (2026-10-17; nota ≤ 2, entrega atrasada, k = 10):

> **Pergunta:** O que os clientes relatam que aconteceu depois que a entrega atrasou?
>
> **Resposta (`respondida`, 5 de 10 fontes citadas):** após o atraso, clientes
> não receberam satisfação ou justificativa dos responsáveis; alguns buscaram
> esclarecimento ou ligaram para reclamar da falta de informação e do prazo
> descumprido.

Fontes citadas, entre elas: “esperava um contato para justificar o acontecido
[...] mas não tive” e “Quero saber o que aconteceu com a minha entrega, o prazo
já passou e não tive satisfação dos responsáveis”. A mesma busca com a pergunta
“O que os clientes relatam sobre entregas atrasadas?” citou os 10 comentários e
devolveu apenas que há atraso: a formulação muda o achado. Três relatos no top-k
levantam uma hipótese (falta de comunicação proativa); não medem sua frequência.

Exemplo real de recusa (2026-10-21; mesmos filtros):

> **Pergunta:** Qual é o prazo oficial de reembolso da Olist quando uma entrega atrasa?
>
> **Resposta (`sem_evidencia`, nenhuma fonte citada):** “As avaliações
> recuperadas não sustentam a resposta solicitada.”

Os 10 comentários recuperados falam de atraso, mas nenhum fala de reembolso ou
de regra da empresa. O modelo explicou isso no registro de execução; a
aplicação mostra a mensagem padrão e não inventa prazo. Captura em
[`reports/demo_cli_p15_20261021.md`](reports/demo_cli_p15_20261021.md).

### Contagem de atrasos

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao contar
```

Conta avaliações com comentário associadas a pedidos entregues. Informa
atrasadas, total elegível, proporção, período de compra e IC95% de Wilson.
Não depende dos resultados da busca e não carrega o modelo de embeddings.
Contrato na [spec 0002](docs/spec/0002-frequencia-atrasos.md).

## Arquitetura e avaliação

```text
CSV Olist -> corpus com texto e metadados
Pergunta -> MiniLM -> busca exata DuckDB com filtros -> evidências candidatas
Contexto revisado -> gerador -> validação de status e citações -> resposta
Corpus completo -> contagem local com população e período
```

Python 3.13 executa o pipeline. Pandas e PyArrow preparam e gravam o corpus;
Sentence Transformers carrega o MiniLM; DuckDB faz a busca exata;
`google-genai` acessa o gerador; Statsmodels calcula o intervalo de Wilson
na EDA e pytest executa os testes. As versões declaradas estão em
[`requirements.txt`](requirements.txt).

MiniLM foi comparado com E5 e TF-IDF usando pooling e julgamento humano. A escolha
e os limites da avaliação estão na [ADR 0002](docs/adr/0002-embedding-minilm-busca-exata-duckdb.md).

**Como os metadados melhoram a recuperação.** O MiniLM acha o assunto, mas não
separa elogio de reclamação: "entrega rápida" e "entrega lenta" têm cosseno 0,76.
O filtro por metadado vira `WHERE` na mesma consulta SQL e restringe o top-10 ao
recorte escolhido; em P09, o filtro de nota retirou as reclamações. Medimos
nas 5 perguntas do gabarito cuja redação nomeia polaridade ou situação da entrega,
com o filtro escolhido lendo a pergunta e a previsão registrada antes de rodar
([spec 0009](docs/spec/0009-ganho-filtros-metadados.md),
[relatório](reports/ganho_filtros_20261021.md)). Precisão@10 pela busca do produto:

| Pergunta | Filtro | Sem filtro | Com filtro |
|---|---|---|---|
| P09: o que mais elogiam na entrega | `nota >= 4` | 0,6 | 1,0 |
| P02: pedido que nunca chega | `situacao_entrega = nao_entregue` | 0,4 | 0,6 |
| P01: reclamações de atraso | `situacao_entrega = atrasado` | 1,0 | 1,0 |
| P10: clientes satisfeitos | `nota >= 4` | 1,0 | 1,0 |
| P11: pontos das notas ruins | `nota <= 2` | 1,0 | 1,0 |

Diferença média +0,12 (IC95% por bootstrap sobre as perguntas: +0,00 a +0,28;
n = 5 perguntas, um anotador, 28 julgamentos cegos novos com 1 discordância em
10 âncoras). Com n = 5 o intervalo é descritivo, não prova superioridade. Em P09,
os 4 erros sem filtro eram reclamações de nota 1 ou 2; com o filtro, as 10 são
elogio. O filtro de nota quase não perde relato relevante (23 de 24 conhecidos em
P09). O de situação de entrega perde: só 4 de 14 relatos conhecidos de "não chegou"
estão em pedidos marcados `nao_entregue`. Por isso: nota para polaridade; situação
de entrega para recortar a população, sabendo que deixa relatos de fora.

Similaridade ajuda a encontrar um relato; não prova que ele contém o fato pedido.
Uma citação válida também não prova que a frase gerada tem suporte no comentário.
O validador rejeita IDs inventados e respostas fora do contrato; quando falta
evidência, retorna `sem_evidencia`. O julgamento humano verifica se as frases
são coerentes com os textos citados.

Status da resposta: `respondida`, `sem_evidencia` e `erro_geracao`. Falha do
serviço não é apresentada como ausência de informação. Quando habilitada no
executor de avaliação, a repetição é limitada a duas chamadas, SDK com uma
tentativa e espera de 2s para falha transitória. Nenhum fallback automático.

Fora do lote curado, cada pergunta do CLI exige prévia, leitura do contexto e
liberação por hash; nenhum envio em lote do corpus.

Evidências: [spec 0006](docs/spec/0006-avaliacao-geracao.md),
[revisão geral](reports/revisao_geral_20261007.md) e
[reavaliação E05](reports/e05_reavaliacao_20261007_01.jsonl).

No gate histórico da configuração entregue, Luiz aprovou 19 casos na rodada 04
e E05 numa reavaliação isolada sob o mesmo contrato: 20/20 casos cobertos
(IC95% de Wilson calculado: 83,9% a 100%). São 18 casos reais, um sintético
e um controle local, escolhidos intencionalmente. O resultado libera apenas a
demonstração curada; não estima a confiabilidade em perguntas novas.

### Decisões técnicas

| Decisão | Motivo e registro |
|---|---|
| Um documento por avaliação, com limpeza mínima | Preserva negação e metadados para conferir cada fonte; [ADR 0001](docs/adr/0001-corpus-limpeza-minima-sem-chunking.md). |
| MiniLM e busca exata em DuckDB | A comparação de recuperação e o custo da indexação estão na [ADR 0002](docs/adr/0002-embedding-minilm-busca-exata-duckdb.md). |
| Filtro de nota para polaridade | Embedding não separa elogio de reclamação; P09 de 0,6 para 1,0 com `nota >= 4` (n = 5 perguntas); [spec 0009](docs/spec/0009-ganho-filtros-metadados.md). |
| Gemini com validação local de status e citações | ID fora do contexto invalida a resposta; suporte da frase exige julgamento humano; [ADR 0003](docs/adr/0003-geracao-gemini-e-validacao-de-evidencias.md). |
| Contagem de atrasos no corpus inteiro | Top-k não fornece denominador de frequência; [ADR 0004](docs/adr/0004-contagem-atrasos.md). |
| Classificação de elogios à entrega | Critérios e limites dos rótulos estão na [ADR 0005](docs/adr/0005-classificacao-elogios.md). |
| Protótipo com Gemini 3.1 Flash-Lite | Modelo e limites da escolha estão na [ADR 0006](docs/adr/0006-gerador-gemini-31-prototipo.md). |
| Até duas tentativas para falha transitória | Repetição observável, sem repetir erro de contrato; [ADR 0007](docs/adr/0007-repeticao-transitoria-observavel.md). |
| Citação por afirmação testada e abandonada | Gate 19/20; a recusa em E17 regrediu em relação à configuração entregue; [ADR 0008](docs/adr/0008-citacao-por-afirmacao.md). |

## Testes

```powershell
New-Item -ItemType Directory -Force .venv/pytest-tmp | Out-Null
& .venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --tb=short -W error::FutureWarning --basetemp .venv/pytest-tmp/local-novo
```

Use uma pasta de basetemp nova por execução. Testes usam fixtures e clientes
falsos, sem API. Passar a suíte não substitui o julgamento humano do conteúdo.
O teste de importação da EDA não executa main nem altera seu relatório histórico.

Para gerar outra EDA, `python src/eda/01_eda_reviews.py` sobrescreve
`reports/eda_olist.md`; esse comando deve fazer parte de uma reavaliação planejada.

## Licença e atribuição

O código em `src/`, `tests/` e scripts está sob [MIT](LICENSE). Dados derivados
e trechos de avaliações estão sob [CC BY-NC-SA 4.0](LICENSE-DATA.md), com
atribuição à Olist. A varredura dos arquivos rastreados em `data/` e `reports/`
não encontrou e-mail, telefone, CPF, CNPJ ou CEP em formato reconhecível.
Nomes próprios no texto livre não foram conferidos manualmente. Os comentários
de origem já estão no dataset público da Olist; isso não elimina o risco
residual de dados pessoais.

## Limites da entrega

- Dados de 2016 a 2018: não representam a operação atual da Olist.
- Avaliações com comentário têm viés de autosseleção. IC95% não corrige esse viés.
- Top-k recupera exemplos, não prevalência de um tema nem causa de reclamação.
- Filtros de nota e situação estão implementados e medidos em 5 perguntas;
  período e categoria não são filtros da entrada atual. O filtro é escolhido
  pelo usuário no CLI, não inferido da pergunta.
- O 0,72 de Precisão@10 da ADR 0002 foi medido na busca usada no pooling; a busca
  do produto difere por maiúsculas (P09 sem filtro: 0,6 contra 0,7). As outras
  9 perguntas não foram remedidas na busca do produto.
- P09 permanece congelado: só a liderança de prazo/rapidez foi liberada;
  ranking completo não foi aprovado.
- Exemplos reais são demonstração (n = 3 perguntas no CLI, seleção intencional),
  não medida de confiabilidade. Roteiro da demo na
  [spec 0004](docs/spec/0004-demo-investigacao-entrega.md).
- Orçamento de chamadas é contado por máquina; duas máquinas somam cotas.
- Há um alerta Dependabot de severidade baixa no PyTorch. A correção não foi
  aplicada para preservar o ambiente usado na avaliação capturada.

### Experimento: citação por afirmação (abandonado)

O experimento ligou cada frase aos próprios `review_id` para facilitar a
localização de uma alegação errada. A configuração entregue cita fontes para a
resposta inteira.

- Luiz aprovou 19/20 casos (IC95% de Wilson: 76,4% a 99,1%). Houve 0 falha de
  contrato em 19 julgáveis (IC95%: 0% a 16,8%). Os casos foram escolhidos
  intencionalmente; os intervalos não estimam o desempenho geral.
- E17, "A entrega foi elogiada neste contexto?", recebeu uma recusa. A
  configuração entregue respondia com a crítica citada. Recusar com evidência
  disponível perdeu cobertura. A hipótese de que uma pergunta negativa criou
  atrito com o contrato por afirmação não foi testada.
- Código e capturas: tag `cfg-citacao-por-afirmacao-abandonada`. Decisão na
  [ADR 0008](docs/adr/0008-citacao-por-afirmacao.md), contrato na
  [spec 0008](docs/spec/0008-citacao-por-afirmacao.md) e votos na
  [ficha oficial](reports/ficha_julgamento_oficial_20261020.jsonl).
