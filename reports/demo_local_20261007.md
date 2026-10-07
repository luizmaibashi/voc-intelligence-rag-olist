# Entrada local mínima — 2026-10-07

## Resultado e fronteira

Luiz confirmou o escopo da spec0004 e previu que testes e demo local
funcionariam. Implementados CLI local e README inicial; corrigida a dependência
da EDA. **243 testes passaram** na validação final, com FutureWarning como erro.
Ensaio com MiniLM real offline funcionou. **Gate da demo real segue bloqueado**:
não houve chamada ao Gemini nesta etapa, e E05 segue sem saída julgável.

## Mudanças

- `requirements.txt`: statsmodels==0.14.6, biblioteca já importada pelo script
  EDA. Instalada somente na venv; também entrou patsy1.0.3. NumPy/Pandas/Torch,
  modelo/prompt/schema/SDK Gemini e controlador de tentativas não foram alterados.
  Distribuição oficial com wheel CPython3.13/Windows:
  https://pypi.org/project/statsmodels/0.14.6/.
- `src/demo.py`: ações buscar/contar/ensaio-sintetico, sem cliente/credencial/API
  de geração. Busca e cálculo usam funções existentes. Saída JSON exibe fontes,
  filtros e limites. Entrada malformada/arquivo/modelo ausente falha visivelmente.
- `tests/test_demo.py` e `tests/test_eda.py`: filtros, fontes, contagem independente,
  simulação restrita, pesos offline, erros de CLI e importação EDA sem main.
- README inicial e contrato da spec0004. Nenhuma publicação/commit/push.

## Correção da EDA

Causa reproduzida na revisão geral: a importação do script falhava com
ModuleNotFoundError statsmodels porque requirements não declarava o import.
Após instalação, runpy.run_path com nome diferente de __main__ retornou
`EDA_IMPORT_OK True`, versão0.14.6. O teste confirma que reports/eda_olist.md
permanece byte a byte igual e testa Wilson nos extremos e num caso intermediário,
comparando statsmodels com a implementação da contagem (tolerância1e-5).

Não executamos main da EDA nem recomputamos seus números sobre os CSVs reais.
A falha de importação está corrigida; isso não é uma nova EDA nem avaliação do
corpus. `pip check`: No broken requirements found.

## Execuções e testes

```powershell
& .venv/Scripts/python.exe -X utf8 -m pip install --only-binary=:all: statsmodels==0.14.6
& .venv/Scripts/python.exe -X utf8 -m pip check
& .venv/Scripts/python.exe -X utf8 -m src.demo --acao ensaio-sintetico
& .venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --tb=short -W error::FutureWarning --basetemp .venv/pytest-tmp/demo-20261007-02
```

Rodada focal inicial:1 falha/21 passes. Fixture do teste de filtros esperava
incluir um comentário ainda marcado no_prazo num recorte atrasado; o índice
o excluiu corretamente. Corrigida somente a situação desse dado sintético no
teste. Não foi alterada busca nem seu contrato para satisfazer o teste.
Rodada completa final: **243 passed**. Logs de instalação/testes locais;
resumo aqui. Revisão independente sonnet-medium somente leitura: nenhum defeito
confirmado; orquestrador conferiu código, spec, comandos e saída real do ensaio.

## Ensaio sintético observado

Três comentários inventados; embedding MiniLM multilíngue, carregamento offline
com local_files_only=True. Sem download automático e sem API. Índice efêmero.

| Consulta | Observado |
|---|---|
| O que relatam sobre entregas atrasadas? | Filtros k2/nota<=2/atrasado; recuperados sintetico-02 (cinco dias/caixa amassada) e sintetico-01 (três dias/caixa intacta) |
| Resposta simulada | Reproduz os relatos inventados, cita os dois IDs e exibe seus textos em fontes_citadas |
| Prazo oficial de reembolso (P15) | Busca concluiu; gerador falso retornou sem_evidencia; aplicação exibiu recusa e nenhuma fonte citada |
| Contagem na fixture completa | 2 atrasadas de3 entregues, proporção2/3, IC95% Wilson[0,207655;0,938510], compras2018-01-01 a2018-03-01 |

Não apresentar isso como acerto do Gemini. Recusa/fala simuladas verificam a
ligação das peças, não raciocínio do modelo. A interpretação da contagem nesta
tabela vale só para a fixture inventada; não é número da operação Olist.

## Riscos conferidos e limites

1. Confundir simulação com avaliação real: modo/gerador/avisos explícitos, gerador
   falso definido dentro do ensaio e sem receber corpus real. Ação buscar só
   devolve candidatos; ação contar não carrega embeddings nem gerador.
2. Reutilizar cache legado incorreto: o emb_minilm.npy desta máquina não tem
   manifesto compatível ao lado. Demo não o consome nem sobrescreve; codifica
   documentos em memória. Isso custa mais tempo na busca completa; não medimos
   latência nem adicionamos cache novo sem contrato.
3. Perder população ao aplicar top-k: contar_atrasos recebe corpus inteiro;
   busca filtra antes de deduplicar. Testes cobrem representante elegível de
   texto repetido e contagem independente de uma busca k1.

Nenhum corpus, pool/gabarito, relatório EDA histórico, formulário P09 ou vetor
histórico foi regenerado. Git confirma ausência de mudanças rastreadas nesses
módulos/dados; não há baseline Git dos arquivos ignorados para afirmar um
confronto byte a byte de todos eles. Teste protege especificamente o relatório EDA.

P09 congelado; alerta Torch pendente; guarda de data estimada ausente continua
pendente, sem ocorrência no raw verificado na revisão geral. README não promete
filtros de categoria/período. Prosa do README conferida pelo passe escrita-organica,
sem travessões/emoji. Sem arquivo novo solto na raiz exceto README necessário.

## Próximo passo

Em etapa própria, conferir busca/contagem sobre corpus real com esta entrada,
revisar textos efetivamente recuperados para montar a avaliação ponta a ponta
da spec0004. Antes de outra medição, pedir previsão numérica apropriada; antes
de enviar payload novo, revisar e liberar o contexto. Diagnóstico delimitado de
disponibilidade do Gemini/ADR0006 em paralelo, sem repetir E05 automaticamente
ou mudar modelo/timeout/tentativas. A avaliação factual, o gate e a publicação
continuam decisões explícitas de Luiz; esta etapa não libera demo real.
