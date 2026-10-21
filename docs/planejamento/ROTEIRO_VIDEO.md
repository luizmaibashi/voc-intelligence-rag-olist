# Roteiro do vídeo (≤ 7 min) — rascunho 2026-10-17, revisto 2026-10-20

Dono: Luiz. Status: rascunho para revisão; gravar só depois do REVERTER-01
(o CLI do `main` precisa rodar a configuração entregue). Meta de 6:30 para sobrar margem.
Falas são guia de tom, não texto para decorar: Luiz explica as escolhas com
as próprias palavras (plano, Etapa 7).

Cobertura do enunciado (p. 10): problema de negócio [N], arquitetura [A],
estratégia RAG [R], recuperação [Rec], demo prática [D], exemplos de perguntas
[P], evidências [E], desafios e decisões [Dec].

| # | Tempo | Bloco | Tela | Ideia central (fala-guia) | Cobre |
|---|---|---|---|---|---|
| 1 | 0:00–0:40 | Dor | Slide: 1 comentário real + nota 1 | "Um gestor de atendimento tem 40 mil comentários e uma pergunta: o que está dando errado na entrega? Ler tudo não cabe; uma IA que inventa resposta é pior que não ter." | N |
| 2 | 0:40–1:30 | Arquitetura | Diagrama do README | Pergunta → MiniLM → DuckDB com filtros → contexto → Gemini → validação de citações. Contagem SQL corre ao lado, separada. "Cada caixa existe por um motivo que dá para medir." | A, R |
| 3 | 1:30–2:20 | Base e busca | Slide: P@10 dos 3 modelos com IC95% | 1 avaliação = 1 documento, limpeza mínima (negação e acento importam). MiniLM × E5 × TF-IDF com gabarito humano: P@10 0,72 [0,55; 0,87], n=14; ICs sobrepostos — escolha justificada, não "vencedor". | R, Rec, Dec |
| 4 | 2:20–3:50 | Demo: a pergunta muda o achado | Terminal: prévia → hash → resposta | Pergunta 1 ("relatam sobre atraso") → resposta óbvia, 10/10 citadas. Pergunta 2 ("o que aconteceu depois do atraso") → 5 fontes, "não receberam justificativa". Mostrar comentário citado. "A IA levantou uma pista; agora preciso medir." | D, P, E, Rec |
| 5 | 3:50–4:30 | Contagem | `--acao contar` | 4.339 de 40.303 = 10,77%, IC95% [10,47%; 11,07%]. "Top-k mostra exemplos; frequência vem de contagem com população definida." Gancho da aula: não afirmar que atraso causou a nota. | E, Dec |
| 6 | 4:30–5:15 | Recusa | Terminal: P15 política de reembolso | Status `sem_evidencia`: relato de cliente não estabelece política oficial. Falha do serviço aparece como `erro_geracao`, nunca como "não sei". | P, E |
| 7a | 5:15–5:35 | Decisões | Spec 0007 / trecho de código | (a) Prévia + hash: nenhum comentário sai sem leitura; (b) teto de 20 chamadas/dia; (c) citação validada contra o contexto, por resposta. | Dec |
| 7b | 5:35–6:10 | Experimento abandonado | `--validar` da ficha oficial (sem API): `19/20`, `E17: recusa_indevida`, `gate: aberto` | "Citar por resposta não diz qual frase errou. Testei citar por frase, com a regra escrita antes: recusar quando há evidência reprova. Deu 19 de 20 (IC95% 76,4% a 99,1%; casos escolhidos de propósito). E17, 'a entrega foi elogiada?', recusou onde a versão entregue respondia com a crítica citada. Perder cobertura custa mais que localizar o erro: voltei para a versão anterior e o experimento ficou registrado (ADR 0008)." | Dec, E |
| 8 | 6:10–6:35 | Limites e próximo passo | Slide de limites | Dados 2016–2018, viés de quem comenta; 20 casos escolhidos de propósito testam o contrato, não estimam taxa de acerto geral. Próximo: contar menções de "sem contato" para testar a pista. | N, Dec |

## Pendências antes de gravar

- **REVERTER-01 auditado** no `origin/main`: a demo do bloco 4 não pode rodar a
  configuração abandonada. O hash mostrado na tela é o que o REVERTER-01 imprimir.
- **Bloco 7b:** E17 tem hipótese (pergunta negativa contra contrato por
  afirmação), não causa medida. Se falar do motivo, dizer "hipótese".

- ~~**Bloco 6 sem execução real no CLI.**~~ Resolvido em 2026-10-21: prévia +
  1 chamada liberada, `sem_evidencia` em 1 tentativa
  (`reports/demo_cli_p15_20261021.md`). Na tela aparece a mensagem genérica da
  aplicação; "relato não estabelece política" é fala, não saída do CLI.
- ~~**Espera dos vetores.**~~ Decidido em 2026-10-21: cortar na edição, sem
  mudar código. Causa: `recuperar` (`src/demo.py`) recalcula os vetores dos
  42.174 comentários a cada comando (índice efêmero, ADR 0002), ~3:50 por
  execução; 6 execuções nos blocos 4 e 6 (prévia + envio de E-A, E-B e P15).
  Deixar 2–3 s da barra de progresso antes de cada corte. Fala no bloco 4:
  "A busca é exata e refaz os vetores de 42 mil comentários a cada consulta,
  uns 4 minutos; cortei a espera. Em produção, o cache que já uso na avaliação
  resolve isso." Conferência ao vivo: se o corpus não mudou, a prévia de E-A
  repete o hash aprovado em 17/10 (`4357b6f9…`).
- Slides: decidido em 2026-10-21 o tema escuro de terminal (direção A), para
  não mudar de visual entre slide e demo. Quatro slides (blocos 1, 2, 3 e 8);
  o bloco 3 ganhou slide porque o ADR em tela fica ilegível no vídeo (P@10 dos
  3 modelos com IC95%, números do ADR 0002). Rascunho no canvas privado
  https://claude.ai/artifact/3ce9d9UDVqj91shkPbGQ12. Falta exportar em
  1280×720.
- Ensaio cronometrado: ler em voz alta e ajustar; se passar de 6:45, cortar o
  bloco 3 primeiro (detalhe fica no README). Com o 7b o total previsto é 6:35.
