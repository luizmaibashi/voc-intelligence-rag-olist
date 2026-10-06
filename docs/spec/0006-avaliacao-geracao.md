# Spec 0006 — Avaliação exploratória de resposta e recusa

**Data:** 2026-10-06. **Dono:** Luiz Maibashi.
**Status:** curadoria proposta e implementação do executor aprovadas no chat;
revisão humana dos critérios, envio novo e execução pendentes.
Esta spec não libera produção nem novos comentários.

## Objetivo e fronteira

Verificar se o gestor recebe informação sustentada pelos comentários, pode
conferir a fonte e é informado quando faltam evidências. Separar recuperação,
geração e falha de serviço. Padrão do protótipo: Gemini 3.1 (ADR-0006).
Não medir frequência temática por top-k, reabrir P09 ou treinar classificador.

## Plano de 20 casos

Perguntas abaixo são propostas. O esperado das candidatas respondíveis só será
confirmado depois de localizar e revisar evidência; ausência de evidência deve
ser registrada, nunca resolvida inventando comentário ou forçando rótulo positivo.
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
| E17 | A entrega foi elogiada neste contexto? | Contexto de reclamação/lentidão; não inverter polaridade. |
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
   de serviço. Só as 3 frases E01 estão liberadas hoje; novos contextos continuam pendentes.
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
- Revisão semântica fica pendente em todos os casos; nenhuma automação libera
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

Executor implementado/testado; gate semântico permanece **pendente** até leitura
e julgamento das respostas por Luiz. Esta versão registra `erro_integracao.fase`
como `gerador` ou `validacao_aplicacao`; exceção na validação não vira automaticamente
falha de disponibilidade da API. Compatibilidade de status é só verificação estrutural.

O ajuste de robustez do núcleo foi autorizado, implementado e testado: status
que não é string retorna `erro_geracao` antes de consultar os estados permitidos.
Próximo: Luiz revisa o manifesto/payloads e critérios e registra previsão/liberação antes
da rodada. Resultados estocásticos são preservados localmente; revisar dados/conteúdo
antes de versionar e registrar as notas humanas.

Referências: specs 0001/0002/0004, ADR-0006 e `reports/integridade_busca_cache.md`.
