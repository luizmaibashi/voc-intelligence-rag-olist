# Roteiro do vídeo (≤ 7 min) — rascunho 2026-10-17

Dono: Luiz. Status: rascunho para revisão. Meta de 6:30 para sobrar margem.
Falas são guia de tom, não texto para decorar: Luiz explica as escolhas com
as próprias palavras (plano, Etapa 7).

Cobertura do enunciado (p. 10): problema de negócio [N], arquitetura [A],
estratégia RAG [R], recuperação [Rec], demo prática [D], exemplos de perguntas
[P], evidências [E], desafios e decisões [Dec].

| # | Tempo | Bloco | Tela | Ideia central (fala-guia) | Cobre |
|---|---|---|---|---|---|
| 1 | 0:00–0:40 | Dor | Slide: 1 comentário real + nota 1 | "Um gestor de atendimento tem 40 mil comentários e uma pergunta: o que está dando errado na entrega? Ler tudo não cabe; uma IA que inventa resposta é pior que não ter." | N |
| 2 | 0:40–1:30 | Arquitetura | Diagrama do README | Pergunta → MiniLM → DuckDB com filtros → contexto → Gemini → validação de citações. Contagem SQL corre ao lado, separada. "Cada caixa existe por um motivo que dá para medir." | A, R |
| 3 | 1:30–2:20 | Base e busca | ADR 0001/0002 em tela | 1 avaliação = 1 documento, limpeza mínima (negação e acento importam). MiniLM × E5 × TF-IDF com gabarito humano: P@10 0,72 [0,55; 0,87], n=14; ICs sobrepostos — escolha justificada, não "vencedor". | R, Rec, Dec |
| 4 | 2:20–3:50 | Demo: a pergunta muda o achado | Terminal: prévia → hash → resposta | Pergunta 1 ("relatam sobre atraso") → resposta óbvia, 10/10 citadas. Pergunta 2 ("o que aconteceu depois do atraso") → 5 fontes, "não receberam justificativa". Mostrar comentário citado. "A IA levantou uma pista; agora preciso medir." | D, P, E, Rec |
| 5 | 3:50–4:30 | Contagem | `--acao contar` | 4.339 de 40.303 = 10,77%, IC95% [10,47%; 11,07%]. "Top-k mostra exemplos; frequência vem de contagem com população definida." Gancho da aula: não afirmar que atraso causou a nota. | E, Dec |
| 6 | 4:30–5:15 | Recusa | Terminal: P15 política de reembolso | Status `sem_evidencia`: relato de cliente não estabelece política oficial. Falha do serviço aparece como `erro_geracao`, nunca como "não sei". | P, E |
| 7 | 5:15–6:05 | Decisões e desafios | Spec 0007 / trecho de código | (a) Prévia + hash: nenhum comentário sai sem leitura; (b) teto de 20 chamadas/dia; (c) citação validada contra o contexto. Desafio honesto: citação é por resposta, não por frase. | Dec |
| 8 | 6:05–6:30 | Limites e próximo passo | Slide de limites | Dados 2016–2018, viés de quem comenta, 2 exemplos não medem confiabilidade. Próximo: contar menções de "sem contato" para testar a pista. | N, Dec |

## Pendências antes de gravar

- **Bloco 6 sem execução real no CLI.** P15 só foi verificada no lote curado
  e no ensaio sintético. Opções: prévia + liberação de 1 chamada (orçamento) ou
  usar a captura do lote curado, declarando a origem.
- **Espera de ~3 min dos vetores** na demo: cortar na edição ou gravar com saída
  já pronta, sem esconder que existe a espera (dizer em uma frase).
- Slides dos blocos 1, 2 e 8: ferramenta e visual a decidir.
- Ensaio cronometrado: ler em voz alta e ajustar; se passar de 6:45, cortar o
  bloco 3 primeiro (detalhe fica no README).
