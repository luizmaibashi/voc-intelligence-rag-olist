# ADR-0005: Regras locais como baseline de temas elogiados

**Data:** 2026-09-28. **Status:** Accepted para protótipo; ranking do corpus pendente.
**Proposto por:** Luiz Maibashi.

## Contexto e decisão

P09 pergunta quais aspectos da entrega são mais elogiados. A contagem de
metadados do ADR-0004 não identifica o aspecto escrito no comentário. A chave
Gemini atual é gratuita e a geração segue indisponível; comentários podem
conter dados sensíveis. Usar regras locais determinísticas como primeiro
baseline em `src/analytics/elogios_entrega.py`. A avaliação independente,
incluindo textos mistos e negativos, decide se as contagens podem ser exibidas.

ROI: permite depurar critérios de negócio e produzir uma referência barata,
sem chamadas externas. O custo é cobertura limitada de linguagem livre;
portanto, nenhuma frequência final será alegada antes da avaliação.

## Alternativas

| Caminho | Decisão |
|---|---|
| Top-k do RAG | Rejeitado: não representa frequência no corpus. |
| Gemini gratuito para classificar tudo | Rejeitado agora: serviço indisponível e revisão de dados pendente. |
| Classificador treinado nos 100 rótulos do agente | Adiado: rótulos não são gabarito humano e temas raros têm poucos exemplos. |
| Regras locais | Escolhidas como baseline interpretável, sujeitas a teste fora da amostra. |

## Falsificação

`classificar_elogio` falha como base de ranking se confundir reclamação com
elogio, perder sistematicamente grafias comuns ou inverter a ordem dos temas
na amostra revisada. Registrar erros por tema antes de alterar as regras.

## Evidência inicial

Após corrigir erros observados na primeira amostra fora do desenvolvimento,
uma segunda amostra nova (`seed=20261001`, n=100) teve 26 marcações da regra,
32 elogios claros na triagem do agente e 1 caso limítrofe que Luiz decidiu
não contar como elogio. Contra os rótulos provisórios:
6 elogios perdidos e 0 falsos positivos entre as 26 marcações. As duas
rodadas e suas versões estão em `data/eval/p09_validacao_agente.csv`.
Esses rótulos **não são gabarito humano**; o gate para divulgar ranking continua
pendente.
