# ADR-0008 — Citação por afirmação como experimento reversível

**Data:** 2026-10-18. **Status:** experimento e contrato da spec 0008 aprovados por Luiz em 18/10/2026; implementação local sem API pronta para revisão, gate novo pendente. **Baseline:** tag publicada `cfg-citacao-por-resposta` no commit `fe652b6`.

## Contexto e valor

O contrato atual devolve `texto` e uma lista de `review_ids` para a resposta inteira. `src/rag/responder.py` confere que cada ID pertence ao contexto, mas não liga uma frase específica à sua fonte nem prova suporte semântico. Nas duas respostas reais da demo, Luiz aprovou o conteúdo após conferência manual; E-A citou 10/10 fontes e E-B, 5/10 (`reports/demo_cli_20261017.md`). A unidade de auditoria ainda é a resposta inteira.

Para o gestor, localizar exatamente a frase problemática reduz o esforço de conferência e permite corrigir o ponto errado. Esse ganho operacional é uma **hipótese**, sem tempo de revisão ou ROI medido. A rastreabilidade atende ao enunciado; a veracidade continuará dependendo da avaliação.

## Decisão

Experimentar saída estruturada `afirmacoes: [{frase, review_ids}]`, com ao menos uma fonte por afirmação respondida. A aplicação monta o texto exibido apenas dessas frases. O campo `limitacao` do provedor é registrado, mas ignorado em `respondida` e nunca exibido como fato; `sem_evidencia` mantém mensagem local fixa e lista vazia. A aplicação validará a estrutura e se os IDs estão no contexto; Luiz julgará, frase a frase, se as fontes sustentam o conteúdo. A instrução pede uma alegação por item, sem garanti-la. A spec 0008 define o contrato executável e as mudanças em CLI, registro e avaliador.

> Saída estruturada garante formato; quem garante a veracidade é a avaliação.

Fonte da formulação e da tabela abaixo: `metodologia/AI_ENGINEERING/20_llm_auditavel_roi.md`, baseada no workshop Anwar Hermuche (17/10/2026, transcrição L1814–1826) e na documentação de [saída estruturada do Gemini](https://ai.google.dev/gemini-api/docs/structured-output), que orienta validar valores na aplicação.

| Camada | Garante | Não garante |
|---|---|---|
| Schema/enum do provedor | Forma pedida e estados permitidos, quando o provedor a respeita | Verdade ou suficiência da fonte |
| Validação em `responder()` | Frase não vazia, ID presente no contexto, vínculo explícito frase–IDs | Que o comentário citado sustenta a frase ou que há só uma alegação |
| `temperature=0` | Menor variação pretendida | Texto idêntico entre execuções |
| Hash de configuração e registro | Qual configuração e saída foram usadas | Qualidade da saída |
| Instrução no prompt | Regra solicitada ao modelo | Obediência garantida |
| Gate E01–E20 julgado por Luiz | Resultado nos casos e afirmações julgados, com `n` e intervalo quando houver proporção | Generalização para perguntas novas ou operação real |

## Alternativas e custo

| Opção | Benefício | Limite / decisão |
|---|---|---|
| Seguir com citação por resposta | Zero engenharia e gate já aprovado | Conferir suporte exige reler a resposta e distribuir fontes manualmente; fica como baseline recuperável. |
| Citação por afirmação | Erro localizável no par frase–fonte | Exige schema, prompt, validação, CLI, registros, testes e rejulgamento humano; escolhida como experimento. |
| Conferência manual só no vídeo | Demonstra uma resposta bem auditada com baixo custo | Não muda o contrato da ferramenta; alternativa de entrega se o experimento for abandonado. |

O custo inclui engenharia e testes em vários módulos, cerca de 20 ou mais chamadas para a rodada julgada distribuídas em pelo menos dois dias sob o teto local de 20 chamadas/dia UTC, e o tempo de Luiz para julgar cada afirmação. JSON por afirmação pode atingir o limite atual de 512 tokens; `finish_reason` será registrado quando disponível, sem inferir truncamento de todo JSON inválido. Alterar o limite muda o hash e exige decisão explícita. Não há estimativa monetária ou de horas validada. O teto não será contornado.

## Validação, abandono e retorno

Antes de medir a nova configuração, Luiz prevê quantos casos E01–E20 terão **todas** as afirmações sustentadas e quantas falhas de contrato ocorrerão; registrar ambas antes das chamadas. Levantar `B/n_julgáveis` das primeiras tentativas históricas com schema e instrução iguais aos da tag; se não houver rodada integralmente equivalente, declarar diferenças. Falhas de serviço sem saída saem do denominador, com exclusões explícitas. A comparação de contrato usa somente casos julgáveis em ambas as configurações (`B_pareado`, `N_pareado`, `n_pareado`); não compara diretamente a régua semântica nova por frase com a régua antiga por resposta.

Luiz definiu a ordem da rodada em 18/10/2026: concluir primeiro os 13 pareáveis (`E02,E03,E04,E06,E07,E08,E09,E10,E11,E12,E14,E15,E18`), atravessando dias se a cota exigir. Se `N_pareado ≥ 3` ao concluir essa fase, registrar abandono aqui com `N`, os 13 casos atribuídos, `n_julgáveis`, exclusões por falha de serviço e IC95% calculado sobre os julgáveis; a entrega volta à tag. Se `N_pareado < 3`, executar os sete restantes (`E01,E05,E13,E16,E17,E19,E20`) e parar no total de cinco falhas de contrato. Esses limiares são tolerância de custo definida antes da medição, não significância estatística. Falha de serviço não entra na parada de contrato e pode exigir reavaliação autorizada, sempre sob o teto. A avaliação preserva as saídas históricas e registra para cada afirmação os IDs e o julgamento humano. Uma proporção publicada traz numerador, `n`, IC95% e o limite de seleção intencional. Citação estruturalmente válida não aprova um caso. Cronometrar auditoria da configuração nova e da tag é opcional; sem medição, redução de tempo segue hipótese.

**Baseline observado:** Luiz previu cerca de 4 falhas antes da apuração; a primeira tentativa da rodada 04, sob schema e instrução da tag, teve `B=0/13` saídas julgáveis (IC95% Wilson [0%; 22,8%]). Seis casos tiveram falha de serviço na primeira tentativa e E20 é controle local. IDs e fonte exatos constam na spec 0008. O limiar pareado aplicável é três falhas nos IDs julgáveis do baseline; o limite absoluto segue cinco.

**Previsões da configuração nova, registradas antes das chamadas:** Luiz prevê 17/20 casos com todas as afirmações sustentadas e `N=3` falhas de contrato. A previsão não aprova o gate nem substitui a contagem observada.

**Execução parcial em 19/10 UTC:** o primeiro envio da fase pareável parou no teto local de 20 chamadas após dez casos, todos sem saída por `ConnectError`. Diagnóstico direto: DNS negado no ambiente padrão e resolvido fora da restrição; isso não demonstra falha do Gemini. E14, E15 e E18 não foram chamados. Portanto, a fase 13/13 e o limiar `N≥3` ainda não foram julgados; não há decisão de abandono antecipado. Captura e denominadores constam em `reports/geracao_citacao_afirmacao_fase1_20261019.md`.

**Continuação autorizada por Luiz:** uma reavaliação dos dez casos sem saída e a primeira execução de E14/E15/E18, mantendo o hash, o contexto, a política de repetição e 20 chamadas/dia UTC. Antes do envio, DNS e TLS do host Gemini serão testados sem API no mesmo ambiente de rede; falha interrompe a rodada antes do ledger. A captura de 19/10 permanece intocada. Janela da fase 1: 20/10 UTC; fase 2, somente se `N<3`: 21/10 UTC; julgamento humano: 22–23/10. Prazo final: 25/10.

**Operação manual e publicação:** Luiz executará a fase 1 exclusivamente neste PC em 20/10 UTC, antes das 21:00 locais. Agendamentos foram cancelados: o PC fica desligado e o sandbox padrão bloqueou DNS. O ledger de cota fica nesta máquina; nenhuma outra enviará chamadas. Ao terminar a fase 1 e registrar `N`, `n_julgáveis`, IC e decisão de parada, fazer commit e push de código, testes, spec/ADR 0008, `docs/aprendizado/MISSAO.md` e relatórios/capturas da fase 1. O julgamento poderá ocorrer na outra máquina após `git pull`, sem chamadas de API nela.

**Critério de abandono:** se até **25/10/2026** o gate E01–E20 da configuração nova não tiver **20/20 casos resolvidos, julgados por Luiz e sem frase sem suporte**, registrar aqui o motivo e usar `cfg-citacao-por-resposta` na entrega. Falha de serviço pendente nessa data deixa o gate não aprovado; nada passa por omissão. README e vídeo seguem a configuração efetivamente entregue. Se aprovado, documentar aqui julgamento, custo observado e limites antes de atualizar README e roteiro. Não reescrever hashes, as duas respostas aprovadas nem o gate históricos como se pertencessem à configuração nova.

## Referências

- `docs/spec/0008-citacao-por-afirmacao.md` — contrato aprovado por Luiz antes do código.
- `docs/spec/0001-resposta-com-evidencias.md`, `docs/spec/0006-avaliacao-geracao.md`, `docs/spec/0007-cli-resposta-gerada.md`.
- `src/rag/responder.py`, `src/rag/provedor_gemini.py`, `reports/demo_cli_20261017.md`.
- `docs/planejamento/BRIEF_CODEX_citacao_por_afirmacao.md` e tag `cfg-citacao-por-resposta`.
