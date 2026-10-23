# Spec 0012 — Situação de entrega comparada por data

**Data:** 2026-10-23. **Status:** implementada localmente; prévias pendentes de liberação.
**Dono da decisão:** Luiz Maibashi.

## Problema medido

Antes desta mudança, `src/preprocessing/corpus.py` comparava `order_delivered_customer_date`
(data e hora) com `order_estimated_delivery_date` (sempre 00:00). Entrega às
14h do dia prometido era classificada como `atrasado`.

No corpus anterior, 526 avaliações `atrasado` tinham `dias_atraso == 0`
(entregues no dia previsto). Na população de entregues (n = 40.303):

| Regra | Atrasados | Proporção | IC95% Wilson |
|---|---:|---:|---|
| Horário (histórica) | ver [linha de base datada](../../reports/atraso_por_data_20261023.md) | ver relatório | ver relatório |
| Data (vigente) | 3.813 | 9,46% | 9,18% a 9,75% |

Os intervalos da regra anterior e da vigente não se sobrepõem. "Atrasado"
para o gestor é "chegou depois do dia prometido"; a regra anterior media
outra coisa.

## Escopo

1. Comparar por data: `atrasado` quando a data da entrega real é posterior à
   data estimada (equivale a `dias_atraso >= 1`). `nao_entregue` e
   `dias_atraso` não mudam.
2. Regenerar o corpus e recontar. Reportar contagem, `n` e IC95% Wilson.
3. ADR 0004: registrar a regra anterior, o achado (526) e o motivo da troca.
4. Atualizar `reports/dicionario_olist.md`, README, roteiro, slides e qualquer
   ocorrência dos números da regra anterior (buscar no repositório
   inteiro, inclusive `docs/video/`). Relatórios datados históricos
   (`reports/*_2026MMDD.md`) ficam como estão, com nota se forem citados.
5. Reabrir o P01 da spec 0009 (17/30 dentro do filtro `atrasado`) e reportar se
   o número mudou. Não refazer julgamento humano sem pedir.

Fora de escopo: embeddings, prompt, gabarito, capturas de geração, filtros de
categoria/período.

## Trava (critério de parada)

`corpus.py` não está em `ARQUIVOS_CODIGO` (`src/rag/liberacao.py:14`), então
esta mudança só altera o hash da prévia se alterar as evidências.

1. Referência: os fingerprints de contexto de E-A, E-B e P15 em
   `reports/previas_demo_0011_20261023.md` (`b5a7476c…`, `32f3b9da…`,
   `180e5e17…`).
2. Depois de mudar: gerar as mesmas prévias (sem `--executar`) e recalcular
   os fingerprints do mesmo jeito.
3. 3/3 iguais → seguir. Qualquer diferença → **parar, reverter e avisar**; a
   alternativa é só declarar os dois números, sem mudar código.

Previsão do Claude: contexto idêntico, porque as 18 evidências citadas em
`data/demo/execucoes.jsonl` são todas `atrasado` com `dias_atraso >= 1`, e
remover linhas fora do top-10 não muda o top-10.

## Item extra: hash não pode depender do fim de linha

`digest_codigo()` faz SHA-256 dos bytes do arquivo no disco. Com
`core.autocrlf=true` e sem `.gitattributes`, o mesmo commit gera CRLF ou LF
conforme a máquina; a reconstrução de 21/10 só bateu convertendo arquivos para
CRLF, com `liberacao.py` em LF. Efeito: gravar em outra máquina, ou um clone
público em Linux/Mac, produz hash diferente e o envio sai bloqueado.

Correção: normalizar `\r\n` → `\n` antes do SHA-256 em `digest_codigo()`, com
teste (mesmo conteúdo em LF e CRLF → mesmo digest). Muda o hash de novo, por
isso entra **antes** da regeneração final das prévias.

## Ordem (uma única liberação)

1. Commit dos filtros (spec 0011) com o relatório das prévias.
2. Normalização do fim de linha + teste.
3. Atraso por data (esta spec), com a trava acima.
4. Gerar E-A, E-B e P15 uma vez, conferir fingerprints, registrar hashes.
   Só então Luiz lê as prévias e libera.

## Aceitação

1. Teste: entrega no dia previsto (qualquer hora) → `no_prazo`; dia seguinte
   → `atrasado`; sem data real → `nao_entregue`.
2. Contagem nova reproduzível pelo CLI, com `n` e IC.
3. Busca dos números da regra anterior sem ocorrência fora dos relatórios
   datados com linha de base histórica anotada.
4. Suíte local passa; nenhuma chamada de API.
5. Commits pequenos: (a) regra + teste + corpus, (b) ADR + docs + vídeo.

## Resultado

Contagem, linha de base histórica, recontagem de P01 e hashes finais das três
prévias estão em `reports/atraso_por_data_20261023.md`. Os quatro slides
em `docs/video/slides/` foram conferidos visualmente: mostram 40.303 como
denominador ou métricas de recuperação, sem o numerador antigo; não exigem
reexportação. O Parquet regenerado fica fora do Git.

**Liberação para gravação (2026-10-23).** Luiz leu os 30 textos das prévias no
ambiente `.venv/sdk175` (`google-genai` 1.75.0), com código de
`ARQUIVOS_CODIGO` igual ao de `81dedba`, e liberou
E-A `28fb0e20214f31f163156580e6a1f3fddfcd18c6fa71fc890e5a607506b40a88`,
E-B `72ea2402264ac2f80a6a7c3ea043a10de4b72209b6eddb07f53b2c1435bf68ec`
e P15 `c53daa6570b52c72f4a9b289b7ae87d21be989beac77b7af34f9c729a8684e24`.
Contexto idêntico ao da liberação de 21/10 (spec 0010), que fica substituída.
O envio ao Gemini fica para a gravação. Qualquer edição em `ARQUIVOS_CODIGO`,
configuração ou corpus exige nova prévia e nova liberação.
