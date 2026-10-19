# Brief para execução — citação por afirmação (experimento)

> Decidido por Luiz em 18/10/2026 na aula 0003 (`docs/aprendizado/licoes/0003-saida-estruturada-formato-nao-verdade.html`). Este brief traz só decisões tomadas; o desenho de detalhe vai em spec aprovada por Luiz antes do código (skill `spec-governance`).

## Decisão

Trocar a citação **por resposta** (`review_ids` para o texto inteiro) por citação **por afirmação** (`afirmacoes: [{frase, review_ids}]`).

- **Por quê:** auditoria par a par — localizar onde a resposta erra e agir no ponto exato. Rastreabilidade pedida no enunciado.
- **O que NÃO compra:** correção. Schema garante formato, não verdade (workshop Anwar L1815; doc Gemini Structured output: validar valores na aplicação). `responder.py:50` continua provando só que o id estava no contexto. Nenhum texto do projeto (README, vídeo, ADR) pode dizer que a resposta ficou "mais certa".

## Regras do experimento (MISSAO: complexidade só como hipótese testável)

- **Baseline:** antes de qualquer edição, criar a tag `cfg-citacao-por-resposta` no commit atual. Hashes, as 2 respostas aprovadas (`reports/demo_cli_20261017.md`) e o gate E01–E20 seguem válidos para ela.
- **Critério de abandono:** se até **25/10/2026** o gate E01–E20 da configuração nova não estiver julgado e aprovado, a entrega volta para `cfg-citacao-por-resposta`. O ADR registra o abandono com o motivo; README e vídeo usam a configuração da tag.
- **Orçamento:** teto local de 20 chamadas/dia UTC continua; a rodada julgada (~20+ chamadas) cabe em ≥ 2 dias. Não contornar o teto.
- **Predição antes da medição:** antes da rodada julgada, pedir a Luiz que preveja quantos de E01–E20 terão todas as afirmações sustentadas. Registrar a previsão antes de rodar.
- Proporções sempre com `n` e intervalo.

## Ordem de execução

1. Tag `cfg-citacao-por-resposta` (push da tag e do `76dc654`: decisão de Luiz).
2. **ADR 0008** `docs/adr/0008-citacao-por-afirmacao.md`, com a tabela "garante / não garante" de `Base_de_Conhecimento/metodologia/AI_ENGINEERING/20_llm_auditavel_roi.md`: contexto (limite de `responder.py:50`), decisão, alternativas (seguir / por afirmação / conferência manual só no vídeo), custo (engenharia + chamadas + rejulgamento por Luiz), critério de abandono, frase "saída estruturada garante formato; quem garante a veracidade é a avaliação" com fonte.
3. **Spec 0008** (ou revisão de 0001/0006), aprovada por Luiz antes do código: contrato `afirmacoes[]`; o que acontece com `texto` e com `sem_evidencia`; validação por par (frase não vazia, ≥ 1 id, todo id no contexto, senão `erro_geracao`); como o gate julga frase a frase.
4. Código: `SCHEMA_RESPOSTA` e `INSTRUCAO` em `src/rag/provedor_gemini.py`; validação em `src/rag/responder.py`; CLI e registro. Testes com cliente falso, incluindo id fora do contexto em uma afirmação só. Teste estrutural não prova suporte: dizer isso no teste/docstring.
5. Previsão de Luiz → rodada julgada E01–E20 frase a frase (Luiz julga) → resultado com `n` e IC.
6. Só com gate aprovado: README (seção de limites), roteiro do vídeo com uma resposta auditada par a par. Se abandonar: README atual + conferência manual frase a frase de uma resposta aprovada no vídeo.

## Pronto quando

Gate novo aprovado até 25/10 **ou** abandono registrado no ADR 0008 e entrega na tag — os dois são saídas válidas do experimento.
