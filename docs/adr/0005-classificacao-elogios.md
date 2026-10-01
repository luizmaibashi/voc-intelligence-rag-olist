# ADR-0005: Regras locais como baseline de temas elogiados

**Data:** 2026-09-28. **Status:** Congelado em 2026-10-01; liberada só a
liderança de prazo/rapidez, ordem completa bloqueada (ver seção final).
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

## Revisão da rubrica em 2026-09-28

Na rodada humana 3 (25 comentários, amostra balanceada pelas previsões da regra),
Luiz definiu que um elogio geral explícito pode coexistir com atributo
específico. Exemplo de contrato: "entrega excelente e rápida" recebe
`elogio_geral` e `prazo_rapidez`. A implementação anterior só atribuía
`elogio_geral` quando nenhum outro tema havia sido encontrado; a condição foi
removida. O arquivo exportado pelo Luiz fica fora do repositório até revisão
de notas livres e PII; a comparação usa somente IDs e rótulos.

A rodada 3 revelou muitos desacordos nos quatro temas e, por ter motivado
este ajuste, passa a ser diagnóstico de desenvolvimento. Uma nova amostra
humana, independente da mudança, é necessária antes de qualquer ranking.

## Fronteira entre elogio observado e satisfação inferida

Na decisão humana da rodada 3, Luiz considerou que uma avaliação somente
positiva permitia inferir boa experiência em todos os aspectos, mesmo sem
menção individual. Para P09, essa inferência inflaria os quatro temas em
conjunto e deixaria de responder quais aspectos foram **elogiados no texto**.
Luiz decidiu preservar a inferência como leitura separada e manter o ranking
P09 restrito aos aspectos explicitamente elogiados. Elogio apenas ao produto
não conta como elogio à entrega. Essa decisão mantém o baseline explicável;
o custo é não capturar satisfação implícita no ranking de temas.

Os votos da rodada 3 foram produzidos sob a rubrica anterior e não medem
precisão ou revocação do classificador para a pergunta P09. O teste seguinte
deve usar casos novos e instruções de rotulagem que distingam elogio observado
de inferência de boa experiência.

A nota de cinco estrelas e a ausência de reclamação são sinais possíveis de
satisfação geral, não evidência de elogio textual a cada atributo. A leitura
de satisfação poderá ser analisada separadamente; usá-la como rótulo P09
inflaria os temas em conjunto. Um elogio somente ao prazo não cria
`elogio_geral` sem avaliação explícita da entrega como um todo.

## Congelamento em 2026-10-01

Com 31 dias até a entrega e P09 fora dos requisitos obrigatórios do enunciado
(que exige resposta com evidências, não ranking validado), Luiz decidiu parar a
validação quando mais rótulos deixassem de mudar a decisão. O teste em
`reports/p09_resultado_amostra_independente.md` mostrou prazo/rapidez em 1º na
regra e nos rótulos humanos, e nenhuma avaliação da amostra com elogio geral sem
elogio ao prazo. A liderança é publicável; a ordem do 2º ao 4º não, porque a
regra subestima elogio geral (revocação 1/16).

Custo aceito: P09 não terá ranking completo. Reabrir somente se a demo precisar
da ordem completa; nesse caso, ampliar `GERAL` e repetir a amostra independente.
