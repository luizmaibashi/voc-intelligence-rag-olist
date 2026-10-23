# ADR 0010: Tela local como casca fina sobre o CLI, preservando os hashes

**Status:** aceita · **Data:** 2026-10-23 · **Relaciona:** spec 0013, ADR 0003, spec 0007, spec 0012

## Contexto

Prévia, leitura do contexto e liberação por hash são a propriedade mais forte do projeto,
mas num terminal aparecem mal, e um gestor não usaria uma linha de comando. Os hashes de E-A,
E-B e P15 foram liberados em 23/10 (spec 0012) e cobrem cinco arquivos de código, a
configuração de geração e o contexto recuperado (`src/rag/liberacao.py`). Qualquer edição
nesses arquivos invalida a liberação.

## Decisão

1. Tela **local** em Streamlit (`src/tela/`), que só importa `responder_cli` e `quantificar`
   de `src/demo.py`. Nenhum dos cinco arquivos do hash foi editado por causa da tela.
   `scripts/paridade_tela.py` confere que a prévia feita pela tela produz os três hashes
   liberados.
2. Duas portas para o mesmo fluxo:
   - **Perguntar** (padrão), trilha em cinco passos para quem decide: pergunta e recorte em
     português, relatos encontrados, aprovação, resposta com as posições citadas, conferência
     das citações e tamanho do problema pela contagem. A aprovação é um checkbox ("Li os
     relatos e nada identifica o cliente") mais o botão "Aprovar e gerar resposta", que envia
     o hash da prévia exibida para a entrada atual.
   - **Modo técnico**, mesmo fluxo do CLI: filtros, `k`, score e o hash **colado** à mão.
3. Na trilha, o hash deixou de ser colado. O rascunho desta ADR mantinha a colagem como
   registro de leitura. Na tela, porém, o vínculo entre o que foi lido e o que é enviado já é
   garantido por dois mecanismos: a prévia é descartada quando pergunta ou recorte mudam, e o
   servidor recusa (`EnvioBloqueado`) qualquer hash diferente do contexto recalculado. Colar
   o hash repetia um gesto do terminal sem acrescentar controle. A colagem continua no Modo
   técnico, onde a trava pode ser demonstrada.
4. Abas Números (contagem de atrasos) e Execuções (somente leitura de
   `data/demo/execucoes.jsonl`: tentativas, erros de integração com IC de Wilson e n,
   mediana de duração). Números em formato pt-BR.
5. Streamlit 1.56.0 fixado em `requirements-app.txt`, instalado com arquivo de restrição
   (`pip freeze` → `-c`), fora do `requirements.txt` da avaliação.
6. **Sem hospedagem.** `.streamlit/config.toml` fixa `server.address = "localhost"` e o tema
   escuro dos slides do vídeo.

## Evidência

Em 2026-10-23, com corpus e pesos reais: paridade 3/3 (`28fb0e20…`, `72ea2402…`, `c53daa65…`),
358 testes, fluxo da trilha exercitado sem navegador (preset E-B reconhecido como contexto
liberado, botão desabilitado sem o checkbox, simulação sem chamada) e no navegador.

## Alternativas

| Alternativa | Por que não |
|---|---|
| Seguir só com o CLI | Funciona; perde legibilidade do controle humano e não mostra uso por um gestor |
| Gradio | Equivalente para este uso; Streamlit tem `st.cache_resource` direto para modelo e corpus |
| Refatorar `demo.py` para servir à tela | Quebra o hash sem ganho para o usuário |
| Colar o hash também na trilha | Gesto sem controle adicional (item 3); fica no Modo técnico |
| Filtros inferidos da pergunta por LLM | Muda o contexto (hash) e exige medir a extração; fica para depois da entrega |
| API + front separado ou hospedagem | Duas peças a manter; hospedar expõe chave e cota e envia texto sem leitura (ADR 0003, spec 0007) |

## Consequências

- A tela é uma segunda porta para a mesma lógica: se o CLI mudar, a tela acompanha sem
  duplicar regra, e a paridade denuncia divergência.
- O registro de execuções e o teto de 20 chamadas por dia são por checkout: gravar de outro
  checkout exige o mesmo `data/demo`.
- A leitura humana continua obrigatória a cada envio. Para uso em volume, o caminho é mascarar
  dados pessoais antes do envio e trocar a leitura integral por auditoria por amostra; nada
  disso foi implementado.
