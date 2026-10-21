# Comando da fase 2 — spec 0008

Origem: bloco 3 do relatório REENVIO-02 do Codex (código auditado em `8f6cd4f`), com
`Set-Location` acrescentado. Rodar no PowerShell 5.1 **só a partir de 21/10 UTC**
(00:00Z = 21:00 de Brasília). Antes de rodar: Luiz registra a previsão
(quantos dos 7 aprovados; quantas das 4 recusas E13/E16/E19/E20 corretas).

Pré-condição verificada em 20/10: os 13 pareáveis têm resultado (E02 e E18 voltaram
nos reenvios; `reports/ficha_julgamento_fase1_20261020.jsonl` aprovada 13/13).
Reserva: lote 1 = 8 chamadas, lote 2 = 4 (E20 não chama API); cabe na cota de 20.
Não apertar Ctrl+C durante uma chamada: deixa envio sem resultado no ledger.

> Registro histórico: o caminho é da máquina original. Para reproduzir, ajuste-o para a raiz do seu clone.
```powershell
& {
    $ErrorActionPreference = 'Stop'
    Set-Location 'C:\Users\Tchan\Documents\Base_de_Conhecimento\PROJETOS\01_PRIORITY\Tech_challenge_fase4'
    $env:PYTHONPATH = '.venv/sdk175'
    if (([datetime]::UtcNow).ToString('yyyy-MM-dd') -le '2026-10-20') { throw 'Fase 2 proibida em 20/10 UTC.' }
    $lotes = @(@('E01','E05','E13','E16'), @('E17','E19','E20'))
    $numero = 0
    foreach ($lote in $lotes) {
        $numero++
        $ids = $lote -join ','
        $saida = "reports/geracao_citacao_afirmacao_fase2_lote${numero}.jsonl"
        $usadas = python -c "from datetime import datetime,timezone; from pathlib import Path; from src.rag import liberacao; print(liberacao.chamadas_no_dia(Path('data/demo/execucoes.jsonl'),datetime.now(timezone.utc)))"
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível ler a cota.' }
        Write-Host "Lote $numero — cota antes: $usadas/20"
        $reserva = 2 * @($lote | Where-Object { $_ -ne 'E20' }).Count
        if ([int]$usadas + $reserva -gt 20) { throw "Cota insuficiente para lote $numero." }
        python -m src.eval.avaliar_geracao --manifesto data/eval/geracao_casos.json --executar --repetir-transitorios --aprovacao-sha256 203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3 --previsao 17 --previsao-falhas-contrato 3 --ids $ids --saida $saida
        if ($LASTEXITCODE -ne 0) { throw "Lote $numero recusado." }
        python -c "import json,sys; esperado=set(sys.argv[2].split(',')); l=[json.loads(x) for x in open(sys.argv[1],encoding='utf-8')]; c=[x for x in l if x.get('tipo')=='caso']; assert {x['id'] for x in c}==esperado and all(x.get('saida_provedor') is not None or x['id']=='E20' for x in c), 'caso não tentado ou sem saída'" $saida $ids
        if ($LASTEXITCODE -ne 0) { throw "Pare: lote $numero incompleto ou sem saída." }
        $usadas = python -c "from datetime import datetime,timezone; from pathlib import Path; from src.rag import liberacao; print(liberacao.chamadas_no_dia(Path('data/demo/execucoes.jsonl'),datetime.now(timezone.utc)))"
        Write-Host "Lote $numero — cota depois: $usadas/20"
    }
}
```

Depois: gerar ficha **nova** (`--saida` recusa sobrescrever) com todas as capturas:
`reports/geracao_citacao_afirmacao_fase1_20261019.jsonl`, `reports/geracao_citacao_afirmacao_f1_*20261020*.jsonl`,
`reports/geracao_reenvio_e02_20261020.jsonl`, `reports/geracao_reenvio_e18_20261020.jsonl` e os dois lotes da fase 2.
O gerador usa a captura mais recente por caso e sai **sem julgamento**. Copiar os
13 julgamentos com `python scripts/copiar_julgamentos.py reports/ficha_julgamento_fase1_20261020.jsonl <ficha_nova> <ficha_com_julgamentos>`;
o script confere `(id, ordem)` e frase idêntica antes de gravar. Julgar os sete
casos restantes, incluindo `julgamento_controle` de E20, e rodar
`python -m src.eval.ficha_julgamento --validar <ficha>`: código 0 fecha o gate
em 20/20 aprovados; código 4 mantém o gate aberto por pendência ou reprovação.
