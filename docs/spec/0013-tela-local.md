# Spec 0013 — Tela local sobre o CLI, sem mudar os hashes liberados

**Status:** pronta para implementar · **Data:** 2026-10-23 · **Branch:** `tela-local` (a partir de `193c05d`)
**Implementa:** Codex · **Audita:** Claude (até 29/10) · **Aceite final:** Luiz, em casa, 31/10 de manhã
**Decisão registrada em:** ADR 0010 (rascunho na base de conhecimento, `docs/tc4/ADR_RASCUNHO_tela_local.md`)

## Problema

O vídeo mostra prévia → leitura do contexto → liberação por hash → resposta com fontes. No
terminal esse controle humano aparece mal. A tela substitui o trecho do CLI no vídeo. Ela é
uma casca: toda regra continua em `src/demo.py` e `src/rag/`.

## Restrição dura (motivo do desenho)

O hash de liberação cobre `src/demo.py`, `src/rag/liberacao.py`, `src/rag/responder.py`,
`src/rag/provedor_gemini.py`, `src/rag/tentativas.py`, a configuração de geração (inclui a
versão do `google-genai`) e o contexto recuperado (`src/rag/liberacao.py:14`,
`src/eval/avaliar_geracao.py:88`). Os hashes liberados (spec 0012) precisam sair **iguais**
pela tela:

| Caso | Pergunta | Filtros | Hash |
|---|---|---|---|
| E-A | O que os clientes relatam sobre entregas atrasadas? | `nota_max=2`, `situacao_entrega=atrasado`, `k=10` | `28fb0e20214f31f163156580e6a1f3fddfcd18c6fa71fc890e5a607506b40a88` |
| E-B | O que os clientes relatam que aconteceu depois que a entrega atrasou? | idem | `72ea2402264ac2f80a6a7c3ea043a10de4b72209b6eddb07f53b2c1435bf68ec` |
| P15 | Qual é o prazo oficial de reembolso da Olist quando uma entrega atrasa? | idem | `c53daa6570b52c72f4a9b289b7ae87d21be989beac77b7af34f9c729a8684e24` |

Portanto **é proibido editar**: os 5 arquivos acima, `src/retrieval/`, `src/eval/avaliar_geracao.py`,
`src/analytics/`, `requirements.txt`, `data/eval/`. Importar deles é permitido, inclusive
nomes com `_` (`_criar_gerador`, `liberacao._ler_registro`).

## O que construir

Arquivos novos, e só eles:

- `src/tela/__init__.py`
- `src/tela/logica.py`: funções puras, sem Streamlit, testáveis.
- `src/tela/app.py`: a interface Streamlit.
- `scripts/paridade_tela.py`: confere os 3 hashes pelo mesmo caminho que a tela usa.
- `tests/test_tela_logica.py`
- `requirements-app.txt`
- uma seção curta no `README.md` ("Tela local"), com o comando de instalação e execução.

### `logica.py`

1. `argumentos_responder(pergunta, k, nota_min, nota_max, situacao, categoria, compra_de, compra_ate) -> dict`:
   normaliza a entrada da tela para **exatamente** os kwargs que o `main` do CLI passa a
   `responder_cli`. `k` sai como `int` (o `st.number_input` pode devolver float), campos vazios
   saem `None` (nunca `""`, `0` ou `"Todos"`), datas como `AAAA-MM-DD`. Esse é o ponto onde a
   paridade de hash quebra se errar: `{"k": 10.0}` e `{"k": 10}` geram hashes diferentes.
2. `chave_entrada(args: dict) -> str`: identidade estável da entrada. A tela guarda a prévia
   junto com essa chave; se a entrada mudar, a prévia é descartada e o envio fica bloqueado.
3. `resumo_execucoes(linhas: list[dict]) -> dict`: a partir de `data/demo/execucoes.jsonl`
   (lido com `liberacao._ler_registro`), conta as tentativas (`tipo == "tentativa"`), as
   tentativas com `erro_integracao` verdadeiro e a mediana de `duracao_ms` das sem erro. A taxa
   de erro sai com n e IC95% de Wilson (`statsmodels.stats.proportion.proportion_confint`,
   `method="wilson"`), como já é feito no projeto. Também conta os resultados por `status`.
   Linhas de outros formatos (por exemplo, com `classe_operacional`) são contadas à parte, nunca
   descartadas em silêncio.

### `app.py` (Streamlit, só local)

- `st.cache_resource` para `carregar_modelo()` e `carregar_corpus(...)`; usar
  `CACHE_VETORES`, `REGISTRO_PADRAO` e `_criar_gerador` de `src.demo`, como o `main` do CLI.
- **Aba "Investigar"**
  - Entradas: pergunta; nota mínima e máxima (vazio = sem filtro); situação da entrega;
    categoria; período de compra; `k` (padrão 10).
  - Botão "Gerar prévia": `responder_cli(..., executar=False)`. Mostra a tabela do contexto
    (ID, texto, nota, situação, score), os alertas de PII, as chamadas restantes no dia e o
    hash em destaque. Mostra também o aviso de que nada foi enviado.
  - Seletor de gerador: `gemini` ou `falso`. Com `falso`, um botão "Simular" chama o gerador
    falso e a saída diz "simulado" em destaque.
  - Envio real: campo "Cole o hash da prévia" + caixa "Li o contexto e nada identifica o
    cliente" + botão "Enviar ao Gemini". O botão só habilita com a caixa marcada, a prévia válida
    para a entrada atual e o campo preenchido. A tela passa o **texto colado**, não o hash da
    prévia: quem compara é `responder_cli`. Hash errado mostra a mensagem de `EnvioBloqueado`
    e nenhuma chamada acontece.
  - Resultado: status (`respondida`, `sem_evidencia`, `erro_geracao`), texto, IDs citados e
    texto integral de cada fonte citada, e o aviso "citação válida não prova suporte".
- **Aba "Contagem"**: `quantificar(corpus)`: atrasadas, total, proporção, IC95% e período,
  com os limites (`LIMITES`).
- **Aba "Execuções"**: somente leitura, `resumo_execucoes` + tabela das últimas execuções.
- Nada de chave na tela. Fonte legível no vídeo (tema padrão do Streamlit, layout `wide`).
- Falha local (corpus ou pesos ausentes) mostra a mesma orientação do CLI, sem stack trace.

### `scripts/paridade_tela.py`

Para E-A, E-B e P15: monta os argumentos por `argumentos_responder`, chama
`responder_cli(executar=False)` com o corpus e o modelo reais e compara com os hashes da tabela.
Imprime `ok`/`DIVERGE` por caso; código de saída 1 se algum divergir. Não chama a API.

### `requirements-app.txt`

Só `streamlit==<versão>`. Escolha a versão estável mais nova publicada **há pelo menos
14 dias** no dia da instalação, e registre a data no README. Instale assim:

```powershell
python -m pip freeze > .venv/constraints-tela.txt
python -m pip install -r requirements-app.txt -c .venv/constraints-tela.txt
python -m pip check
```

Se o instalador precisar mudar qualquer pacote já instalado (`numpy`, `torch`, `protobuf`,
`pandas`, `pyarrow`, `google-genai`...), **pare e reporte**: não relaxe a restrição.

## Critérios de aceite

1. `git diff --name-only main...tela-local` lista só os arquivos novos acima e o `README.md`.
2. A suíte inteira passa sem alteração nos testes existentes, mais `tests/test_tela_logica.py`, cobrindo:
   `k` float → int; vazios → `None`; mesmos kwargs do CLI para E-A; mudança de qualquer campo
   muda `chave_entrada`; `resumo_execucoes` com fixture (taxa e IC; mediana só das sem erro;
   linhas de formato desconhecido contadas à parte).
3. `pip check` limpo e `pip freeze` igual ao de antes, exceto pelo Streamlit e suas dependências novas.
4. Em casa, com corpus e pesos: `python -X utf8 scripts/paridade_tela.py` imprime `ok` nos 3
   casos. **Sem isso, a tela não entra no vídeo** (vale o CLI).
5. Prévia de E-A pela tela, conferida a olho: mesmo hash e mesmos 10 IDs do CLI.

## Fora de escopo

Hospedagem, login, multiusuário, API, busca híbrida (ADR 0009: não adotada), reranker,
qualquer refatoração de `src/demo.py` e mudança de texto do prompt.

## Como rodar (para o README)

```powershell
$env:PYTHONPATH = '.venv/sdk175'
python -m streamlit run src/tela/app.py
```

A primeira carga lê o corpus e o cache de vetores; o envio ao Gemini continua exigindo a
chave no ambiente e respeita o teto diário (spec 0007).
