# PRD: Do CSV ao gráfico — receita por região

## Introdução
Pipeline que junta `vendas.csv` e `lojas.csv`, produz um pivot de receita por região × mês e publica uma página estática com gráfico e conclusão. O código é escrito pelo agente no laço Ralph; "pronto" é definido pela suíte `pytest`.

## Objetivos
- `vendas_lojas.csv` (inner join por `id_loja`) com 420 linhas e receita total 931274.06.
- `pivot_receita.csv` com 4 regiões × 6 meses (2026-01 a 2026-06), soma 931274.06.
- `index.html` com gráfico da receita mensal por região e parágrafo de conclusão (≥ 300 caracteres).
- Suíte `pytest` com pelo menos 4 testes, toda verde.

## Histórias
- US-001 Join: inner join por `id_loja`, mantendo a coluna `receita_brl`; as 3 vendas órfãs (`id_loja=999`, R$ 8.120,00) e a loja 108 (Batel/PR, sem vendas) ficam fora e isso é registrado no README.
- US-002 Pivot: receita por região × mês, cabeçalho exato `regiao,2026-01,...,2026-06`, 2 casas decimais com ponto, sem R$ nem separador de milhar; arredondar só na escrita.
- US-003 Página: `index.html` com `<svg>` ou `<canvas>` (Chart.js via CDN permitido) e um `<p>` de conclusão ≥ 300 caracteres citando Sudeste R$ 265.077,49 como líder.
- US-004 Testes e README: `tests/test_pipeline.py` com ≥ 4 testes; README explicando a escolha do join e o que ficou de fora.

## Restrições
- Não apagar nem alterar linhas de `vendas.csv`/`lojas.csv`; não inventar dados; ler `receita_brl` como número.
- Apenas biblioteca padrão do Python (csv, decimal) — sem pandas.
- Saídas na raiz do repo.

## Fora de escopo
- Servidor web, banco de dados, left/outer join como entrega.
