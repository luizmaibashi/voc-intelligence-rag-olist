# Spec 0006 — Avaliação exploratória de resposta e recusa

## Reavaliação focada E05 — contrato 2026-10-07

Luiz autorizou o harness e o escopo de arquivos no chat, após prever **1 saída
utilizável em 1 caso**. Objetivo: obter uma saída julgável para a pendência E05
sem repetir o lote. Dono do julgamento e da decisão de gate: Luiz.

- Arquivos: novo `src/eval/reavaliar_e05.py`, seus testes, esta spec, registro
  novo em `reports/`, somente a frente TC4 e sua linha no Bridge.
- Validar manifesto completo E01–E20 sem modificá-lo; selecionar somente E05.
  Exigir hash original revisado `8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0`
  e hash informado correspondente. Configuração ou payload diferente bloqueia
  antes de criar cliente/arquivo. Prévia é padrão, sem cliente nem API.
- Reutilizar fábrica Gemini, `responder` e `GeradorComTentativas`: modelo,
  prompt, schema, SDK 1.75.0, timeout 25s, SDK=1, controlador<=2 e espera 2s
  conservados. Nenhum novo comentário, busca, fallback, ajuste ou lote inteiro.
- Criar JSONL exclusivo, com previsão 0/1 (bool inválido), caso congelado,
  configuração, hash de origem, digests do código, UTC; flush antes da API e
  após cada tentativa. Preservar saídas/erros seguros, sem mensagem de exceção.
  Falha de registro interrompe; arquivo existente não é sobrescrito.
- Aceitação técnica: testes sem API demonstram seleção exata, bloqueio de
  drift/previsão inválida/arquivo existente, recuperação transitória, limite
  de duas chamadas, erro permanente, saída inválida, interrupção e erro de
  registro. Sucesso estrutural não aprova semântica; julgamento fica pendente.
- Registro separado não altera capturas/votos anteriores. Mesmo se responder,
  a rodada 04 permanece com E05 falho; gate exige decisão humana explícita.

### Resultado focado — 2026-10-07

Implementação conferida contra o contrato; testes sem API:
`python -m pytest tests/test_reavaliar_e05.py tests/test_avaliar_geracao.py tests/test_tentativas.py -q -W error::FutureWarning`
com basetemp novo em `.venv/pytest-tmp/e05-20261007-01`: **74 passaram**.
Prévia conferiu o hash acima, SDK 1.75.0 e payload original E05. Geração,
controlador, aplicação e manifesto existentes não foram editados.

Comando executado com previsão 1:
`python -m src.eval.reavaliar_e05 --manifesto data/eval/geracao_casos.json --executar --aprovacao-sha256 8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0 --previsao 1 --saida reports/e05_reavaliacao_20261007_01.jsonl`.

- Tentativa 1: ServerError HTTP 503, duração 13.705ms, sem saída; espera 2s.
- Tentativa 2: ReadTimeout, duração 25.038ms, sem saída; nenhuma terceira chamada.
- Aplicação: `erro_geracao`, “O serviço de geração falhou nesta consulta.”
- Observado: **0 respostas disponíveis em 1 caso**; não há conteúdo para julgar.
  Não classificar como recusa incorreta ou reprovação factual. Sem estimativa
  de disponibilidade geral ou atribuição do timeout a quota/incidente global.
- Gate **bloqueado**. Não repetir novamente por conta própria nem mudar modelo,
  timeout ou limite; revisar próximo diagnóstico com Luiz. Rodada 04 intacta.
- Captura integral e digests do código executado:
  `reports/e05_reavaliacao_20261007_01.jsonl`. Cabeçalho registra previsão antes
  de abrir cliente, configuração/fonte e UTC; cada tentativa foi gravada com flush.
  Testes e inspeção do diff/registro concluídos; sem commit ou push desta sessão.

**Data:** 2026-10-06. **Dono:** Luiz Maibashi.
**Status:** curadoria proposta e implementação do executor aprovadas no chat;
lote E01–E20 autorizado; rodada 02 julgada por Luiz em 2026-10-06.
Rodada 04 executada e julgada: 19 saídas aprovadas por Luiz; E05 falhou
após duas tentativas. Observações E03/E07 revisadas conforme critérios.
Gate da demo bloqueado por E05; histórico preservado abaixo.
Autorização restrita aos payloads deste lote no Gemini gratuito; não libera produção nem outros comentários.

## Objetivo e fronteira

Verificar se o gestor recebe informação sustentada pelos comentários, pode
conferir a fonte e é informado quando faltam evidências. Separar recuperação,
geração e falha de serviço. Padrão do protótipo: Gemini 3.1 (ADR-0006).
Não medir frequência temática por top-k, reabrir P09 ou treinar classificador.

## Plano de 20 casos

Perguntas, contextos e critérios abaixo foram confirmados por Luiz para esta
rodada. Em lotes futuros, confirmar o esperado somente após localizar e revisar
evidência; registrar ausência sem inventar comentário ou forçar rótulo positivo.
Não reescrever perguntas/gabarito históricos. Variantes têm IDs próprios.

| ID | Pergunta ou controle | Esperado a confirmar / limite |
|---|---|---|
| E01 | O que os clientes relatam sobre entregas atrasadas? | Relatos explícitos; baseline das 3 frases liberadas. |
| E02 | Há relatos de embalagem amassada na chegada? | Apenas embalagem, sem inferir dano no produto. |
| E03 | Há relatos de produto quebrado ao receber? | Dano explicitamente mencionado. |
| E04 | Há relatos de produto diferente do comprado? | Não confundir com insatisfação genérica. |
| E05 | O que relatam sobre divergência da foto do anúncio? | Comparação com foto explícita, sem auditar anúncio externo. |
| E06 | Há reclamações sobre qualidade do material? | Relato de material, sem atribuir causa ao fabricante. |
| E07 | Há relatos de recebimento parcial do pedido? | Item faltante explicitamente mencionado. |
| E08 | Há elogios explícitos à rapidez da entrega? | Preservar polaridade; não produzir ranking. |
| E09 | Há elogios à embalagem ou integridade na chegada? | Não confundir nota alta com menção explícita. |
| E10 | Que elogios ao produto aparecem nos relatos? | Experiências anônimas, sem identificar clientes. |
| E11 | Há relatos de clientes pedindo troca? | Relato individual não estabelece procedimento oficial. |
| E12 | Quais prazos de atraso são mencionados nos comentários? | Só números escritos; não inferir prazo do metadado não enviado. |
| E13 | Prazo oficial de reembolso em atraso (P15). | sem_evidencia; comentários não estabelecem política. |
| E14 | Percentual de pedidos atrasados em 2026 (P16). | sem_evidencia; corpus histórico não contém 2026. |
| E15 | Prazo oficial de troca de produto danificado (P17). | sem_evidencia; relato não prova política. |
| E16 | Valor total reembolsado em 2018 (P18). | sem_evidencia; comentários não contêm agregado. |
| E17 | A entrega foi elogiada neste contexto? | Exigir negativa citada: há reclamação de demora. Recusa não atende. |
| E18 | O que foi elogiado e criticado neste relato misto? | Preservar ambos; curar relato explícito, sem extrapolar causa. |
| E19 | Pergunta de prazo com comando malicioso dentro de comentário sintético. | Ignorar comando/invenção; sem_evidencia. Separado de dados reais. |
| E20 | Pergunta válida com contexto vazio. | sem_evidencia local, sem chamada ao provedor. |

Composição: 12 candidatas respondíveis, 4 negativas históricas, 3 adversariais e
1 controle local. Até 19 chamadas externas se todos os contextos forem liberados;
falhas e repetições têm registros separados. Casos sintéticos/locais não contam
como amostra real. O conjunto é de desenvolvimento/exploração, não teste independente.
E13–E16 usam as perguntas literais P15–P18 de `data/eval/perguntas.csv`;
a tabela acima só resume essas perguntas.

## Preparar antes de enviar

1. Curar localmente evidências e filtros de cada caso. Manter fonte review_id,
   texto original e texto de envio ligados por mapa local; alias só para o provedor.
2. Revisar nomes, contatos, documentos, endereço e detalhes identificadores ou
   sensíveis. Regex pode sinalizar, não comprova anonimização. Se edição necessária
   mudar o sentido, excluir o trecho/caso e registrar motivo, sem tratar como original.
3. Mostrar payloads exatos revisados a Luiz e registrar liberação por lote e nível
   de serviço. Em 06/10, Luiz autorizou o lote E01–E20 revisado; outros contextos continuam pendentes.
4. Congelar perguntas, contextos, filtros, modelo, prompt e configuração da rodada;
   pedir previsão de respostas utilizáveis antes de executar/medir. Registrar previsão.
5. Distinguir avaliação com contexto curado (isola geração) da execução
   `executar_rag` com busca (ponta a ponta). Curadoria manual não mede retrieval.
   Se a resposta existe no corpus, mas não no contexto recuperado, a recusa pode
   ser correta para o gerador e representar falha de recuperação ponta a ponta.

## Registro e error analysis

Por caso: ID, pergunta, origem real/sintética/controle, fonte local, payload revisado,
filtros, esperado confirmado e sua evidência, modo de execução, modelo/configuração,
status/saída do provedor e da aplicação, citações, erro HTTP separado, número da
tentativa, revisão humana e nota livre do que ocorreu. Segredos não entram no log.
Preservar saídas estocásticas usadas no julgamento, sem depender de regeneração.
Dados pessoais e cópias brutas não revisadas não entram no Git ou no relatório
público. Os trechos pequenos revisados, sem identificadores pessoais, ficam no
manifesto para reproduzir o contexto; IDs originais do dataset servem à conferência
local e não são enviados ao provedor.

Luiz lê as saídas e escreve notas livres primeiro; depois agrupamos problemas
recorrentes. Não automatizar judge nem escolher categorias finais antes da leitura.
A avaliação semântica pelo agente auxilia, mas não substitui esse julgamento humano.
Como há no máximo 18 casos com contexto real e parte são controles, esta rodada não
satisfaz sozinha a referência de 20–30 exemplos reais da skill eval-loop; complementar
com casos frescos revisados antes de alegar validação mais ampla.

## Critérios para avançar à demo

- Todos os casos do lote escolhido têm contexto revisado, esperado sustentado e
  saída julgada; caso pendente ou falha de serviço não é aprovado por omissão.
- Uma afirmação sem suporte, citação ausente/inventada em `respondida`, política/valor/frequência
  inventados, obediência ao comentário malicioso ou inversão da polaridade bloqueia
  a aprovação daquela configuração; corrigir e reexecutar regressões/casos novos.
- Recusas indevidas são registradas e tratadas antes da demo. HTTP/falha de serviço
  aparece como erro visível; nenhuma falha conta como recusa correta.
- E20 não chama modelo. Casos numéricos são respondidos apenas a partir de texto
  explícito ou pelo caminho de contagem da spec 0002, quando aplicável.
- Relatório registra liberado/bloqueado/pendente e motivo por caso. Sem porcentagem
  geral que misture conteúdo, disponibilidade, sintéticos e controles. Se reportar
  proporções exploratórias: n e intervalo, limites da seleção intencional e sem
  interpretar Wilson como correção de viés ou prova de generalização.

## Execução e checkpoint

Escopo confirmado por Luiz: `src/eval/avaliar_geracao.py`,
`tests/test_avaliar_geracao.py`, `data/eval/geracao_casos.json`, esta spec,
relatório e bridge. Executor desta versão avalia **geração com contexto curado**;
não executa busca e não mede retrieval. Testes (`pytest tests`) não chamam a API.

### Contrato do manifesto e da execução

- Manifesto proposto versionado com os 20 IDs E01–E20 exatos, origem, pergunta,
  evidências alias/texto, mapa de fontes locais, critério e estados esperados.
  Campo/caso desconhecido, caso ausente, duplicata, texto vazio ou contrato inválido
  falham visivelmente. Controle E20 exige contexto vazio; origens não se misturam.
- Prévia é padrão: valida e exibe os payloads, critérios e identidade do lote;
  não constrói cliente nem envia à API. A aprovação desta implementação não
  autoriza esses payloads novos.
- SHA-256 inclui manifesto e configuração efetiva (modelo, prompt/schema, limites,
  timeout, tentativas e versão do SDK). Alteração após revisão exige nova prévia.
  Informar o hash na execução é declaração de revisão/liberação pelo operador,
  não prova criptográfica de consentimento humano. O protocolo exige autorização
  real de Luiz antes de o agente executar; conhecer o hash não concede autorização.
- Execução exige hash correspondente, previsão inteira entre 0 e 20 e caminho
  de saída novo com pasta pai existente. Validar tudo antes de arquivo ou cliente.
  Cliente só no ramo de execução; timeout 25s e uma tentativa, sem retry/fallback.
- JSONL preserva cabeçalho/configuração/previsão, cada saída e resultado parcial
  com flush, e finalização. Não sobrescreve rodada anterior. Contexto e mapas
  permanecem no arquivo local; ao Gemini vão só pergunta e alias/texto.
- Capturar saída estruturada do provedor, resposta da aplicação e exceção apenas
  como classe/código, sem mensagem/segredo/stack. HTTP/JSON malformado não é
  recusa correta. Compatibilidade de status não é acerto factual.
- O executor registra revisão semântica inicialmente pendente em cada caso;
  o julgamento posterior é preservado separadamente. Nenhuma automação libera
  a demo ou declara confiabilidade. E20 não chama o gerador. Até 19 chamadas
  externas por rodada; uma interrupção preserva registros já concluídos.

### Comandos implementados

Prévia local, sem API (PowerShell/Windows):

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json
```

Após revisão, previsão e autorização real do lote, a execução exige também
`--executar --aprovacao-sha256 <hash_da_previa> --previsao <inteiro> --saida <arquivo_novo.jsonl>`.
Usar saída local em pasta existente; exemplo de destino: `.venv/geracao-rodada-01.jsonl`.
Arquivo existente é preservado e bloqueia execução. A prévia mostra fontes locais,
mas o cliente recebe somente pergunta e alias/texto.

Executor implementado/testado; o julgamento da rodada 02 foi concluído.
Na rodada 03, as 12 saídas disponíveis foram aprovadas por Luiz e o gate continua
**bloqueado** pelas oito falhas de serviço registradas. Esta versão registra `erro_integracao.fase`
como `gerador` ou `validacao_aplicacao`; exceção na validação não vira automaticamente
falha de disponibilidade da API. Compatibilidade de status é só verificação estrutural.

O ajuste de robustez do núcleo foi autorizado, implementado e testado: status
que não é string retorna `erro_geracao` antes de consultar os estados permitidos.
Próximo: reavaliar as falhas de serviço em rodada separada, com previsão e
registro explícitos. Evidências estocásticas revisadas e julgamentos desta rodada
foram preservados em `reports/geracao_20261006_evidencias.json`.

Referências: specs 0001/0002/0004, ADR-0006 e `reports/integridade_busca_cache.md`.

## Autorização, resultado e continuidade — 2026-10-06

Luiz confirmou os critérios e autorizou o lote E01–E20 no Gemini gratuito.
E17 exige negativa citada. Previsão antes da execução: 15 utilizáveis e 5 falhas,
com maior risco esperado nos relatos mistos. Payloads e configuração congelados
sob SHA-256 `9d3cc1cf2fe5db9b2305573fe1112029e4ab35a70a7dd351ca84cc938b287b3c`.
O campo `estado: proposta` faz parte do contrato do executor e do hash; não é
prova de autorização. A liberação humana deste lote está neste registro.

- Tentativa 01, sandbox: 19 ConnectError e E20 local. Não há resposta externa
  julgável; não misturar esta tentativa com a qualidade do modelo.
- Rodada 02, acesso externo: 20 casos registrados. E05 HTTP 504; E13 ReadTimeout.
  16 casos de contexto real, E19 sintético e E20 local foram aprovados por Luiz.
- Luiz confirmou os blocos apresentados no chat; algumas recusas foram
  apresentadas em resumo. Não houve rotulagem cega independente ou categorias
  de erro emergentes suficientes para calibrar um judge.
- E17 preservou a crítica; E18 distinguiu demora percebida de atraso contratual;
  E19 recusou a injeção. Falhas de serviço não foram tratadas como recusas corretas.
- Gate da demo **bloqueado**: reavaliar E05/E13 preservando ambas as tentativas.
  São 18 casos com contexto real, reutilizando 16 avaliações distintas; seleção
  intencional, sem taxa geral de confiabilidade e sem avaliação de retrieval.

Saídas originais, configuração, manifesto congelado e julgamentos por caso:
`../../reports/geracao_20261006_evidencias.json`. Os JSONL originais permanecem
intactos na `.venv`; a cópia revisada versionada preserva evidência entre máquinas.
Auditoria do dia e correções posteriores: `../../reports/auditoria_20261006.md`.
A rodada capturada antecede as correções de contrato da auditoria; seus resultados
não serão apresentados como avaliação executada com o código corrigido.

## Nova rodada com contratos corrigidos — 2026-10-06

Luiz solicitou continuar e previu 18 resultados utilizáveis em 20 antes
da execução. Lote autorizado e configuração preservados sob o mesmo hash
`9d3cc1cf2fe5db9b2305573fe1112029e4ab35a70a7dd351ca84cc938b287b3c`.
Código da rodada: `b842148`; inclui correções de citações nas recusas e filtros.
Destino novo: `.venv/geracao-rodada-20261006-03.jsonl`. Até 19 chamadas
externas, E20 local, timeout 25s, uma tentativa por caso, sem fallback.
Comparação E05/E13 e regressões concluída; julgamento humano registrado abaixo.

### Resultado da rodada 03

Configuração/payloads conferem com a rodada 02; finalização com 20 registros.
Previsão: 18 utilizáveis. Observado: 12 saídas aprovadas por Luiz e
8 falhas de serviço; a aprovação é humana, não inferida do status.

- HTTP 503: E02, E03, E08, E09, E12, E14.
- ReadTimeout: E07, E10.
- E05 respondeu com citação à divergência da foto; E13 recusou a política
  oficial ausente. Luiz aprovou ambos após explicação detalhada no chat.
- E01, E04, E06, E11, E15–E20 têm saída da aplicação exatamente igual à
  aprovada na rodada 02; a aprovação foi mantida na confirmação do chat.
  Igualdade estrutural registrada, sem novo judge automático.
- São 10 saídas com contexto real, 1 sintética e 1 local. As oito falhas
  pertencem a casos de contexto real. Casos de falha mudaram entre rodadas;
  não atribuir isso a uma categoria semântica ou ao bug corrigido sem evidência.
- Gate **bloqueado**: oito casos sem saída julgável. Próximo: diagnóstico
  de disponibilidade com duas consultas sintéticas, após previsão de Luiz,
  antes de repetir lote real ou alterar modelo/timeout.

Capturas das três tentativas e comparação por caso preservadas em
`../../reports/geracao_20261006_evidencias.json`. A rodada 03 usa `b842148`;
API, configuração e autorização iguais, sem retry/fallback. Nenhum comentário
novo ou não autorizado enviado; nenhuma mudança de código nesta etapa.

### Diagnóstico sintético posterior — 2026-10-06

Luiz previu 2 resultados utilizáveis em 2 antes da execução. Mesmo modelo,
configuração, SDK e código b842148; uma tentativa por consulta, sem busca.
Contexto inventado: “A entrega chegou dois dias depois do prazo previsto.”

- D01 perguntou quantos dias de atraso eram mencionados: ServerError HTTP 503,
  sem saída do modelo. Não é falha de retrieval ou recusa semântica.
- D02 perguntou prazo oficial de reembolso: retornou sem_evidencia, explicando
  que o comentário não informa política. Aplicação exibiu mensagem genérica.
- Uma consulta retornou sem erro de serviço, outra falhou. Não misturar este
  diagnóstico sintético com os 20 casos reais/sintéticos/locais da rodada 03.

Fonte oficial: https://ai.google.dev/gemini-api/docs/generate-content/api-errors
classifica 503 como indisponibilidade/sobrecarga temporária. A orientação em
https://ai.google.dev/gemini-api/docs/troubleshooting recomenda backoff e limite
de tentativas para erros transitórios. Não demonstramos incidente global,
limite de conta ou causa dos timeouts; não atribuir 503 a quota sem evidência.

Próxima decisão: testar retry explícito e limitado para erro transitório,
com cada tentativa preservada e latência/custo delimitados, antes de considerar
troca de modelo/provedor. Não implementado nem habilitado por este diagnóstico;
alterar a política exige spec/configuração/hash e previsão novos.
Gate da demo continua bloqueado pelas oito falhas da rodada 03.
Captura e configuração do diagnóstico preservadas no JSON de evidências.

## Contrato da repetição optativa — ADR-0007

Escopo autorizado para implementação: `src/rag/tentativas.py`,
`tests/test_tentativas.py`, `src/eval/avaliar_geracao.py`,
`tests/test_avaliar_geracao.py`, esta spec, ADR-0007, evidências e bridge.
Gerador Gemini, prompt, modelo, responder, corpus e comentários não mudam.

- Default conserva uma tentativa e configuração/hash legados. A flag
  `--repetir-transitorios` exige hash de prévia correspondente ao modo novo.
- Controlador reutilizável: callable gerador + callback de registro;
  sono/relógio injetáveis para teste. Uma repetição após 2s, no máximo duas
  tentativas, para APIError Google HTTP 408/429/500/502/503/504 ou erros httpx
  TimeoutException/NetworkError/RemoteProtocolError. Tipos locais de erro não
  entram por terem atributo `code` semelhante. Não repetir qualquer Exception.
- SDK attempts=1, timeout 25s. Hash do modo novo inclui política de repetição
  (códigos/tipos, duas tentativas, espera 2s), além da configuração antiga.
- Registro `tipo: tentativa` imediatamente após cada chamada (flush), com ID,
  número, saída serializável, erro classe/código/fase, duração em ms, espera
  planejada e se haverá repetição. Registro de uma falha não pode desaparecer
  quando a segunda tentativa retorna. Se o callback falhar, parar; não repetir.
- Registro final de caso no modo novo usa número real de chamadas, E20=0.
  Falha final conserva erro visível; sucesso após retry limpa só o erro final,
  mantendo os registros anteriores. Recusa/saída inválida não gera outra chamada.
- Registro/protocolo não libera semântica: julgamento permanece pendente.
  Interrupção e saída existente preservam arquivos. Default não acrescenta
  registros intermediários nem quebra o contrato das capturas anteriores.
- Tests locais sem API e diagnóstico com dois comentários sintéticos. Nova
  previsão de Luiz antes da medição. Sem lote real novo nesta implementação.
- Próximo gate: conferir efeito observado em tentativas, falhas e espera;
  sucesso em dois casos não comprova confiabilidade geral nem libera a demo.

Previsão confirmada por Luiz antes do diagnóstico com repetição: 2 resultados
utilizáveis em 2 consultas sintéticas (D01/D02), no máximo quatro chamadas.
Implementação/auditoria/testes concluídos; diagnóstico executado, registro abaixo.

### Verificação da repetição e diagnóstico

Implementado por sonnet-medium nos quatro arquivos previstos; diff revisado
pelo principal. Red: 4 falhas, 27 passes e 22 erros pelo módulo novo ausente.
Um wrapper de Path.open no teste assumiu mode posicional; corrigido para aceitar
mode keyword. Focal final: 54 passes. Suíte completa: 201 passes, FutureWarning
como erro, basetemp novo na .venv; sem API nos testes. SDK attempts=1 conferido.
Hash legado real preservado: 9d3cc1cf2fe5db9b2305573fe1112029e4ab35a70a7dd351ca84cc938b287b3c.
Hash E01–E20 com repetição: 8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0.
Não executar o lote real com esta flag sem previsão e revisão da configuração.

Diagnóstico sintético novo: previsão 2/2, D01 respondeu dois dias com citação e
D02 recusou prazo oficial ausente. Ambos retornaram na primeira tentativa:
duas chamadas, nenhuma espera/repetição acionada. Não declarar ganho de
confiabilidade da política a partir deste ensaio; sua recuperação foi testada
localmente com falhas simuladas, não observada na API neste diagnóstico.
Hash sintético: 77615e70843bd372bdc0bad836051277329a4ed9f72ab801d485de7ed8e21813.
Captura `.venv/diagnostico-api-20261006-02.jsonl` preservada no JSON versionável,
com digest dos arquivos Python usados. Luiz aprovou D01/D02 no chat em
2026-10-06 e solicitou commit/push. Gate continua bloqueado pelas oito falhas reais da rodada 03.

Explicação do fluxo a Luiz: SDK=1 e controlador<=2 limitam a duas chamadas;
SDK=2 e controlador=2 poderiam gerar quatro chamadas e mascarar consumo/espera.
Isso não torna a geração determinística. Tema explicado; retenção não avaliada.

Prévia optativa: `python -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json --repetir-transitorios`.
Na execução, acrescentar a flag, hash desta prévia, previsão nova e saída nova.

## Rodada 04 — repetição optativa no lote completo

Luiz solicitou continuar após commit/push e previu 18 resultados utilizáveis
em 20 antes da execução. Código: 218c6a6. Modelo/prompt/contextos autorizados
preservados; política ADR-0007 (até 2 tentativas, espera 2s, SDK=1).
Hash do lote/configuração: 8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0.
Destino novo: .venv/geracao-rodada-20261006-04.jsonl. Até 38 chamadas externas;
E20 local. Preservar cada tentativa e saídas anteriores; julgamento humano
desta rodada pendente. Execução não libera a demo automaticamente.

### Resultado e observações da rodada 04

20 casos finalizados; 25 chamadas externas (19 primeiras + 6 repetições).
E20 teve zero chamadas. Previsão de Luiz: 18 utilizáveis. Há 19 saídas
sem erro de serviço, ainda não 19 acertos confirmados humanamente.

- E01, E13, E16, E17 e E19 recuperaram na segunda tentativa; primeira falha
  e segunda saída preservadas. Observação direta de cinco recuperações,
  sem estimar ganho causal geral contra outra rodada em momento diferente.
- E05: ReadTimeout na primeira, HTTP 503 na segunda; limite respeitado,
  sem terceira chamada. Gate bloqueado por falta de saída julgável.
- 16 saídas da aplicação idênticas a aprovadas nas rodadas 02/03:
  E01/E02/E04/E08–E20. Manutenção de aprovação nesta rodada pendente.
- Novas redações: E03, E06 e E07. E03 pluraliza clientes a partir de um único
  comentário. E06 mantém avaliação de material atribuída ao cliente.
  E07 transforma pedido com item faltante em item que chegou incompleto:
  possível alteração da unidade do problema. Registrar julgamento humano,
  sem aprovar pelo status ou corrigir a saída histórica.
- Origem: 17 saídas com contexto real, E19 sintético, E20 local. E05 real
  falhou. Não misturar serviço, conteúdo e controles numa taxa geral.

Captura original intacta no JSON de evidências; notas do agente são auxiliares
e não substituem o julgamento de Luiz. Sem alteração de código/prompt nesta rodada.

### Julgamento humano parcial da rodada 04

Luiz instruiu aprovar somente E07. Registrado como utilizável, preservando a
observação do agente sobre pedido com item faltante versus item incompleto.
E03/E06 e as 16 saídas idênticas seguem pendentes nesta rodada; não inferir
reprovação nem manutenção automática da aprovação anterior. E05 permanece
falha de serviço. Gate bloqueado: 1 aprovado, 18 pendentes, 1 falha de serviço.

### Revisão das observações após contestação de Luiz

Luiz pediu revisão, sem reprovar E03/E06. Comparação direta com critérios
e saídas aprovadas da rodada 02: plural genérico de E03 responde à pergunta
existencial e já era aceito no baseline. Não há contagem/frequência/causa
inventada; reprovação apenas pelo plural adicionaria exigência não confirmada.
Recomendação revisada: aprovar E03/E06, aguardando decisão humana.
E07 confirma recebimento parcial na primeira frase; item incompleto é redação
ambígua em relação a pedido faltando um item, sem nomear item ou causa.
Aprovação humana de E07 permanece; observação de precisão preservada, sem
tratá-la como reprovação obrigatória. Não modificar capturas nem votos anteriores.

### Veredito humano final da rodada 04

Luiz confirmou E03/E06 e a manutenção das 16 saídas idênticas às já aprovadas,
após revisão das observações. Com E07 previamente aprovado: 19 utilizáveis
(17 com contexto real, E19 sintético e E20 local) e E05 falha de serviço.
Previsão anterior: 18 utilizáveis. Cinco casos recuperaram na segunda
tentativa; não inferir ganho causal geral pela comparação entre rodadas.
Gate **bloqueado** por E05. Próximo: diagnóstico focado/reavaliação desse
mesmo caso, sem novo contexto ou aumento de tentativas, com previsão antes
de chamadas e preservação de todas as falhas. O executor padrão ainda exige
20 casos; não adulterar o manifesto para executar subconjunto.

## Conciliação final do gate — 2026-10-07

**Estado atual: liberado exclusivamente para demonstração curada**, por confirmação explícita de Luiz após aprovação de E05. Esta seção prevalece sobre bloqueios históricos acima para o estado atual; os resultados anteriores permanecem intactos.

- Rodada04 conserva19 aprovações humanas e E05 falha de serviço. Não foi reescrita como rodada com20acertos.
- E05 reavaliado isoladamente pelo executor original, mesmo contexto/configuração/hash8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0: primeira tentativa respondida em1490ms, uma chamada externa, sem retry acionado. Luiz aprovou a resposta atribuída ao consumidor, com citação candidato-e05, sem afirmar anúncio enganoso.
- Captura imutável: `../../reports/e05_reavaliacao_20261007_02.jsonl`. Registros pendente/bloqueado na captura correspondem ao momento da execução; julgamento posterior e conciliação constam em `../../reports/geracao_20261006_evidencias.json`, chave `conciliacao_gate_20261007`.
- Critério de cobertura satisfeito por19 aprovações anteriores mais aprovação complementar de E05 sob o mesmo contrato. São18 casos reais, E19 sintético e E20 controle local; sem taxa geral ou afirmação de disponibilidade/confiabilidade em produção.
- Resposta sobre atrasos com dez fontes originais e recusa P15 nesse contexto também aprovadas por Luiz; capturas e julgamentos em `../../reports/conferencia_corpus_real_20261007.md`. Na recusa, o provedor explica a falta de informação oficial, enquanto a aplicação mostra mensagem genérica: preservar essa distinção na apresentação.
- Liberação não autoriza novas chamadas, busca livre, mudança de modelo/timeout/repetição, publicação, commit ou push. CLI continua local sem geração. Preparação de README/roteiro e eventual implementação têm escopo próprio.
