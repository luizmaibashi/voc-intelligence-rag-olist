# Brief para execução: REVERTER-01 + README-02 (main coerente com a entrega na tag)

> Decidido por Luiz em 20/10/2026, depois do abandono da citação por afirmação (ADR 0008, `004a1f8`: gate 19/20, E17 regrediu).
> A entrega é a configuração da tag `cfg-citacao-por-resposta` (`fe652b6`). Hoje o `main` ainda tem o código da configuração abandonada; quem clonar e seguir o README rodaria a configuração reprovada.

## Pré-condição

**Só comece depois que o VALIDAR-01 estiver no `origin/main` e auditado pelo Claude**, e depois que a ficha oficial E01 a E20 estiver commitada em `reports/`. As duas tarefas mexem em `tests/` e o VALIDAR-01 altera `src/eval/ficha_julgamento.py`. Se a pré-condição não valer, pare e reporte.

## Tarefa 1: REVERTER-01

### O quê

Fazer o código de geração no `main` voltar a se comportar como a tag, sem apagar a trilha do experimento.

1. **Tag de preservação antes de mexer:** `cfg-citacao-por-afirmacao-abandonada` no commit atual do `main` (já com a ficha oficial), com push da tag. É ali que as capturas da fase 1 e da fase 2 continuam reproduzíveis com o hash `203ec986…`.
2. **Restaurar da tag** (`git checkout cfg-citacao-por-resposta -- <arquivo>`), não `git revert`, para o estado final ficar explícito por arquivo:
   - `src/rag/provedor_gemini.py`, `src/rag/responder.py`, `src/demo.py`, `src/eval/avaliar_geracao.py`;
   - `tests/test_avaliar_geracao.py`, `tests/test_demo.py`, `tests/test_demo_responder.py`, `tests/test_reavaliar_e05.py`, `tests/test_responder.py`;
   - remover `tests/test_citacao_afirmacao.py` (não existe na tag).
3. **Manter, sem restaurar:** `src/eval/ficha_julgamento.py`, `tests/test_ficha_julgamento.py`, `scripts/copiar_julgamentos.py`, `tests/test_copiar_julgamentos.py` (ferramenta de julgamento: só lê capturas e não importa nada de `src/`), toda a pasta `docs/`, `reports/`, `data/eval/`, `LICENSE`, `LICENSE-DATA.md`.
4. Antes de restaurar, liste com `git diff --stat cfg-citacao-por-resposta main -- src tests requirements.txt` todo arquivo que difere da tag. **Arquivo que difere e não aparece nas listas dos itens 2 e 3: pare e reporte**, não decida sozinho.

### Testes

- Suíte completa com o comando do README (basetemp novo). Informe passou/falhou e a contagem.
- Hash do lote sem API: `$env:PYTHONPATH = '.venv/sdk175'; python -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json --repetir-transitorios`. Informe o hash impresso.
  - Compare com o hash da rodada 04 da baseline registrado na spec 0008 (`8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0`).
  - Se forem diferentes, mostre qual campo de `configuracao_geracao()` explica a diferença (por exemplo `versao_sdk`). Não force igualdade.
- `python -m src.demo --acao ensaio-sintetico` roda e mostra citação por resposta, não `afirmacoes`.
- **Zero chamada de API.** Não use `--executar`.

### Commit

`revert(rag): restaurar geração da tag cfg-citacao-por-resposta`, com corpo citando ADR 0008 e a tag de preservação.

## Tarefa 2: README-02

Commit separado, depois da tarefa 1.

1. **Bloco `<!-- PENDENTE-GATE-0008 -->`:** remova os marcadores e as duas variantes. No lugar, crie a seção `### Experimento: citação por afirmação (abandonado)` com, no máximo, um parágrafo curto e uma lista, tudo tirado do ADR 0008 (seção "Resultado e decisão"):
   - o que foi testado: cada frase ligada aos próprios `review_id`, para localizar uma alegação errada;
   - resultado: 19/20 casos aprovados no julgamento humano (IC95% Wilson 76,4% a 99,1%); 0 falha de contrato em 19 julgáveis (IC95% 0% a 16,8%); casos escolhidos intencionalmente, não estimativa geral;
   - por que saiu: E17 ("A entrega foi elogiada neste contexto?") recusou, quando a configuração da tag respondia com a crítica citada; recusa com evidência disponível conta como perda de cobertura;
   - hipótese não testada para E17 (pergunta negativa contra o contrato por afirmação), dita como hipótese;
   - onde está: tag `cfg-citacao-por-afirmacao-abandonada`, ADR 0008, spec 0008, ficha oficial em `reports/`.
2. **Números do gate da entrega:** para a configuração entregue, cite o resultado do gate histórico como está registrado em `docs/spec/0006-avaliacao-geracao.md` e `reports/revisao_geral_20261007.md`, com numerador, `n`, IC95% e limite de seleção. **Não calcule número novo nem arredonde diferente da fonte.** Se a fonte não tiver IC, calcule Wilson, diga que calculou e mostre a conta no relatório.
3. **Seção "Reprodução sem credencial e reprodução de capturas":** troque o hash `203ec986…` pelo hash que a tarefa 1 imprimiu e diga a qual configuração ele pertence. As capturas da configuração abandonada passam a ser reproduzíveis só na tag de preservação: diga isso em uma frase.
4. **Tabela "Decisões técnicas", linha da ADR 0008:** troque "Citação por afirmação em experimento" por uma linha que diga que foi testada e abandonada (19/20, regressão em E17), com o link.
5. **Linha ~43:** troque "[um teste de cache](reports/integridade_busca_cache.md)" por "[relatório de integridade do cache](reports/integridade_busca_cache.md)".
6. **Varredura de coerência:** `git grep -n "afirmac\|afirmaç" README.md`. Tudo que descrever a citação por afirmação como comportamento atual do CLI deve virar passado ou sair. Liste cada linha alterada no relatório.

### Regras de texto (README público, skill escrita-orgânica)

- Use **zero** travessão (`—`) e zero meia-risca (`–`) nas linhas novas ou alteradas. Para intervalo, escreva "a" ("76,4% a 99,1%").
- Zero emoji, nada de palavra de propaganda ("robusto", "abrangente", "crucial"). O abandono é resultado de experimento, não fracasso nem vitória: escreva os números com o limite ao lado.
- Mesmo tom do README atual.

### Testes

- `git diff --check`; links relativos novos existem; a tag citada existe no remoto.
- Contagem nas linhas alteradas: `—`/`–` = 0, emoji = 0. Informe o número.
- `git grep -n "PENDENTE-GATE" README.md` não retorna nada.

## Relatório (formato de README-01)

Um bloco por tarefa: `TAREFA`, `ARQUIVOS` (`git show --stat` de cada commit), `TESTES`, `CRITÉRIO DE ACEITE`, `NÃO VERIFICADO`. Conventional Commits, **sem** `Co-Authored-By`; `git pull --rebase origin main` antes de cada push. Não torne o repo público.

## Pronto quando

O `main` gera respostas como a tag, a suíte passa e não houve chamada de API. A tag de preservação existe no remoto. O README descreve a configuração entregue, registra o experimento abandonado com números, `n` e IC, e não tem mais bloco pendente nem travessão em linha alterada.
