# Spec 0002 — Frequência de atraso entre avaliações com comentário

**Dono da decisão:** Luiz Maibashi. **Status:** aprovado para implementação local em 2026-09-28.

## Objetivo e escopo

Demonstrar uma pergunta de frequência verificável sobre o corpus inteiro, sem
inferir prevalência a partir dos dez resultados da busca. Contar `review_id`
únicos com comentário e pedido entregue; numerador é `situacao_entrega ==
"atrasado"`, denominador inclui `"atrasado"` e `"no_prazo"`. Informar também
contagens, intervalo das datas de compra e IC95% de Wilson para a proporção.

Esta primeira pergunta é adicional às P05, P08, P09 e P11. Não classifica
motivos de reclamação, produtos danificados nem resposta da loja. Não permite
extrapolar para pedidos sem comentário ou para o período atual.

## Contrato e aceitação

- Entrada: corpus processado com `review_id`, `texto`, `situacao_entrega` e `data_compra`.
- Exigir `texto` não vazio para preservar a população de avaliações com comentário.
- Exigir IDs únicos, estados conhecidos e datas válidas para os entregues.
  Entrada sem contrato falha visivelmente.
- Se não houver pedidos entregues no recorte, falhar com erro explícito, sem
  dividir por zero nem inventar porcentagem.
- Saída: numerador, denominador, proporção, IC95% e datas mínima/máxima de
  compra. A mensagem para demo sempre inclui o denominador e o período.
- Teste com fixture pequena, incluindo não entregue, e confronto com contagem
  independente do Pandas. Regressão deve falhar se remover filtro ou denominador.

## Risco e validação

O corpus cobre só avaliações com comentário; há viés de seleção. A coluna
`situacao_entrega` é derivada em `src/preprocessing/corpus.py`. Toda a
computação é local e não envia textos para serviços externos. Luiz revisa o
diff e aprova eventual publicação; testes validam aritmética, não
representatividade dos pedidos da Olist. O IC descreve incerteza amostral
sob um modelo hipotético; não corrige o viés de quem comenta.
