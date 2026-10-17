# Spec 0007 — Resposta gerada no CLI com prévia, hash e orçamento

**Data:** 2026-10-16. **Dono da aprovação (spec, merge e cada envio):** Luiz Maibashi.
**Status:** aprovada por Luiz em 2026-10-16; implementada com cliente falso
(263 testes passando), aguardando revisão do diff. Nenhuma chamada real feita.
**Origem:** item 2e da `docs/planejamento/MATRIZ_ENUNCIADO.md`.

## Objetivo

O enunciado (p. 6–7) exige demonstrar o fluxo pergunta → embedding → recuperação
→ contexto → geração → resposta fundamentada. Hoje `src/demo.py` só busca e
conta; a geração existe apenas no executor de avaliação curada. Sem essa ligação
a demo e o vídeo não mostram o pipeline pedido. Valor de negócio: o gestor faz
uma pergunta e recebe síntese com citações conferíveis, sem enviar comentário
não revisado a serviço externo nem estourar a cota gratuita.

## Decisões de Luiz (2026-10-16)

1. **Liberação:** prévia + hash por pergunta. A regra do `AGENTS.md` (contexto
   novo exige revisão e liberação explícita) permanece inalterada.
2. **Orçamento:** teto de 20 chamadas Gemini por dia UTC, contador local.
3. **Registro:** JSONL fora do Git em `data/demo/execucoes.jsonl`.

## Escopo

Incluído:

- Nova ação `--acao responder` em `src/demo.py`, aceitando `--pergunta`, `--k`
  e os filtros já existentes (`--nota-min`, `--nota-max`, `--situacao-entrega`).
- **Passo 1, prévia (padrão, sem API):** busca real; imprime pergunta, filtros
  efetivos, contexto exato que seria enviado (`review_id` + texto + score),
  alertas heurísticos de PII, chamadas restantes no dia e `sha256` do payload.
  Não lê credencial nem cria cliente Gemini.
- **Passo 2, envio:** `--executar --aprovacao-sha256 <hash>`. Recalcula o
  payload; hash diferente bloqueia sem chamar API. Com hash igual, usa
  `GeradorGemini(contexto_revisado=True)` envolvido por `GeradorComTentativas`
  (≤ 2 chamadas, política da ADR 0007) e `responder()`. Imprime status, texto,
  citações com texto integral de cada `review_id` citado, filtros e limites.
- **Hash** cobre: pergunta normalizada, k, filtros, lista ordenada de
  (`review_id`, texto), modelo, instrução, schema e limites de geração.
  Mudança em qualquer item exige nova prévia.
- **Alerta PII** (regex de e-mail, telefone, CPF/CNPJ, CEP): só informa e
  destaca; não bloqueia nem substitui a leitura humana (nome próprio passa).
- **Orçamento:** antes do envio, contar chamadas reais do dia UTC no JSONL;
  se `usadas + 2 > 20`, bloquear (reserva as 2 tentativas possíveis). Cada
  tentativa real registrada conta, inclusive falha.
- **Registro:** uma linha JSONL por execução real, com UTC, hash, pergunta,
  filtros, k, IDs do contexto, tentativas, status, texto, citações e digest do
  código. Gravar e dar flush do cabeçalho **antes** da API (trilha mesmo se o
  processo cair). `data/demo/` entra no `.gitignore`.
- **`--gerador falso`:** mesmo fluxo com gerador local identificado, sem chave,
  sem contador e sem hash obrigatório, para quem reproduz sem credencial.
  A saída marca `"modo": "simulado"`.

Fora do escopo:

- Perguntas de frequência pela geração (continuam em `--acao contar`; top-k
  não mede frequência).
- Filtros de período e categoria; reescrita da pergunta; interface web.
- Liberar o corpus em lote, mudar a regra de PII do `AGENTS.md` ou o modelo.
- Rodar chamada real durante a implementação: só testes com cliente falso.

## Critérios de aceitação (testes com cliente falso, sem rede)

1. Prévia nunca instancia cliente Gemini nem lê variável de credencial.
2. `--executar` sem `--aprovacao-sha256`, ou com hash divergente, sai com
   código ≠ 0 e zero chamadas ao cliente.
3. Hash igual + cliente falso válido → status `respondida`, citações ⊂ contexto,
   texto de cada citação exibido.
4. Cliente falso citando ID fora do contexto → `erro_geracao` (reuso de `responder`).
5. Cliente falso com `sem_evidencia` → recusa exibida como tal; exceção do
   cliente → `erro_geracao`, nunca apresentado como falta de evidência.
6. 19 chamadas já registradas no dia → bloqueio antes da API (19 + 2 > 20);
   registro de outro dia UTC não conta.
7. Linha JSONL gravada antes da chamada e completada depois; arquivo
   existente é anexado, nunca sobrescrito.
8. Alerta PII dispara para e-mail/telefone/CPF sintéticos e não bloqueia.
9. `--gerador falso` roda sem chave e marca modo simulado.
10. Suíte existente continua passando (`pytest`, `-W error::FutureWarning`).

## Restrições e riscos

- Texto livre de cliente vai a serviço externo no nível gratuito: o hash
  registra a liberação feita por Luiz; o agente não executa `--executar`
  sem ordem explícita na conversa. Conhecer o hash não concede autorização.
- Contador local é por máquina: não protege a cota se rodar em duas máquinas.
- Citação válida não prova suporte semântico (limite já declarado na spec 0001).
- Não alterar `geracao_casos.json`, votos, gabarito, P09, corpus nem relatórios
  históricos.

## Arquivos a tocar

`src/demo.py`, `src/rag/liberacao.py` (novo: payload, hash, alerta PII,
orçamento e registro), `tests/test_demo_responder.py` (novo), `.gitignore`,
`README.md` (seção da nova ação) e esta spec. Bridge só na frente TC4.

## Gates antes do commit

Revisão do diff por Luiz, `pytest` completo, quiz pós-implementação
(spec-governance etapa 4) e `/code-review`. Primeira chamada real só depois
do merge, com previsão registrada e autorização na conversa.
