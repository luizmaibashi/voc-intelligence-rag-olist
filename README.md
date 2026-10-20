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

Os pacotes principais têm versões fixadas. A faixa do SDK Gemini e as
dependências transitivas ainda não formam um lock completo. O ambiente dos
registros de geração usou google-genai 1.75.0; uma versão diferente muda seu hash.
Statsmodels 0.14.6 é declarado porque o script da EDA usa o intervalo de Wilson.

## Pesos do modelo

A entrada local carrega `paraphrase-multilingual-MiniLM-L12-v2` com
`local_files_only=True`. Não baixa pesos automaticamente. Se o modelo ainda
não estiver no cache, prepare-o com conexão antes de executar a demo:

```powershell
& .venv/Scripts/python.exe -X utf8 -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")'
```

Esse comando baixa o modelo; não envia comentários da Olist. Nome do modelo
não fixa uma revisão dos pesos remotos. Registre a revisão na avaliação final.

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
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao responder --pergunta "O que os clientes relatam sobre entregas atrasadas?" --nota-max 2 --situacao-entrega atrasado --k 10 --executar --aprovacao-sha256 <hash>
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

O hash autorizado desse lote é
`203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`.
Para reproduzi-lo, são necessários o mesmo SDK, manifesto, contexto e código;
outra versão do SDK gera outro hash. A política
de prévia, liberação e cota está na
[spec 0007](docs/spec/0007-cli-resposta-gerada.md).

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

### Decisões técnicas

| Decisão | Motivo e registro |
|---|---|
| Um documento por avaliação, com limpeza mínima | Preserva negação e metadados para conferir cada fonte; [ADR 0001](docs/adr/0001-corpus-limpeza-minima-sem-chunking.md). |
| MiniLM e busca exata em DuckDB | A comparação de recuperação e o custo da indexação estão na [ADR 0002](docs/adr/0002-embedding-minilm-busca-exata-duckdb.md). |
| Gemini com validação local de status e citações | ID fora do contexto invalida a resposta; suporte da frase exige julgamento humano; [ADR 0003](docs/adr/0003-geracao-gemini-e-validacao-de-evidencias.md). |
| Contagem de atrasos no corpus inteiro | Top-k não fornece denominador de frequência; [ADR 0004](docs/adr/0004-contagem-atrasos.md). |
| Classificação de elogios à entrega | Critérios e limites dos rótulos estão na [ADR 0005](docs/adr/0005-classificacao-elogios.md). |
| Protótipo com Gemini 3.1 Flash-Lite | Modelo e limites da escolha estão na [ADR 0006](docs/adr/0006-gerador-gemini-31-prototipo.md). |
| Até duas tentativas para falha transitória | Repetição observável, sem repetir erro de contrato; [ADR 0007](docs/adr/0007-repeticao-transitoria-observavel.md). |
| Citação por afirmação em experimento | Liga cada frase a suas fontes para auditoria, sem prometer maior correção; [ADR 0008](docs/adr/0008-citacao-por-afirmacao.md). |

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

## Limites e entrega pendente

- Dados de 2016 a 2018: não representam a operação atual da Olist.
- Avaliações com comentário têm viés de autosseleção. IC95% não corrige esse viés.
- Top-k recupera exemplos, não prevalência de um tema nem causa de reclamação.
- Filtros de nota e situação estão implementados; período e categoria não são
  filtros da entrada atual.
- P09 permanece congelado: só a liderança de prazo/rapidez foi liberada;
  ranking completo não foi aprovado.
- Exemplos reais são demonstração (n = 2 perguntas no CLI, seleção intencional),
  não medida de confiabilidade. Roteiro da demo na
  [spec 0004](docs/spec/0004-demo-investigacao-entrega.md).
- Orçamento de chamadas é contado por máquina; duas máquinas somam cotas.
- Revisar o alerta de PyTorch e a compatibilidade do patch em ambiente separado
  antes de publicação/entrada livre. Não alterar o ambiente da avaliação capturada.
- Publicação do repo e vídeo de até 7 minutos ficam para a etapa de entrega.

<!-- PENDENTE-GATE-0008 -->
### Texto a fechar após o gate E01–E20, até 25/10

**Se a configuração por afirmação for adotada:** a resposta liga cada frase
validada aos `review_id` correspondentes. Isso facilita localizar e corrigir
uma alegação; não prova que a frase é verdadeira ou sustentada. Registrar aqui
o resultado do julgamento dos 20 casos, com numerador, `n`, IC95%, exclusões
e distinção entre falha de serviço, contrato, recusa e suporte semântico.

**Se a configuração for abandonada:** a entrega usa a tag
`cfg-citacao-por-resposta`. A lista de fontes vale para a resposta inteira,
sem vínculo garantido entre frase e fonte. Registrar aqui o motivo do abandono
e os números do gate histórico com numerador, `n`, IC95% e limites da seleção.
<!-- /PENDENTE-GATE-0008 -->
