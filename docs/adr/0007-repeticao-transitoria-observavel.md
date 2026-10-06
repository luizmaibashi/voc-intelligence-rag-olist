# ADR-0007 — Uma repetição transitória explícita e observável

**Data:** 2026-10-06. **Status:** Accepted para implementação/diagnóstico pelo Luiz no chat (“vamos la”); liberação da demo permanece bloqueada.

## Contexto

Rodada 03: oito falhas de serviço em 20 casos (seis HTTP 503, dois timeouts).
Diagnóstico de duas consultas sintéticas: uma HTTP 503, outra recusou corretamente.
Falhas aparecem mesmo sem retrieval e com texto curto. Isso não prova incidente
global, superioridade de outro modelo ou confiabilidade semântica geral.

## Decisão

Adicionar controlador compartilhado de tentativas, habilitado explicitamente
no executor com `--repetir-transitorios`. Padrão sem flag preserva uma tentativa
e o hash/configuração das rodadas anteriores. SDK sempre com attempts=1.

Com a flag: no máximo duas chamadas por consulta, espera fixa de 2s antes da
segunda, apenas para Google APIError HTTP 408/429/500/502/503/504 ou httpx
TimeoutException/NetworkError/RemoteProtocolError. Demais exceções, JSON inválido,
status/citação inválidos ou recusa não disparam repetição. Nenhum fallback.
Uma única espera não constitui backoff exponencial completo; sem concorrência
neste protótipo, não adicionar jitter ou circuit breaker sem sinal de necessidade.

Cada tentativa é gravada imediatamente em registro próprio com ID do caso,
número, saída ou classe/código seguro do erro, duração observada e espera
planejada. Retorno final preserva histórico mesmo quando a segunda funciona.
Não gravar mensagem de exceção, headers, stack ou chave. SDK timeout=25s por
chamada; orçamento nominal até 52s (2×25+2), sem promessa de deadline global
rígido da função ou de cobrança única em timeout.

## Motivo de negócio e trade-offs

Tentar concluir a demo sem trocar provedor/modelo ou ocultar sua instabilidade.
Até 38 chamadas externas por lote E01–E20, contra 19 sem repetição; no diagnóstico
de dois casos, até quatro chamadas. Benefício de disponibilidade ainda não medido.
Espera e possível consumo adicional são explícitos. Se serviço continuar falhando,
retornar erro visível e rever decisão; não aumentar tentativas continuamente.

Alternativas: manter tentativa única preserva baseline (continua disponível);
retry automático do SDK oculta as tentativas intermediárias; fallback troca
modelo e mistura qualidade; timeout maior não resolve HTTP 503. Não escolhidas
para este diagnóstico. Sem ganho financeiro estimado ou atualização de dependência.

## Validação e revisão

Testar erro transitório seguido de sucesso, duas falhas, erro permanente, saída
malformada, recusa, falha de registro, contexto vazio, interrupção e ausência de
segredos. Hash antigo deve rejeitar modo novo antes de arquivo/cliente. Preservar
regressões antigas. Diagnóstico sintético exige previsão antes de chamadas.
Se persistir falha, não repetir lote real; avaliar mudança com evidência própria.

## Referências

- Spec 0006, ADR-0006 e reports/geracao_20261006_evidencias.json.
- https://ai.google.dev/gemini-api/docs/troubleshooting (retry limitado para transitórios).
- Wiki Resiliencia_Industrial_LLMs: aplicar filtragem/limites; fallback e self-healing ficam fora do escopo.
