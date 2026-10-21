# ADR-0008 — Citação por afirmação como experimento reversível

**Data:** 2026-10-18. **Status:** **abandonado em 20/10/2026** (gate 19/20; ver "Resultado e decisão"). Experimento e contrato da spec 0008 aprovados por Luiz em 18/10/2026. **Entrega:** tag publicada `cfg-citacao-por-resposta` no commit `fe652b6`.

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

## Resultado e decisão (20/10/2026, 21:15 local = 21/10 00:15Z)

**Execução.** Fase 1 (13 pareáveis) em 20/10 UTC, com E02/E18 recuperados em reenvio autorizado por falha de serviço; fase 2 (`E01,E05,E13,E16,E17,E19,E20`) em 21/10 UTC, capturas `reports/geracao_citacao_afirmacao_fase2_lote1.jsonl` e `_lote2.jsonl`, hash `203ec986…` igual ao autorizado. Na fase 2, E13 e E16 tiveram `ServerError 503` na primeira tentativa e saída na segunda, conforme a política de repetição. Chamadas no ledger desta máquina: 20 em 19/10 (sem saída, `ConnectError`), 18 em 20/10 e 8 em 21/10 UTC.

**Contrato.** `N = 0` falhas de contrato em 19 casos julgáveis (E20 é controle local), IC95% Wilson [0%; 16,8%]. `N_pareado = 0/13`. Previsão de Luiz: `N = 3`.

**Julgamento de Luiz, frase a frase.** **19/20 aprovados** (IC95% Wilson [76,4%; 99,1%]); fase 1 13/13 e fase 2 6/7 (IC95% [48,7%; 97,4%]). Previsões: 17/20 no lote; 7/7 na fase 2 (errou por 1) e 4/4 recusas corretas (acertou). Os votos de E16 (recusa, inicialmente NS) e E20 (controle, inicialmente sem voto) foram revistos para S depois de o Claude apontar que a justificativa sustentava a recusa (E16) e que E20 tem contexto vazio por desenho, porque a avaliação curada isola geração e não mede retrieval (E20). A revisão foi influenciada e fica registrada como tal.

**Reprovado: E17.** Pergunta "A entrega foi elogiada neste contexto?", fonte "muito demorada a entrega"; a configuração nova devolveu `sem_evidencia` (`status_esperado_compativel: false`). Pela regra fixada por Luiz em 19/10, antes de qualquer resultado, recusa em caso com `respondida` esperada não passa (perda de cobertura). A baseline respondeu E17 preservando a crítica (spec 0006, resultados da rodada julgada), então é **regressão** da configuração nova, não caso que nunca passou.

**Leitura do critério.** E17 não tem frase, então "sem frase sem suporte" seria literalmente verdadeiro; essa leitura aprovaria por omissão e contraria o próprio critério ("nada passa por omissão") e a regra de 19/10. Também foi descartado reenviar E17 até passar: o executor recusa caso já enviado sob o mesmo hash (`src/eval/avaliar_geracao.py:272`), e repetir um reprovado mede sorte, não a configuração.

**Decisão de Luiz: abandono.** O gate não tem 20/20 aprovados; a entrega usa `cfg-citacao-por-resposta`. README e vídeo seguem a tag; a demonstração de auditoria par a par fica como conferência manual de uma resposta aprovada (alternativa da tabela acima). O experimento entra no README como medido, não como funcionalidade.

**Hipótese não testada para E17.** A pergunta exige resposta negativa ("não houve elogio"); no contrato por afirmação, cada frase precisa de fonte, e uma afirmação de ausência não tem comentário que a diga literalmente. O modelo pode preferir recusar a ancorar uma negação, atrito que a citação por resposta não tinha. "Azar" é a explicação alternativa, pouco provável com `temperature=0`, mas não excluída: `n = 1` tentativa. Luiz previu 2 recusas em 3 repetições; não houve medição. Testar exigiria reavaliação focal autorizada em código, com saída fora da ficha, e só vale se uma nova configuração (instrução para perguntas negativas) for experimentada depois da entrega.

**Limite da ferramenta achado no processo.** `--validar` saía com código 0 mesmo com casos pendentes, e E20 nunca deixava de ser pendente. Correção em `docs/planejamento/BRIEF_CODEX_VALIDAR-01.md`; a ficha oficial E01 a E20, com os votos acima, será gerada depois dela em `reports/`. Os 13 julgamentos da fase 1 foram copiados por `(id, ordem)` com frase idêntica (ensaio reproduziu a ficha aprovada byte a byte).

## Referências

- `docs/spec/0008-citacao-por-afirmacao.md` — contrato aprovado por Luiz antes do código.
- `docs/spec/0001-resposta-com-evidencias.md`, `docs/spec/0006-avaliacao-geracao.md`, `docs/spec/0007-cli-resposta-gerada.md`.
- `src/rag/responder.py`, `src/rag/provedor_gemini.py`, `reports/demo_cli_20261017.md`.
- `docs/planejamento/BRIEF_CODEX_citacao_por_afirmacao.md` e tag `cfg-citacao-por-resposta`.
