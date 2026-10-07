# Retomada — checkpoint 2026-10-07

## Estado atual para a próxima sessão

- CLI `src/demo.py` e README inicial prontos: buscar/contar locais e ensaio
  sintético com gerador falso. Ensaio com MiniLM real offline funcionou;
  243 testes passaram. Nenhuma API chamada na implementação local.
- EDA importa com statsmodels0.14.6 declarado/instalado; main não reexecutado,
  relatório histórico preservado. Sem reconstruir corpus/cache/pool/gabarito.
- E05 focado: previsão1, zero saídas; HTTP503 seguido de ReadTimeout, duas
  chamadas. Modelo/payload/timeout/política originais. Gate real bloqueado.
- Leia primeiro o Bridge (só TC4), README e reports/demo_local_20261007.md.
  Consulte reports/revisao_geral_20261007.md para diagnóstico; spec0006 e
  reports/e05_reavaliacao_20261007_01.jsonl para evidências de serviço.
- Próximo: previsão numérica antes de conferir busca/fontes/contagem reais.
  Revisar textos recuperados antes de eventual geração; autorização E01–E20
  não libera busca livre. Diagnóstico de disponibilidade ADR0006 em paralelo,
  sem repetir E05 automaticamente ou mudar modelo/timeout/tentativas.
- P09 congelado, guarda de data prevista ausente e revisão Torch pendentes.
  Gabarito antigo untracked fora do commit. Publicação/vídeo<=7min pendentes.
- Quiz de aprendizado enviado, ainda sem resposta: por que contar no corpus
  inteiro e por que simulação aprovada não libera Gemini. Não bloqueia entrega.

## Histórico da retomada de 2026-10-06

## Ponto de parada

Código: commit 218c6a6, geração Gemini 3.1 Flash-Lite e repetição optativa.
A rodada 04 foi executada e julgada: 19 saídas aprovadas por Luiz, E05 com falha
de serviço. São 17 casos aprovados com contexto real, E19 sintético e E20 local.
Previsão antes da execução: 18 utilizáveis. Foram 25 chamadas externas e cinco
recuperações na segunda tentativa (E01, E13, E16, E17, E19).
E05: ReadTimeout na primeira, HTTP 503 na segunda. Não houve saída para julgar.
Gate da demo bloqueado; não apagar falhas nem combinar aprovações de momentos
diferentes para declarar que esta rodada passou inteira.

E03/E06 foram aprovados após revisão da observação do agente: plural genérico
não sustenta reprovação pelo critério existencial. E07 foi aprovado por Luiz,
com ressalva de redação (item incompleto versus pedido com item faltante).
Capturas e votos originais permanecem intactos no JSON de evidências.

## Fontes a abrir, nesta ordem

1. Context Bridge da base: índice e somente tech_challenge_fase4.
2. Este arquivo e docs/spec/0006-avaliacao-geracao.md (estado atual/veredito 04).
3. reports/geracao_20261006_evidencias.json: ler metadados/resumo_rodada04 e,
   se necessário, registros E05; evitar carregar todas as capturas no contexto.
4. ADR-0007 e src/rag/tentativas.py para mudar repetição; spec 0004 antes da demo.

## Sincronização e ambiente

Projeto privado: https://github.com/luizmaibashi/voc-intelligence-rag-olist.
Atualizar o checkout limpo por fast-forward; se houver mudanças locais ou
divergência, inspecionar antes de integrar. Nunca resetar/descartar para sincronizar.
Os registros versionados bastam para revisar esta avaliação em outra máquina.
.venv, chave, corpus, CSVs brutos e PDF do enunciado não são transferidos pelo Git.
Os scripts exploratórios dos diagnósticos estavam na .venv e não são comandos
versionados de produção; não presumir que existirão na máquina de casa.

Recriar .venv com Python 3.13 e requirements.txt se necessário. SDK usado:
google-genai 1.75.0. Conferir versões; hash do lote inclui versão SDK, prompt,
modelo e política. Gerar nova prévia no ambiente de casa; hash antigo só vale
se a configuração conferir. Credencial Gemini somente no ambiente local,
GEMINI_API_KEY ou GOOGLE_API_KEY; nunca no Git ou no checkpoint.
A avaliação de contexto curado usa o manifesto; não precisa regenerar corpus.
Para RAG com busca/contagem, CSVs Olist locais em data/raw/ e
python -m src.preprocessing.corpus. Conferir caches; não transferir vetores
sem manifesto compatível nem regenerar gabarito/pool julgado.

Prévia com repetição, sem API:

```powershell
& .venv/Scripts/python.exe -X utf8 -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json --repetir-transitorios
```

Hash usado nesta máquina: 8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0.
SDK interno=1, controlador<=2, espera 2s, timeout SDK=25s por chamada.
Até 38 chamadas externas no lote inteiro. Falhas e tentativas são registradas
com flush; nenhuma mensagem de exceção/segredo é gravada.

## Próxima ação concreta

Preparar e conferir um diagnóstico focado de E05 a partir do caso exato do
manifesto, sem alterar texto/pergunta/modelo ou aumentar tentativas. O executor
versionado exige E01–E20; não existe --caso/--ids. Não remover casos do manifesto
para contornar validação. Um harness focado precisa de escopo/contrato e registro
próprios, reutilizando o controlador e preservando fonte/configuração/tentativas.
Antes de chamar API, pedir previsão 0 ou 1 para esse caso e registrar o número.
Nenhuma previsão nova foi dada após o fechamento da rodada 04.

Não rodar outro lote inteiro automaticamente. Não mudar timeout, modelo,
provider ou critérios em tentativa de fazer o gate passar. Sucesso posterior
em E05 não apaga falha da rodada 04; registrar tentativa e decidir explicitamente
se basta para o próximo gate. Depois: fluxo ponta a ponta da spec 0004, entrada
reproduzível/README e revisão de publicação/vídeo (até 7 min; entrega 01/11).

## Restrições e débitos

- Luiz autorizou somente os payloads revisados E01–E20 no Gemini gratuito.
  Contexto novo recuperado em busca livre exige revisão/liberação antes de envio.
- P09 congelado: somente liderança prazo/rapidez liberada; ranking completo não.
- Testes locais: 201 passaram; não são avaliação factual da API. Código não mudou
  após a suíte. Não há estimativa geral de disponibilidade/qualidade.
- PyTorch 2.12.1 tem alerta GHSA-rrmf-rvhw-rf47; patch 2.13.0 ainda não validado.
  Revisar compatibilidade em ambiente separado antes de publicação/demo livre.
- data/eval/gabarito.csv untracked antigo foi preservado, fora do commit; não usar
  como gabarito desta avaliação nem presumir que estará em casa.
- Logs/JSONL originais na .venv são locais; cópia revisada integral e julgamentos
  estão versionados em reports/geracao_20261006_evidencias.json.
- Hook commit-msg não inicia no sandbox Windows; funcionou fora dele sem bypass.
  Pytest usa pasta pai .venv/pytest-tmp criada e basetemp novo para cada execução.

## Prompt para abrir a sessão de casa

“Retome tech_challenge_fase4 pelo Context Bridge. Confira o Git do projeto e
abra docs/RETOMADA_CASA.md. A rodada 04 tem 19 aprovados e E05 com falha de
serviço; gate bloqueado. Prepare a reavaliação focada de E05, preserve o escopo
por arquivos e peça minha previsão antes de chamar API. Não repita o lote todo,
não altere comentários/modelo/critério e não reabra P09. Use sonnet-medium quando
necessário; outros comentários seguem sem liberação.”
