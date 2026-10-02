# ralph-lab — do CSV ao gráfico

Pipeline que cruza `vendas.csv` com `lojas.csv`, agrega a receita por região × mês
e publica uma página estática com gráfico e conclusão. Usa só a biblioteca padrão
do Python (`csv`, `decimal`, `pathlib`, `html`).

## Como rodar

```bash
python3 pipeline.py       # gera vendas_lojas.csv, pivot_receita.csv e index.html na raiz
python3 -m pytest -q      # roda a suíte de testes
```

Depois, abra `index.html` no navegador.

| Arquivo              | Conteúdo                                                        |
|----------------------|-----------------------------------------------------------------|
| `vendas_lojas.csv`   | vendas enriquecidas com `nome_loja`, `regiao` e `uf` (inner join) |
| `pivot_receita.csv`  | receita por região (linhas) × mês 2026-01 a 2026-06 (colunas)   |
| `index.html`         | gráfico de linhas em SVG inline + conclusão gerada dos dados    |

Os arquivos de entrada `vendas.csv` e `lojas.csv` nunca são alterados.

## Por que inner join

A pergunta do relatório é "quanto cada região faturou". Uma venda só tem região
se a loja dela existe no cadastro, então o join certo é o **INNER JOIN por
`id_loja`**:

- Um *left join* a partir de vendas manteria as vendas órfãs com região vazia —
  elas inflariam o total sem poder ser atribuídas a nenhuma região do pivot.
- Um *right/outer join* a partir de lojas traria a loja sem vendas como uma linha
  de receita nula, sem acrescentar nada à soma.

Com o inner join, o total do relatório é exatamente a soma das células do pivot.

## O que ficou de fora (armadilhas)

| Etapa                              | Linhas | Receita (R$)  |
|------------------------------------|-------:|--------------:|
| `vendas.csv` (entrada)             |    423 |    939394.06  |
| Vendas órfãs descartadas           |      3 |      8120.00  |
| `vendas_lojas.csv` (após o join)   |    420 |    931274.06  |

- **3 vendas órfãs**: V00421, V00422 e V00423 têm `id_loja=999`, que não existe em
  `lojas.csv`. Somam R$ 8.120,00 e são descartadas — o pipeline imprime essa
  contagem e o valor no terminal a cada execução.
- **Loja 108 (Batel/PR) sem vendas**: está no cadastro, mas não tem nenhuma venda
  no período; por isso não aparece no join nem no relatório. A região Sul continua
  presente por causa da loja 107 (Moinhos/RS).
- **Receita total**: 931274.06 dos 939394.06 de entrada.
- **Números como texto**: algumas vendas vêm sem casas decimais (ex.: `1200`).
  A receita é lida com `decimal.Decimal` e só é arredondada para 2 casas na
  escrita dos CSVs, evitando erro de ponto flutuante na soma.
