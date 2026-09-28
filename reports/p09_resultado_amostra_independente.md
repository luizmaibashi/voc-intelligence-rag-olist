# P09 — resultado provisório da amostra independente

**Data:** 2026-09-28. **Amostra:** 50 avaliações com comentário, sorteadas com
`seed=20260929` após excluir 385 IDs dos CSVs P09 anteriores. IDs em
`data/eval/p09_amostra_independente_ids.csv`; rótulos sem texto em
`data/eval/p09_amostra_independente_rotulos.csv`. Votos e notas originais
permanecem em `Downloads/p09_votos_luiz_amostra_independente.csv`.

## Rubrica aplicada

Luiz marcou 55 `sim`, 72 `nao` e 123 `incerto` nos 250 campos da amostra.
Esclareceu que `incerto` expressava dúvida sobre a experiência real quando o
aspecto não aparecia no texto. Para P09, autorizou converter esses 123 votos
em `nao` (ausência de elogio explícito). A coluna `voto_original` preserva o
registro inicial; `rotulo_p09` contém a interpretação acordada. Nenhum texto
bruto está nos CSVs versionáveis.

## Matriz por tema

Cada linha usa as mesmas 50 avaliações. Intervalos de 95% são Wilson;
precisão e revocação usam seus denominadores próprios. A amostra excluiu
casos anteriores e só representa esse recorte do corpus com comentário.

| Tema | VP | FP | FN | VN | Precisão | Revocação |
|---|---:|---:|---:|---:|---|---|
| Prazo/rapidez | 14 | 0 | 6 | 30 | 14/14; IC [0,785; 1,000] | 14/20; IC [0,481; 0,855] |
| Integridade | 1 | 0 | 2 | 47 | 1/1; IC [0,207; 1,000] | 1/3; IC [0,061; 0,792] |
| Pedido correto | 1 | 0 | 7 | 42 | 1/1; IC [0,207; 1,000] | 1/8; IC [0,022; 0,471] |
| Elogio geral | 1 | 0 | 19 | 30 | 1/1; IC [0,207; 1,000] | 1/20; IC [0,009; 0,236] |
| Texto misto | 0 | 0 | 4 | 46 | indefinida (0 previsões positivas) | 0/4; IC [0,000; 0,490] |

Em 24/50 avaliações houve pelo menos um aspecto elogiado que a regra não
marcou (IC95% [0,348; 0,615]); Luiz havia previsto 15/50 antes da revisão.
Em 25/50 houve algum desacordo, incluindo `misto`. As contagens por tema se
sobrepõem e não devem ser somadas como casos únicos.

## Diagnóstico inicial e gate

Os 34 falsos negativos dos quatro aspectos não acionaram o padrão positivo
correspondente nem foram suprimidos por um padrão de reclamação. Falta uma
revisão humana dos casos para separar expressões positivas não cobertas de
possíveis votos que ainda usem inferência de boa experiência. A amostra não
autoriza ajustar padrões diretamente aos votos sem essa revisão.

**Gate da spec 0003: bloqueado.** A revocação observada de elogio geral e
pedido correto é baixa e os intervalos dos temas raros são largos. Não
publicar ranking P09. Próximo passo: análise qualitativa local dos desacordos,
correção da causa confirmada e outra amostra independente após a mudança.
O formulário `data/processed/p09_revisao_erros_local.html` reúne os 25 casos
com desacordo e pede 38 decisões por tema sob a rubrica final. O arquivo
contém texto bruto e permanece fora do Git; sua exportação não contém texto.

## Segunda revisão humana dos desacordos

Luiz respondeu às 38 decisões: confirmou 31 marcações positivas, corrigiu
6 para `nao` e deixou 1 `incerto`. O CSV original com notas fica em
`Downloads/p09_revisao_erros_amostra_independente.csv`; a coluna `rotulo_final`
do CSV versionável incorpora a revisão e mantém `voto_original` separado.
Após a revisão, 20/50 avaliações têm ao menos um aspecto confirmado que a
regra perdeu (IC95% [0,276; 0,538]); 22/50 têm algum desacordo confirmado.

| Tema | VP | FP | FN | VN | Incerto | Precisão | Revocação |
|---|---:|---:|---:|---:|---:|---|---|
| Prazo/rapidez | 14 | 0 | 6 | 30 | 0 | 14/14; IC [0,785; 1,000] | 14/20; IC [0,481; 0,855] |
| Integridade | 1 | 0 | 2 | 47 | 0 | 1/1; IC [0,207; 1,000] | 1/3; IC [0,061; 0,792] |
| Pedido correto | 1 | 0 | 3 | 46 | 0 | 1/1; IC [0,207; 1,000] | 1/4; IC [0,046; 0,699] |
| Elogio geral | 1 | 0 | 18 | 31 | 0 | 1/1; IC [0,207; 1,000] | 1/19; IC [0,009; 0,246] |
| Texto misto | 0 | 0 | 2 | 47 | 1 | indefinida (0 previsões positivas) | 0/2; IC [0,000; 0,658] |

Nos 29 falsos negativos confirmados dos quatro aspectos, o padrão positivo
correspondente não foi acionado. Os dois casos mistos confirmados não
acionaram `NEGATIVO`. Todos os 18 falsos negativos de `elogio_geral`
coincidem com voto positivo de prazo/rapidez; falta fixar se um elogio apenas
ao prazo também deve preencher `elogio_geral` antes de alterar código.
As notas livres da revisão também indicam que alguns `sim` foram justificados
por inferência a partir do tom positivo, sem menção inequívoca à entrega.
Portanto, a matriz acima é condicional aos rótulos registrados e não é ainda
um gabarito estável para ajustar a regra ou liberar o ranking. A distinção
entre elogio geral explícito e consequência de um atributo positivo precisa
ser fechada com Luiz.

## Próxima decisão de rótulo

Para avançar sem transformar um elogio ao prazo em elogio geral por inferência,
a spec 0003 passou a exigir elogio próprio à entrega como um todo. A tela
local `data/processed/p09_elogio_geral_explicito_local.html` reúne apenas os
18 casos em que a revisão anterior confirmou `elogio_geral` e a regra não o
marcou. Luiz fará uma decisão final sob essa definição; o CSV exportado
conterá só ID, rótulo e nota, sem texto bruto. A matriz acima é provisória
até essa decisão. Antes de revisar, Luiz previu que **6 a 12 dos 18** ainda
terão elogio geral explícito.

Na exportação `Downloads/p09_elogio_geral_explicito.csv`, Luiz marcou 16 dos
18 casos como `sim` e 2 como `nao`, acima da previsão. A matriz condicional
passaria a 1 VP, 0 FP, 16 FN e 33 VN em `elogio_geral`, com revocação 1/17
(IC95% Wilson [0,010; 0,270]); 20/50 avaliações ainda teriam algum aspecto
perdido (IC95% [0,276; 0,538]). Porém, ao menos uma justificativa do `sim`
descreve apenas rapidez, sem elogio geral próprio. Esse conflito entre a
definição escrita e o voto precisa ser resolvido antes de tratar os 16 como
gabarito estável ou ampliar o padrão de `elogio_geral`.
Luiz confirmou que, nesse caso concreto, só `prazo_rapidez` é positivo;
`elogio_geral` passou a `nao`, sem apagar os votos anteriores. A matriz
condicional fica em 1 VP, 0 FP, 15 FN e 34 VN para elogio geral, com
revocação 1/16 (IC95% Wilson [0,011; 0,283]). Os 15 `sim` restantes serão
revisados em `data/processed/p09_fundamento_elogio_geral_local.html`, agora
com seleção do fundamento textual e uma palavra de avaliação geral quando
aplicável. O HTML contém comentários brutos só localmente.

## Pausa para retomar em outra máquina

Luiz pausou antes de responder os 15 casos. O formulário com comentários fica
fora do Git. Após reconstruir `data/processed/corpus_reviews.parquet` a partir
dos CSVs Olist locais, executar
`python -m src.eval.gerar_formulario_p09_pendente` para recriá-lo em
`data/processed/p09_fundamento_elogio_geral_local.html`. O template versionado
não contém comentários. Responder os 15 casos e exportar
`p09_fundamento_elogio_geral.csv` antes de qualquer ajuste no classificador.
