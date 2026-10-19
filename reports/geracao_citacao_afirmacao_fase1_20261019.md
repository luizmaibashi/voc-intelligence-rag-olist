# Rodada de citação por afirmação — fase 1, execução parcial

**Data UTC:** 2026-10-19. **Configuração:** `google-genai 1.75.0`, hash `203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3`, até duas tentativas para falha transitória. **Autorização:** Luiz liberou o hash após revisar a prévia dos 13 contextos. **Previsões anteriores às chamadas:** 17/20 casos sustentados; `N=3` falhas de contrato no lote completo. Captura bruta: `reports/geracao_citacao_afirmacao_fase1_20261019.jsonl`; orçamento local: `data/demo/execucoes.jsonl` (fora do Git).

## Ocorrência

E02, E03, E04, E06, E07, E08, E09, E10, E11 e E12 receberam duas tentativas cada. Todas falharam com `ConnectError`, sem saída do provedor. O script as rotulou `falha_servico`, mas a verificação direta encontrou bloqueio DNS no ambiente padrão (`Resolve-DnsName generativelanguage.googleapis.com`: **Acesso negado**); a mesma resolução DNS com execução escalada funcionou. A inferência operacional é bloqueio local de rede, sem evidência de indisponibilidade do serviço Gemini. Não houve corpo de resposta para julgar formato ou suporte de afirmações.

O ledger contabilizou **20/20 tentativas** no dia UTC e o avaliador parou antes de E14. E14, E15 e E18 não foram chamados. Nenhum caso será reenviado neste dia para contornar o teto. A fase 1 está **incompleta: 10/13 casos atribuídos tentados, 0 julgáveis, 3 não tentados**. `N` observado de falhas de contrato em saídas julgáveis é `0/0`; proporção e IC95% são indefinidos. O limiar de abandono dos 13 não foi avaliado e o gate continua pendente.

Antes de continuar, executar em ambiente com rede autorizada, conferir o saldo de 20 chamadas do novo dia UTC e preservar estas capturas. Repetir os dez casos com falha local exige registro explícito da reavaliação e mecanismo que não descarte o histórico nem exceda a cota; a execução original impede reenvio sob o mesmo hash. O prazo de 25/10/2026 continua valendo.

**Decisão posterior de Luiz:** autorizou uma reavaliação dos dez IDs acima e a primeira execução de E14/E15/E18, mantendo hash, escopo e teto. O avaliador ganhou opção específica `--reavaliar-falhas-locais`, que confere esta captura (SHA-256 `44c87c8f5ad60531b8172de85ab8d46767305b17b2d13c8cec4297445960a199`) e o ledger antes de permitir apenas um segundo envio. A prévia/hash não mudou; suíte com SDK 1.75.0: 263 testes aprovados. Em perfil de rede elevado, sem API nem chave, DNS resolveu 16 endereços e TLS 1.3 abriu; o preflight deve ser repetido no mesmo ambiente imediatamente antes do envio de 20/10 UTC.
