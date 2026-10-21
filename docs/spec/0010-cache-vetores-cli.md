# Spec 0010 — Cache dos vetores do corpus no CLI

**Data:** 2026-10-21. **Status:** executada e aceita em 2026-10-21. Critérios 1, 3 e 4 atendidos; critério 2
reprovou como escrito por erro de formulação e foi aceito pelo Luiz pelo payload
idêntico fora o campo `codigo` (ver Resultado).
**Dono da aprovação:** Luiz Maibashi. **Prazo da entrega:** 2026-10-31.

## Problema

`recuperar` (`src/demo.py`) refaz os vetores das 42.174 avaliações a cada comando
(índice efêmero, ADR 0002): cerca de 3:50 por execução na máquina registrada. A
demo do vídeo tem 6 execuções (prévia e envio de E-A, E-B e P15), então cerca de
24 minutos de espera e um corte por execução na edição. O roteiro gasta cerca de
10 s explicando o corte e promete que "o cache que já uso na avaliação resolve
isso". Essa promessa não vale como está: o cache da avaliação cobre os textos
distintos do pooling, e a spec 0005 proíbe associá-lo ao corpus completo de busca.

## Contrato

- O CLI (`buscar` e `responder`) reutiliza um cache dos vetores de **todas as
  linhas** do corpus, em ordem, em `data/processed/emb_busca_minilm.npy` com
  manifesto `.json` ao lado. `data/processed/` já está fora do Git.
- A identidade do cache segue a spec 0005: textos em ordem (SHA-256), modelo,
  normalização, versão de sentence-transformers e dimensão, mais o digest dos
  vetores. Qualquer diferença, arquivo corrompido ou formato inválido avisa e
  regenera. Nunca reaproveita o cache distinto do pooling.
- A lógica de cache fica num só lugar: a função de `pool_candidatos` passa a
  delegar para uma função compartilhada em `src/retrieval/`, com o caminho como
  parâmetro. Sem segunda cópia (achado de duplicação da revisão de 21/10).
- Gravação atômica: escreve em arquivo temporário e troca no fim, para que um
  Ctrl+C ou duas execuções ao mesmo tempo não deixem cache meio escrito válido.
- `recuperar` sem caminho de cache mantém o comportamento atual (testes e ensaio
  sintético não gravam nada em disco).
- Nada muda na busca, nos filtros, no payload nem no hash da prévia.

## Critério de aceite (decidido antes de rodar)

1. **Top-10 idêntico.** Para E-A, E-B e P15, com os filtros usados na demo, a
   lista de `review_id` em ordem e os textos do contexto são idênticos entre a
   execução sem cache e a execução lendo o cache. Uma posição diferente reprova.
2. **Hash idêntico.** A prévia de E-A lendo o cache imprime o hash aprovado em
   2026-10-17 (`4357b6f9…698796`), se o corpus não mudou desde então.
3. **Testes primeiro.** Testes sintéticos com encoder falso, sem rede: cache
   reaproveitado não chama o encoder; texto alterado, modelo diferente, digest
   errado ou arquivo truncado regeneram; ausência de caminho não grava. Falham
   antes da mudança e passam depois; suíte inteira verde.
4. **Tempo.** Medir com relógio de parede o comando `responder` (prévia de E-A),
   uma vez gerando o cache e uma vez lendo.

Se 1 ou 2 reprovar, a mudança não entra antes da gravação e o roteiro fica com
o corte na edição, como decidido em 2026-10-21.

## Previsão (registrar antes de medir)

| Medida | Previsão do agente | Previsão do Luiz |
|---|---|---|
| Comando com cache novo (primeira vez) | igual ao atual, cerca de 4 min | igual ao agente |
| Comando lendo o cache | menos de 30 s (modelo, corpus, DuckDB) | igual ao agente |
| Top-10 idêntico nas 3 perguntas | sim | igual ao agente |
| Hash de E-A igual ao de 17/10 | sim | igual ao agente |

Previsão do Luiz registrada no chat em 2026-10-21, antes de qualquer medição.

Base da previsão do agente: o encoder é a parte cara; carregar 42.174 × 384
float32 (cerca de 65 MB) e montar a tabela DuckDB deve custar segundos. Se a
leitura passar de 60 s, o gargalo não é o encoder, e isso vai para o relatório.

## Resultado (2026-10-21)

Linha de base com o código anterior (`8333558`), corpus codificado uma vez em
178 s, prévias de E-A, E-B e P15 com nota ≤ 2, `atrasado`, k = 10. Depois da
mudança, quatro prévias pelo CLI (`--acao responder`, sem `--executar`):

| Execução | Tempo de parede | Top-10 igual à linha de base |
|---|---|---|
| E-A, gera o cache | 194 s | 10/10 posições |
| E-A, lê o cache | 20,6 s | 10/10 |
| E-B, lê o cache | 20,6 s | 10/10 |
| P15, lê o cache | 21,3 s | 10/10 |

| Previsão (agente e Luiz) | Resultado |
|---|---|
| Primeira vez cerca de 4 min | 3:14, acertou |
| Leitura abaixo de 30 s | 20,6 a 21,3 s, acertou |
| Top-10 idêntico nas 3 | sim, acertou |
| Hash de E-A igual ao de 17/10 | **não, como escrito**: ver abaixo |

**Critério 2 mal formulado.** O hash da prévia inclui o digest de `src/demo.py`
(`liberacao.ARQUIVOS_CODIGO`, spec 0007): qualquer mudança nesse arquivo muda o
hash de propósito, para exigir nova liberação. A prévia de E-A agora imprime
`338d0b32…`. Recalculado com o digest do código anterior (o gravado no envio de
P15 em 21/10), o payload novo reproduz `4357b6f9…` em E-A e `ba7b7fb4…` em E-B:
fora o campo `codigo`, nada mudou. A spec deveria ter pedido isso. Luiz aceitou
no chat em 2026-10-21, depois de ver o resultado, com esse critério reformulado.
Consequência: os hashes de E-A, E-B e P15 mudaram e precisam de nova liberação
antes da gravação.

**Achados laterais.**
- A linha de base de P15, com código e contexto iguais aos de 21/10, dá
  `50e01e7a…`, não o `5d874a74…` liberado naquele dia. Mesmos 10 IDs e mesmos
  textos. Suspeita não verificada: a versão do `google-genai` entra no hash e o
  `requirements.txt` não a trava (`>=1.73,<2`).
- O digest do código depende do fim de linha do arquivo em disco (CRLF aqui, LF
  no Git). Um clone com outra configuração imprime outro hash para o mesmo código.
  Não afeta a segurança do envio; afeta a comparação de hashes entre máquinas.

## Limites e riscos

- Mudança de código depois da avaliação e antes da gravação. Mitigação: critérios
  1 e 2 comparam com a execução atual; reprovou, não entra.
- O primeiro comando continua lento; gerar o cache antes de gravar.
- Nome de modelo não fixa a revisão dos pesos (mesmo limite da spec 0005).
- Determinismo do encoder entre execuções é premissa; o critério 1 a testa só nas
  3 perguntas da demo.
- ADR 0002 ganha uma nota: o índice em DuckDB continua efêmero; os vetores passam
  a ter cache no CLI.

## Fora do escopo

Índice aproximado, banco persistente, mudar a busca ou os filtros, remedir P@10,
qualquer chamada ao Gemini (os critérios usam só a prévia).
