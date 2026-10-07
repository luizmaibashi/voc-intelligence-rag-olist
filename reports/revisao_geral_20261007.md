# Revisão geral do TC4 — 2026-10-07

## Veredito

**Direção técnica coerente com o enunciado; entrega ainda incompleta.** O núcleo
tem dados preparados, busca, resposta citada/recusa, contagem e trilha de
avaliação. Não demonstramos prontidão da solução completa para apresentação.
Gate da demo permanece **bloqueado**. Não foi feita chamada de geração nesta
revisão; não houve mudança de código, dependência, payload, modelo ou tentativa.

Três lacunas principais: disponibilidade do gerador, avaliação ponta a ponta
com busca real, e instalação/entrada/documentação/vídeo reproduzíveis.

## Escopo, método e limites

- Snapshot: HEAD `bf1052a4eb552370946a36b90000b1427e5003a5`, `main`, mais harness
  E05, testes, spec e JSONL locais de 07/10. Não houve checkout/reset/staging.
- Fontes: enunciado local `[IAST] - Tech Challenge - Fase 4.pdf`, páginas 4–10;
  AGENTS, specs 0001–0006, decisões e relatórios relevantes; código de corpus,
  recuperação, cache/pooling, geração/recusa, métricas, contagem, P09 e scripts
  auxiliares. Histórico Git consultado; blame conferido nos pontos de entrada.
- Leituras independentes com perfis `sonnet-low` (inventário/entrega) e
  `sonnet-medium` (contratos locais de geração e refutação). A ferramenta não
  informa um identificador verificável do modelo Sonnet 5.5. Saídas auditadas
  pelo principal contra código, registros, enunciado e reproduções locais.
- Revisão focada de conformidade e riscos; não é execução do workflow dedicado
  `spec-compliance` nem auditoria integral de todas as dependências/história.
  Nenhuma medição nova de retrieval, factualidade ou disponibilidade geral.
- Não regeneramos corpus, embeddings, pool, gabarito, relatórios históricos ou
  formulários P09. Nenhum texto novo foi enviado ao Gemini.

## Requisitos acadêmicos e evidência de atendimento

| Requisito | Evidência | Estado |
|---|---|---|
| Seleção, limpeza, ausentes e documentos justificados (PDF p.6) | EDA/proveniência, ADR0001, `src/preprocessing/corpus.py` | Implementado; reprodução da EDA tem dependência faltante |
| Embeddings, armazenamento e recuperação (pp.6–7) | ADR0002, `src/retrieval/indice.py`, cache validado no pooling | Componentes implementados; aplicação completa ainda sem entrada persistente |
| Pipeline pergunta → busca → contexto → resposta (pp.6–7) | `src/rag/responder.py:59` liga embedding, busca e gerador | Implementado como função; validação atual com corpus real ponta a ponta pendente |
| Fontes verificáveis (p.7) | `responder.py:43–56`, citações preservadas nas capturas | IDs validados; falta exposição integrada de texto/fontes para a demo |
| Reconhecer falta de evidência (pp.7–8) | Specs0001/0006, P15–P18, testes/capturas | Exercitado com contexto curado; não garante recusa geral |
| Metadados (pp.8–9, opcional) | Busca valida/aplica nota e situação de entrega | Parcial; categoria/período não são filtros implementados em `buscar` |
| Código, instalação, README e reprodução (p.9) | Fonte/requirements/ADRs existentes; inventário `git ls-files`, `rg --files` | README e entrada de demo ausentes; reprodução parcial |
| Repositório público (p.9) | Último checkpoint documenta remoto privado | Publicação pendente; visibilidade não consultada novamente nesta revisão |
| Vídeo com demonstração até 7 min (p.10) | Spec0004 fornece narrativa; inventário de arquivos | Vídeo final ausente no projeto |

O PDF exige demonstração prática, não interface web. Interface visual é escolha
de implementação, não motivo para adicionar um framework antes de fechar o fluxo.
A data 01/11 vem do Bridge/retomada, não de uma data explícita no PDF lido.

## O que já está correto

1. **Corpus preserva significado.** Título e mensagem unidos; limpeza mínima
   conserva negação, acentos e texto curto relevante. Uma avaliação por review_id
   é decisão explícita, não deduplicação por texto que apague metadados.
2. **Busca foi comparada com baselines.** ADR0002 documenta MiniLM, E5 e TF-IDF,
   pooling e julgamento humano. Precisão@10 histórica MiniLM: 0,72, IC95%
   bootstrap [0,55;0,87], n=14 perguntas. A diferença pareada para E5 inclui
   zero. É escolha justificável, não superioridade estatística comprovada.
3. **Filtros antecedem deduplicação na busca.** SQL filtra o recorte elegível,
   agrupa por lower(texto) e limita k; notas/situações inválidas falham. Specs0005
   e testes preservam a correção de filtros/cache. Métrica antiga não é nova
   medição da busca após essas alterações.
4. **Cache tem identidade.** Textos ordenados, modelo, prefixo, normalização,
   versão, dimensão e digest dos vetores são verificados. Esse cache serve ao
   pooling/calibração; não há ainda um entrypoint de demo que una toda a carga.
5. **Contagem tem população explícita.** `contar_atrasos` usa corpus elegível,
   não top-k; informa numerador, denominador, período e Wilson. Não mede taxa de
   atraso de todos os pedidos nem frequência de motivos escritos nos comentários.
6. **Resposta e erro não se confundem.** `respondida`, `sem_evidencia` e
   `erro_geracao` são distintos. IDs inventados são rejeitados inclusive na
   recusa. Pertencer ao contexto é necessário, mas não prova suporte factual.
7. **Tentativas são observáveis.** SDK=1; controlador<=2 com espera 2s somente
   para transitórios. Flush preserva cada chamada e o histórico de falhas.
   Não há fallback automático ou terceira tentativa.
8. **P09 tem limite de uso.** Liderança de prazo/rapidez foi liberada por Luiz;
   ranking completo congelado. Isso preserva uma conclusão útil sem alegar
   qualidade do classificador para todos os temas. P09/NLP não bloqueiam a demo.

## Avaliação atual: software, conteúdo, serviço e fluxo

| Camada | Evidência atual | Limite |
|---|---|---|
| Software | **221 testes passaram** em 07/10 | Casos cobertos; não todas as rotas/scripts e não qualidade do LLM |
| Conteúdo com contexto curado | Rodada04: 17 saídas com contexto real aprovadas, E19 sintético e E20 local aprovados | Seleção intencional, revisão em blocos, contextos reutilizados; não taxa geral de acerto |
| Serviço | E05 na rodada04 falhou; reavaliação07/10: 503 → ReadTimeout | Zero saídas em um caso; não há conteúdo para julgamento |
| Ponta a ponta real | Função de integração/testes e smoke sintético históricos | Falta executar/julgar busca real, filtros, fontes, contagem e recusa no fluxo da spec0004 |

E05 já respondeu em rodada anterior. Isso não apaga a falha de serviço atual.
O problema observado ocorre também com contexto escolhido, sem retrieval;
não há evidência para atribuí-lo ao embedding. Google descreve HTTP503 como
indisponibilidade/sobrecarga, mas o registro não prova incidente global ou quota
da conta: https://ai.google.dev/gemini-api/docs/troubleshooting.

## Achados confirmados e débitos

### R1 — Reprodução da EDA falha no ambiente declarado (P2)

`src/eda/01_eda_reviews.py:9` importa `statsmodels.stats.proportion`. A biblioteca
não está em requirements.txt e não está instalada na venv. A importação via
`runpy.run_path(..., run_name="revisao_somente_import")` falhou com
`ModuleNotFoundError: No module named 'statsmodels'`, antes de executar main.
Nenhum relatório foi sobrescrito. Inventário não encontrou setup/lock alternativo.

Impacto: alguém que siga só requirements não reproduz a EDA. `pip check` passa
porque verifica consistência das bibliotecas instaladas, não os imports do
projeto. A suíte não importa esse script. Correção fica para etapa de reprodução:
declarar a dependência com versão validada ou reutilizar uma implementação
local adequada do intervalo; não instalar/adotar alternativa nesta revisão.

### R2 — Estimativa de entrega ausente é assumida como pontual (P3)

`src/preprocessing/corpus.py:26–29`: entrega real presente e prevista NaT produz
`no_prazo`. Fixture mínima reproduziu o resultado. Os testes do corpus cobrem
data real ausente, atraso e pontualidade, mas não prevista ausente.

**Impacto atual não demonstrado:** nos CSVs locais todas as estimativas existem
e todos os order_id das avaliações existem na tabela de pedidos (checagens
booleanas locais). Portanto não há evidência de corrupção dos números atuais.
Antes de aceitar outro conjunto, exigir estimativa válida para julgar prazo
ou tratar desconhecido explicitamente; nunca presumir pontualidade silenciosa.

### R3 — Dependência com advisory e ambiente sem lock completo

Venv/requirements usam torch2.12.1. Advisory GHSA-rrmf-rvhw-rf47 confirmado em
07/10: afetadas <=2.12.1, versão corrigida2.13.0, vetor local via torch.jit.script.
Fonte: https://github.com/advisories/GHSA-rrmf-rvhw-rf47.
Busca direta src/tests não encontrou uso de TorchScript, torch.load ou
trust_remote_code; isso não prova ausência de caminho transitivo.

Validar patch em ambiente separado antes da publicação/entrada livre, seguindo
auditoria06/10. Não foi demonstrado bloqueador de outra dependência. Gatilho:
publicação/demo livre; compatibilidade e efeito sobre embeddings pendentes.
A faixa google-genai>=1.73,<2 permite variação; SDK julgado é1.75.0. Documentar
versão efetiva e avaliar lock para reprodução, sem alterar o ambiente capturado.

### R4 — Documentos históricos não são o status operacional

Spec0001 ainda se apresenta como rascunho; auditoria06/10 e relatório de
integridade têm checkpoints anteriores à rodada04. ADR0006 registra escopo de
três frases no momento da decisão, ampliado depois apenas para E01–E20.
Ler o registro mais recente/spec0006/Bridge para o estado atual; não reabrir
votos ou remover histórico. README deverá separar contrato atual de histórico.

Nenhum novo defeito foi confirmado no harness/geração/limite de chamadas.
SQL parametrizado, barreira de contexto revisado, validação de citações/hash e
controle de tentativas foram preservados. Isso não substitui auditoria completa
de segredos/PII/histórico antes de tornar o repositório público.

## Verificações executadas

Previsão humana antes da suíte: **todos passam**. Observado: **221 passed**.

```powershell
& .venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --tb=short -W error::FutureWarning --basetemp .venv/pytest-tmp/revisao-geral-20261007-01
& .venv/Scripts/python.exe -X utf8 -m pip check
```

Python3.13.15; NumPy2.4.3, Pandas3.0.1, Torch2.12.1,
SentenceTransformers5.6.0, DuckDB1.5.2, google-genai1.75.0, pytest9.0.3.
`pip check`: No broken requirements found. Corpus processado e nove CSVs raw
presentes; não foram reconstruídos. `git diff --check` sem erro no projeto.
Evidência de serviço preservada em `e05_reavaliacao_20261007_01.jsonl`.

## Próximos passos recomendados, para decisão de Luiz

1. **Fechar reprodução local e uma entrada mínima.** Resolver R1; especificar
   comando que carregue corpus/encoder/índice, mostre fontes e faça contagem.
   Conectar as peças localmente primeiro com gerador falso, sem API. Planejar
   arquivos antes de implementação. Guardar teste R2 na preparação de dados.
2. **Tratar disponibilidade em paralelo.** Rever ADR0006, usando erros já
   preservados e diagnóstico delimitado após nova previsão; não repetir E05
   continuamente nem aumentar timeout/tentativas. Troca de modelo/provedor ou
   nível de serviço precisa de decisão e avaliação própria, não fallback oculto.
3. **Validar fluxo real da spec0004.** Pergunta sobre atrasos com filtros
   explícitos, comentários recuperados/fontes, contagem local e P15. Revisar
   os textos efetivamente recuperados e obter liberação para novos payloads
   antes de API. Preservar resposta bruta, aplicação e julgamento humano.
4. **Concluir o gate explicitamente.** Separar conteúdo, serviço e retrieval;
   sucesso posterior não converte rodada04 em lote integralmente aprovado.
   Se a configuração mudar, definir regressões e não herdar votos sem evidência.
5. **Entregar.** README com instalação/execução, arquitetura, dados, exemplos,
   limites e justificativas; checagem de dependência/segredos/publicação; repo
   público e vídeo<=7min. Não adicionar P09 completo, classificador novo, troca
   de banco ou interface elaborada sem necessidade da entrega.

## Explicação para aprendizado

O sistema reúne quatro responsabilidades: um arquivo organizado de relatos,
um bibliotecário que encontra trechos, um redator que os explica e uma calculadora
que conta no conjunto inteiro. A citação funciona como endereço do trecho.
Endereço válido não garante que a explicação corresponda ao texto.

Testes locais verificam regras das peças. Contexto curado entrega os trechos
prontos ao redator. Ponta a ponta exige que o bibliotecário encontre sozinho os
trechos certos. Disponibilidade exige que o redator esteja acessível. São
perguntas diferentes; um resultado positivo em uma não libera todas as outras.

Para um gestor, valor proposto é investigar uma reclamação e conferir sua fonte.
Não medimos economia, receita ou representatividade da operação atual. Para a
carreira do Luiz, a próxima evidência útil é uma solução reproduzível que ele
consiga demonstrar e explicar, com esses limites claros.
