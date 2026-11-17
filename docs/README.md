# Como ler esta pasta

O README da raiz explica o que o sistema faz. Esta pasta guarda por que ele
ficou assim: cada decisão foi escrita antes do código ou antes da medição, e o
resultado ficou registrado mesmo quando contrariou a expectativa.

## O fluxo de trabalho

1. **Contrato antes do código.** Uma spec diz o que a mudança precisa garantir
   e como vai ser testada. Exemplo: a [spec 0007](spec/0007-cli-resposta-gerada.md)
   exige prévia do contexto e liberação por hash antes de qualquer envio ao
   modelo, porque comentário de cliente não sai sem leitura humana.
2. **Decisão com alternativa descartada.** Escolhas difíceis de reverter viram
   ADR, com o custo de não decidir e as opções recusadas. Exemplo: a
   [ADR 0002](adr/0002-embedding-minilm-busca-exata-duckdb.md) escolhe o MiniLM
   com intervalos de confiança sobrepostos e diz isso, em vez de declarar um
   vencedor.
3. **Previsão antes da medição.** Antes de rodar uma avaliação, a regra de
   aprovação e a previsão ficam escritas. O resultado não é reinterpretado
   depois.
4. **Execução delegada e auditada.** Parte da execução foi feita por agentes de
   IA a partir de instruções fechadas; cada entrega foi conferida contra
   testes e arquivos antes de entrar no `main`. Os briefs de execução saíram
   da versão publicada e continuam no histórico do Git (`docs/planejamento/`).

## Um caso em que o processo mudou o rumo

A [ADR 0008](adr/0008-citacao-por-afirmacao.md) testou citar a fonte frase a
frase, para localizar o erro com mais precisão. A regra escrita antes era:
recusar uma pergunta que tinha evidência reprova. O experimento deu 19 de 20 e
reprovou nesse ponto, então a entrega voltou para a versão anterior e o
experimento ficou documentado como abandonado.

## O que há em cada pasta

| Pasta | Conteúdo | Para quem |
|---|---|---|
| [`adr/`](adr/) | 10 decisões de arquitetura: corpus, busca, geração, contagem, elogios, modelo, repetição, citação, busca híbrida, tela local | quem quer entender o porquê de cada escolha |
| [`spec/`](spec/) | 14 contratos de comportamento, com critérios de aceite e testes | quem quer conferir o que o sistema garante |
| [`video/`](video/) | Slides do vídeo de apresentação | apoio à apresentação |

Specs e ADRs antigas são mantidas como foram escritas na época. Algumas citam
arquivos de trabalho que não fazem parte da versão publicada.
