# Spec 0005 — Integridade dos filtros e do cache de embeddings

**Data:** 2026-10-06. **Dono da aprovação:** Luiz Maibashi.
**Escopo:** confirmado no chat antes das alterações.

## Objetivo

Evitar perda de evidências elegíveis por deduplicação prematura e associação
silenciosa de vetores antigos a textos diferentes. Preservar a demo da spec 0004.

## Contrato e aceitação

- O carregamento do corpus de busca preserva todas as avaliações e metadados.
- A busca filtra antes de agrupar textos iguais pela chave em minúsculas.
  Retorna até k textos distintos; representante por maior score e menor review_id
  em empate, escolhido dentro do recorte elegível. Testar nota, entrega, caixa,
  ordem de entrada e duplicatas que ocupariam todas as posições do top-k.
- O cache só é reutilizado com identidade dos textos em ordem, modelo configurado,
  prefixo, normalização, versão de sentence-transformers e dimensão compatíveis.
  Um digest dos vetores vincula o manifesto ao arquivo; cache legado, incompleto,
  corrompido ou incompatível avisa e regenera. Saída do encoder inválida falha.
- A calibração usa explicitamente os textos distintos do pooling e a mesma função
  de cache validado; não associa o cache distinto ao corpus completo de busca.
- Testes sintéticos falham antes e passam depois da correção. Rodar a suíte local
  e revisar diff sem regenerar o pool julgado nem modificar os dados reais.

## Limites e riscos

Sem troca de provedor, envio externo, publicação, medição de desempenho ou
reavaliação da qualidade histórica. Nome de modelo não fixa revisão dos pesos
remotos; uma troca conhecida de pesos sob o mesmo nome exige invalidar o cache.
Gabarito e ranking P09 permanecem preservados. A correção pode alterar resultados
de busca com filtros; métricas antigas não são revalidadas por testes sintéticos.

## Evidência

Reprodução prévia: busca esperava ID b (nota 5/no_prazo), recebeu vazio; cache
esperava vetor do texto novo [0,1], recebeu vetor antigo [1,0]. Usados somente
comentários sintéticos, DuckDB local e encoder determinístico sem rede.
Resultado final e comandos serão registrados em reports/integridade_busca_cache.md.
