# Brief para execução: PUBLICACAO-02 (licença, atribuição e ajustes do README)

> Decidido por Luiz em 20/10/2026, depois da auditoria de README-01 (`d36c652`) e PUBLICACAO-01.
> Opção escolhida: declarar licenças separadas no repo atual, **sem reescrever histórico** e sem remover arquivos.

## Contexto

- A página oficial do dataset no Kaggle informa **CC BY-NC-SA 4.0**. O repo tem trechos reais de avaliações em `data/eval/`, `reports/` e no próprio README (exemplo real, linhas ~164–166). A cláusula SA obriga as adaptações com esse texto a sair sob a mesma licença.
- Na auditoria, a varredura de PII com padrão formatado (e-mail, telefone, CPF, CNPJ, CEP) deu 0 nos arquivos rastreados de `data/` e `reports/`. Nomes próprios em texto livre não foram conferidos à mão. O mesmo texto já é público no dataset de origem, que já vem anonimizado da fonte. Luiz aceita esse risco residual, desde que fique declarado no README.

## Escopo (só estes arquivos)

1. `LICENSE` (novo): licença MIT para o **código** (`src/`, `tests/`, scripts), `Copyright (c) 2026 Luiz Maibashi`.
2. `LICENSE-DATA.md` (novo): declara que os arquivos derivados do dataset Olist que contêm texto de avaliação seguem **CC BY-NC-SA 4.0**. Conteúdo mínimo:
   - atribuição: título do dataset, autor (Olist), link da página do Kaggle já usada no README e link do legalcode `https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en`;
   - indicação de mudanças: o que este repo fez com os dados (documento por avaliação, limpeza mínima, seleção de casos e julgamentos), em 2–3 frases;
   - lista dos caminhos cobertos. Levante a lista com `git ls-files data reports` e marque **todo** arquivo que contém texto de avaliação. Use a lista com `*` do PUBLICACAO-01 como ponto de partida, mas confira cada um: arquivo novo que fique fora da lista sem justificativa conta como falha;
   - uso não comercial: o repo é trabalho acadêmico (FIAP) e portfólio.
   - CSV bruto e corpus processado continuam fora do Git; só derivados já rastreados entram na declaração.
3. `README.md`, quatro ajustes:
   1. **Nova seção `## Licença e atribuição`** (antes de `## Limites e entrega pendente` ou logo depois). Dizer: código em MIT (`LICENSE`), dados e trechos de avaliações em CC BY-NC-SA 4.0 com atribuição à Olist (`LICENSE-DATA.md`), e o risco residual de PII na mesma linha da conferência: padrões formatados zerados, nomes em texto livre não conferidos manualmente, texto idêntico ao dataset público de origem.
   2. **Linha ~42** ("Registre a revisão na avaliação final"): tirar o imperativo dirigido a nós. Procure no repo (`git grep -n "e8f8c21\|revision\|revisão dos pesos"`) se a revisão usada nas capturas foi registrada.
      - Se foi, cite a revisão e onde ela está registrada.
      - Se não foi, reescreva como limite, sem imperativo. A revisão no cache do PC de casa é `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` (`refs/main` em `~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2`). Pode citá-la só como "revisão no cache local em 20/10/2026", **sem afirmar** que foi a das capturas.
   3. **Linhas ~257–259:** a linha "Revisar o alerta de PyTorch..." vira um limite declarado: existe um alerta Dependabot de severidade baixa no PyTorch, não corrigido para preservar o ambiente da avaliação capturada. Apague a linha "Publicação do repo e vídeo de até 7 minutos ficam para a etapa de entrega."
   4. **Título do bloco pendente (linha ~262):** "E01–E20" vira "E01 a E20". Não mexa em mais nada dentro de `<!-- PENDENTE-GATE-0008 -->`.

Fora do escopo: reescrever histórico, remover arquivos, tornar o repo público, mudar código, mexer no bloco PENDENTE-GATE além do título.

## Regras de texto (README público, skill escrita-orgânica)

- Use **zero** travessão (`—`) e zero meia-risca (`–`) nas linhas novas ou alteradas do README e do `LICENSE-DATA.md`.
- Zero emoji. Nada de palavra de propaganda ("robusto", "abrangente", "crucial").
- Mesmo tom do README atual: frase curta, afirmação com limite explícito.

## Testes

- `git diff --check`.
- Links relativos novos existem (`LICENSE`, `LICENSE-DATA.md`).
- Contagem nas linhas alteradas do README: `—`/`–` = 0, emoji = 0. Informe o número.
- `LICENSE-DATA.md`: compare a lista de caminhos com os arquivos de `git ls-files data reports` que contêm texto de avaliação. Informe quantos estão cobertos e quantos ficaram de fora, com o motivo de cada um.

## Relatório (mesmo formato de README-01)

`TAREFA`, `ARQUIVOS` (com `git show --stat HEAD`), `TESTES`, `CRITÉRIO DE ACEITE`, `NÃO VERIFICADO`. Commit em Conventional Commits, **sem** `Co-Authored-By`; `git pull --rebase origin main` antes do push.

## Pronto quando

`LICENSE` e `LICENSE-DATA.md` existem; o README tem a seção de licença, não tem mais tarefa interna aparecendo e não tem travessão em linha alterada; o bloco PENDENTE-GATE está intacto, salvo o título.
