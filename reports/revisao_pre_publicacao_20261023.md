NÃO PODE PUBLICAR: o GitHub ainda está privado e o vídeo final de até 7 minutos não foi apresentado para conferência.

# Revisão pré-publicação, 23/10/2026

**Escopo.** `main` em `81dedba77f66`, igual ao clone novo do remoto. Li o enunciado, páginas 4 a 10, e `reports/revisao_geral_20261007.md`. A revisão foi somente leitura no TC4. Não houve chamada ao Gemini, commit ou push. O clone e seus downloads ficaram em `.tmp_tc4_prepub_20261023/`, fora do repositório aninhado.

## Reprodução a partir do remoto

| Achado | Arquivo:linha ou commit | Gravidade | Sugestão |
|---|---|---|---|
| Clone de `81dedba`, Python 3.13, instalação e `pip check` concluídos. O comando de testes do README passou: **344 testes**. | `README.md:16-28,298-307` | opcional | Manter o comando documentado com criação prévia de `.venv/pytest-tmp`. |
| `python -m pytest -q` falhou ao criar o diretório temporário padrão neste ambiente. O comando literal do README funcionou. Não atribuo a falha ao código. | `README.md:298-307` | opcional | Para o avaliador, usar o comando do README. |
| Download novo dos nove CSVs, SHA-256 do ZIP igual ao esperado. Corpus regenerado: 42.174 documentos, 36.453 textos distintos. `--acao contar` retornou 3.813/40.303, 9,46%, IC95% 9,18% a 9,75%. Não usei `data/raw/` do checkout inicial. | `README.md:59-78`; `src/preprocessing/corpus.py:59` | opcional | Preservar o hash do ZIP como controle de versão dos dados. |
| Download dos pesos MiniLM pelo comando do README e `--acao ensaio-sintetico` concluídos. A saída distinguiu gerador falso e recusa por falta de evidência. | `README.md:32-57`; `src/demo.py:98` | opcional | Mostrar o ensaio apenas como integração local. |
| O ZIP baixado fica não rastreado no clone. | `README.md:66` | opcional | Remover o ZIP ou ignorá-lo antes de usar esse clone para qualquer publicação. |

## Enunciado, requisitos 1 a 4

| Item do PDF | Achado | Arquivo:linha ou commit | Gravidade | Sugestão |
|---|---|---|---|---|
| 1. Seleção, limpeza, ausentes e documentos | Implementados e justificados. Uma avaliação com comentário por `review_id`; ausência mascarada é excluída. Estimativa de entrega ausente ainda vira `no_prazo`, mas não ocorreu no CSV conferido. | `src/preprocessing/corpus.py:14-56`; `docs/adr/0001-corpus-limpeza-minima-sem-chunking.md:1`; `reports/dicionario_olist.md:5-30` | opcional | Em outra versão da base, falhar ou sinalizar estimativa ausente. É o R2 da revisão anterior, sem efeito demonstrado neste corpus. |
| 1. Embeddings, armazenamento e índice | MiniLM e busca exata DuckDB implementados. O corpus Parquet é regenerado a partir dos CSVs. | `src/retrieval/indice.py:15-36,88-101`; `README.md:59-88`; `docs/adr/0002-embedding-minilm-busca-exata-duckdb.md:1` | opcional | Explicar no vídeo que o índice é criado em memória. |
| 2. Pergunta, transformação, recuperação, seleção, contexto e geração | Fluxo integrado no CLI. A pergunta recebe embedding direto. Filtros antecedem top-k. A geração real requer prévia e hash. | `src/retrieval/indice.py:38-101`; `src/rag/responder.py:59-75`; `src/demo.py:138-212`; `README.md:90-135` | opcional | Demonstrar busca, prévia e fontes com uma pergunta preparada. |
| 3. Resposta fundamentada e evidências | IDs são validados, fontes citadas aparecem com texto. Há exemplo real e julgamento humano curado. Isso não prova qualidade para perguntas livres. | `src/rag/responder.py:25-56`; `README.md:177-191,260-281` | opcional | Dizer no vídeo que 20/20 é o lote curado, não taxa de acerto geral. |
| 4. Falta de evidência e fora de escopo | `sem_evidencia` difere de `erro_geracao`. Recusa sobre política oficial foi capturada. O ensaio sintético reproduziu a recusa local. | `src/rag/responder.py:17-22,52-56`; `README.md:193-203,266-270`; `reports/demo_cli_p15_20261021.md:1` | opcional | Mostrar P15 e não prometer recusa universal. |
| Adicional opcional: metadados | Nota, entrega, categoria exata e período da compra estão disponíveis. Ganho medido em 5 perguntas para nota/situação; categoria/período ainda sem medição de ganho. | `src/retrieval/indice.py:38-83`; `src/demo.py:208-213`; `README.md:233-259,325-328` | opcional | Separar no vídeo o ganho medido dos filtros novos. |

## Entregáveis da página 9 e vídeo da página 10

| Item | Achado | Arquivo:linha ou commit | Gravidade | Sugestão |
|---|---|---|---|---|
| Repositório público | Consulta ao GitHub em 23/10 retornou `visibility: private`. | Remoto `luizmaibashi/voc-intelligence-rag-olist`, `main` `81dedba` | bloqueia publicação | Tornar público somente após fechar os demais bloqueadores e conferir a página anônima. |
| Código-fonte | Presente. | `src/demo.py:196-213`; `src/preprocessing/corpus.py:39`; `src/retrieval/indice.py:38` | opcional | Nenhuma. |
| Instalação e execução | Comandos reproduzidos no clone, inclusive dados e pesos. | `README.md:16-78,90-135,298-307` | opcional | Nenhuma. |
| README explicativo | Presente com problema de negócio e limites. | `README.md:1-12,322-346` | opcional | Nenhuma. |
| Arquitetura | Fluxo e componentes descritos. | `README.md:216-231` | opcional | Usar o mesmo fluxo no vídeo. |
| Tecnologias e bibliotecas | Descritas e declaradas. | `README.md:7-9,225-229`; `requirements.txt:1-15` | opcional | Nenhuma. |
| Estratégia RAG | Busca, filtros, contexto, geração e validação descritos. | `README.md:90-135,233-270` | opcional | Nenhuma. |
| Preparação da base | Fonte, limpeza, metadados e regeneração descritos. | `README.md:59-88`; `reports/dicionario_olist.md:1-36` | opcional | Nenhuma. |
| Decisões técnicas | Oito ADRs e tabela de motivos. | `README.md:284-296`; `docs/adr/` | opcional | Nenhuma. |
| Exemplos de perguntas e respostas | Resposta real citada e recusa real presentes. | `README.md:177-203` | opcional | Nenhuma. |
| Reprodução | Clone novo testado. Pesos não têm revisão remota fixada e dependências transitivas não têm lock completo. | `README.md:26-46,59-78,137-176` | corrigir antes do vídeo | Declarar no vídeo o limite de reprodutibilidade exata das capturas. |
| Vídeo até 7 minutos com problema, arquitetura, recuperação, prática, exemplos, fontes e decisões | Nenhum arquivo de vídeo final foi encontrado no clone. `docs/video/` contém quatro slides. O roteiro histórico foi removido em `cf04d5d`. | `docs/video/slides/`; commit `cf04d5d`, `docs/planejamento/ROTEIRO_VIDEO.md` | bloqueia publicação | Gravar, cronometrar e revisar o vídeo final contra os oito tópicos da página 10. |

## Histórico, dados e links

| Achado | Arquivo:linha ou commit | Gravidade | Sugestão |
|---|---|---|---|
| Varri `git log --all -p` por `AIza`, atribuição de `API_KEY`, `GEMINI`, `.env`, caminho local, e-mail, telefone, CPF e CEP. Não apareceu chave literal com os dois primeiros padrões. Houve menções a `GEMINI` e `.env` em código e documentação; os padrões numéricos também atingiram IDs, hashes, métricas e fixtures. Não confirmo dado pessoal a partir desses falsos positivos. | Exemplo de caminho local em `b3d767613bcb`, `docs/planejamento/COMANDO_FASE2_0008.md`; menções de `.env` em `4e96977db693`, `src/demo.py` | corrigir antes do vídeo | Fazer uma revisão humana final dos textos livres versionados antes de mudar a visibilidade. Não publicar os valores suspeitos no checklist. |
| Nenhum `.parquet`, PDF, `.venv`, `.env` ou arquivo de `data/raw/` apareceu como arquivo antes commitado no histórico de nomes. O PDF do enunciado e os slides de aula não estão no Git; o PDF é coberto por `*.pdf` no ignore. Os quatro PNGs próprios de `docs/video/slides/` estão versionados. | `.gitignore:1-7`; `git log --all --name-only` | opcional | Manter PDF e CSVs brutos fora do Git. |
| Os arquivos versionados identificados com comentário bruto da Olist em README, `data/eval/`, capturas e slide 1 constam de `LICENSE-DATA.md`. As tabelas adicionais de P09 com ID e rótulo não contêm coluna de texto de avaliação. | `LICENSE-DATA.md:1-54`; `data/eval/*.csv:1` | opcional | Atualizar a lista se um novo arquivo passar a incluir comentário literal. |
| Links relativos Markdown de README, `docs/README.md`, oito ADRs e doze specs foram resolvidos no clone, sem destino ausente. | `README.md`; `docs/README.md`; `docs/adr/`; `docs/spec/` | opcional | Nenhuma. |
| `docs/README.md` diz haver 10 specs, mas existem 12. | `docs/README.md:38`; `docs/spec/0011-filtros-categoria-periodo.md`; `docs/spec/0012-atraso-por-data.md` | corrigir antes do vídeo | Trocar a contagem por 12. |

## Números e fontes

| Achado | Arquivo:linha ou commit | Gravidade | Sugestão |
|---|---|---|---|
| A contagem vigente do README, ADR 0004 e dicionário bate com o corpus regenerado: 3.813/40.303, 9,46%, IC95% 9,18% a 9,75%. P01 15/30 está registrado como recontagem de cobertura, sem novo julgamento. | `README.md:70-78`; `docs/adr/0004-contagem-atrasos.md:38-39`; `reports/dicionario_olist.md:36`; `reports/atraso_por_data_20261023.md:8-23` | opcional | Usar apenas a regra por data como número atual. |
| 4.339/40.303, 10,77% aparece em relatórios datados como linha histórica da regra por horário. Não encontrei o valor como métrica vigente em README, ADRs, dicionário ou slides. | `reports/atraso_por_data_20261023.md:8-15`; `reports/conferencia_corpus_real_20261007.md:32`; `reports/demo_cli_20261017.md:11` | opcional | Se citar captura antiga, nomear a regra histórica. |
| O ganho médio de precisão por filtro, +0,12 em 5 perguntas, e a latência mediana 5,32 s em 18 tentativas têm amostra e limites no README. E19 é um único ataque sintético. As três prévias novas têm hashes registrados, mas não estão liberadas para envio. | `README.md:233-259,325-339`; `reports/ganho_filtros_20261021.md`; `reports/latencia_capturas_20261023.md`; `reports/injecao_indireta_20261023.md`; `reports/atraso_por_data_20261023.md:25-53` | opcional | Preservar esses qualificadores na fala. |

## Até cinco pontos de confusão para a primeira leitura

| Achado | Arquivo:linha ou commit | Gravidade | Frase de correção |
|---|---|---|---|
| O exemplo real de geração usa captura anterior à regra de atraso por data. | `README.md:177-203`; `reports/atraso_por_data_20261023.md:8-15` | corrigir antes do vídeo | “Esta captura é de 17/10; a contagem atual usa o dia prometido e foi revalidada separadamente.” |
| “20/20” pode soar como precisão geral. | `README.md:278-282` | corrigir antes do vídeo | “Esses 20 casos foram escolhidos e julgados para a demo; perguntas novas exigem nova verificação.” |
| A busca mostra fontes candidatas, mas não frequência de reclamações. | `README.md:90-114,205-214` | corrigir antes do vídeo | “Top-k encontra exemplos; a proporção de atrasos vem de uma contagem do corpus elegível inteiro.” |
| O modo falso pode parecer resposta Gemini. | `README.md:48-57,137-153` | corrigir antes do vídeo | “Esta saída é uma simulação local; a resposta real exige contexto revisado e hash liberado.” |
| O índice em memória e o carregamento de pesos podem parecer travamento inicial. | `README.md:32-46,109-114` | corrigir antes do vídeo | “A primeira busca calcula vetores do corpus e pode demorar; o vídeo mostra uma execução já preparada.” |

## NÃO VERIFICADO

- Vídeo final, duração e qualidade da narração: nenhum vídeo foi fornecido ou encontrado no clone.
- Disponibilidade, factualidade e segurança do Gemini para perguntas novas: nenhuma API foi chamada; os hashes novos `28fb0e20…`, `72ea2402…` e `c53daa65…` continuam sem liberação.
- Detecção completa de PII em texto livre e em todo o histórico: a varredura por padrões não substitui leitura humana; IDs e hashes produzem falsos positivos.
- Reprodutibilidade bit a bit das capturas antigas: revisão exata dos pesos MiniLM e dependências transitivas não está fixada no README.
- Visibilidade anônima após futura mudança para público: a consulta de 23/10 confirmou apenas o estado privado atual.
