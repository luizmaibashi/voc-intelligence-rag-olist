# ADR-0006 — Gemini 3.1 Flash-Lite como padrão do protótipo

**Data:** 2026-10-06. **Status:** Accepted para protótipo pelo Luiz no chat.
**Escopo:** substitui a escolha de modelo da ADR-0003; preserva seu contrato,
validação, recusa e revisão prévia do contexto.

## Contexto

No ensaio local de 06/10, três comentários reais curtos foram revisados e
liberados explicitamente, com IDs substituídos. O 3.5 recusou política oficial,
mas o resumo falhou com HTTP 504 em duas tentativas. O 3.1 retornou resumo citado
e recusa com as mesmas perguntas/contexto/configuração, em momento posterior.
Evidências: `../../reports/integridade_busca_cache.md`, seção smoke real.
São duas perguntas escolhidas, não uma estimativa de disponibilidade ou qualidade.

## Decisão e motivo

Definir `MODELO_GERACAO = "gemini-3.1-flash-lite"` em
`src/rag/provedor_gemini.py`. Preservar seleção explícita via
`GeradorGemini(modelo=...)`, sem fallback automático ou troca do provedor.

A decisão permite avançar a avaliação com o modelo que respondeu ao ensaio,
com alteração pequena e reversível. Não promete mais disponibilidade, precisão,
ROI financeiro ou economia de tempo medidos. Não alterar prompt/schema nesta
troca, para não misturar decisões sem evidência.

## Consequências e alternativas

- O cliente passa a pedir 3.1 quando não recebe modelo explícito; testes verificam
  o argumento enviado e a possibilidade de selecionar 3.5.
- Persistem erros de serviço, dependência externa e risco de afirmação sem suporte.
  Citação válida não prova fidelidade; próxima etapa é avaliação da spec 0006.
- Manter 3.5 como padrão: possível, mas falhou no resumo escolhido neste ensaio.
- Trocar provedor ou instalar modelo local: não necessário para esta alteração;
  reavaliar se os ensaios ampliados não conseguirem concluir com qualidade.
- Retry/fallback automático: adiado; ocultaria instabilidade sem limite de custo
  e critério definidos. Falhas continuam visíveis como `erro_geracao`.

## Critérios de validação e revisão

`test_adaptador_envia_contexto_e_schema_sem_rede` deve conferir padrão 3.1 e
override 3.5. Suíte na venv deve passar. Testes usam cliente falso e não comprovam
API disponível; saídas reais do smoke estão no relatório.

Ao finalizar a rodada da spec 0006, revisar a decisão se houver afirmação sem
suporte, recusa inadequada ou falhas de serviço que impeçam a demonstração.
Não liberar comentários adicionais por consequência desta escolha: aprovação
continua restrita às três frases registradas, até revisão de novos contextos.

## Referências

- ADR-0003 e specs 0001, 0004, 0006.
- [Modelo 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite).
- [Termos de uso](https://ai.google.dev/gemini-api/terms): observar o nível de serviço.
