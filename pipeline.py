"""Pipeline do CSV ao gráfico: vendas.csv + lojas.csv -> vendas_lojas.csv -> pivot_receita.csv -> index.html."""
import csv
import html
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENDAS = RAIZ / "vendas.csv"
LOJAS = RAIZ / "lojas.csv"
VENDAS_LOJAS = RAIZ / "vendas_lojas.csv"
PIVOT = RAIZ / "pivot_receita.csv"
INDEX = RAIZ / "index.html"

# Paleta categórica (slots 1-4, ordem fixa por região em ordem alfabética)
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CORES_ESCURO = ["#3987e5", "#d95926", "#199e70", "#c98500"]


def ler_csv(caminho):
    with caminho.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def inner_join(vendas, lojas):
    """INNER JOIN por id_loja; devolve (linhas unidas, vendas órfãs)."""
    por_id = {loja["id_loja"]: loja for loja in lojas}
    unidas, orfas = [], []
    for venda in vendas:
        loja = por_id.get(venda["id_loja"])
        if loja is None:
            orfas.append(venda)
            continue
        unidas.append({
            **venda,
            "nome_loja": loja["nome_loja"],
            "regiao": loja["regiao"],
            "uf": loja["uf"],
        })
    return unidas, orfas


def soma_receita(linhas):
    return sum((Decimal(l["receita_brl"]) for l in linhas), Decimal("0"))


def gravar_csv(caminho, linhas, campos):
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def pivot_receita(linhas):
    """Receita por região × mês (AAAA-MM); devolve (meses, {regiao: {mes: Decimal}})."""
    meses = sorted({l["data"][:7] for l in linhas})
    pivot = {}
    for l in linhas:
        por_mes = pivot.setdefault(l["regiao"], {m: Decimal("0") for m in meses})
        por_mes[l["data"][:7]] += Decimal(l["receita_brl"])
    return meses, pivot


def gravar_pivot(caminho, meses, pivot):
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["regiao"] + meses)
        for regiao in sorted(pivot):
            w.writerow([regiao] + [f"{pivot[regiao][m]:.2f}" for m in meses])


def ler_pivot(caminho):
    """Lê pivot_receita.csv de volta para (meses, {regiao: {mes: Decimal}})."""
    with caminho.open(newline="", encoding="utf-8") as f:
        linhas = list(csv.reader(f))
    meses = linhas[0][1:]
    pivot = {l[0]: dict(zip(meses, map(Decimal, l[1:]))) for l in linhas[1:]}
    return meses, pivot


def brl(valor):
    """Formata Decimal como R$ 1.234,56."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def svg_linhas(meses, pivot, largura=720, altura=360):
    """Gráfico de linhas (SVG inline) da receita mensal por região."""
    esq, dir_, topo, base = 80, 120, 20, 40
    regioes = sorted(pivot)
    maximo = max(v for r in regioes for v in pivot[r].values())
    passo = Decimal("10000")
    teto = -(-maximo // passo) * passo
    larg_util, alt_util = largura - esq - dir_, altura - topo - base

    def x(i):
        return esq + larg_util * i / (len(meses) - 1)

    def y(v):
        return topo + alt_util * (1 - float(v / teto))

    partes = [f'<svg viewBox="0 0 {largura} {altura}" role="img" '
              f'aria-label="Receita mensal por região (R$)">']
    for k in range(int(teto / passo) + 1):
        v = passo * k
        partes.append(f'<line class="grade" x1="{esq}" x2="{largura - dir_}" '
                      f'y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        partes.append(f'<text class="eixo" x="{esq - 8}" y="{y(v) + 4:.1f}" '
                      f'text-anchor="end">{int(v / 1000)} mil</text>')
    for i, m in enumerate(meses):
        partes.append(f'<text class="eixo" x="{x(i):.1f}" y="{altura - base + 20}" '
                      f'text-anchor="middle">{m}</text>')
    for n, regiao in enumerate(regioes):
        pontos = [(x(i), y(pivot[regiao][m])) for i, m in enumerate(meses)]
        caminho = " ".join(f"{px:.1f},{py:.1f}" for px, py in pontos)
        partes.append(f'<g class="serie" style="--cor: var(--series-{n + 1})">')
        partes.append(f'<polyline points="{caminho}"/>')
        for (px, py), m in zip(pontos, meses):
            dica = html.escape(f"{regiao} · {m}: {brl(pivot[regiao][m])}")
            partes.append(f'<g class="ponto"><circle class="alvo" cx="{px:.1f}" cy="{py:.1f}" r="12"/>'
                          f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4"/><title>{dica}</title></g>')
        partes.append(f'<text class="rotulo" x="{pontos[-1][0] + 10:.1f}" '
                      f'y="{pontos[-1][1] + 4:.1f}">{html.escape(regiao)}</text>')
        partes.append("</g>")
    partes.append("</svg>")
    return "\n".join(partes)


def conclusao(meses, pivot, n_vendas, unidas, orfas, lojas_sem_venda):
    totais = {r: sum(pivot[r].values(), Decimal("0")) for r in pivot}
    lider = max(totais, key=totais.get)
    total = sum(totais.values(), Decimal("0"))
    pct = f"{totais[lider] * 100 / total:.1f}%".replace(".", ",")
    sem_venda = ", ".join(f"{l['id_loja']} ({l['nome_loja']}/{l['uf']})" for l in lojas_sem_venda)
    return (
        f"Entre {meses[0]} e {meses[-1]}, o inner join de vendas com lojas somou "
        f"{brl(total)} de receita em {len(unidas)} das {n_vendas} vendas registradas. "
        f"A região líder foi o {lider}, com {brl(totais[lider])} no semestre "
        f"({pct} do total). "
        f"Ficaram fora do relatório {len(orfas)} vendas órfãs, cujo id_loja não existe "
        f"no cadastro de lojas ({brl(soma_receita(orfas))} descartados), e a loja "
        f"{sem_venda}, que não teve nenhuma venda no período e por isso não entra no join."
    )


def gravar_index(caminho, meses, pivot, texto):
    regioes = sorted(pivot)
    legenda = "".join(
        f'<li><span class="chave" style="background: var(--series-{n + 1})"></span>'
        f"{html.escape(r)}</li>" for n, r in enumerate(regioes))
    cab = "".join(f"<th>{m}</th>" for m in meses)
    corpo = "".join(
        f"<tr><th>{html.escape(r)}</th>"
        + "".join(f"<td>{brl(pivot[r][m])}</td>" for m in meses) + "</tr>"
        for r in regioes)
    cores = "\n".join(f"  --series-{n + 1}: {c};" for n, c in enumerate(CORES))
    cores_escuro = "\n".join(f"    --series-{n + 1}: {c};" for n, c in enumerate(CORES_ESCURO))
    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Receita mensal por região</title>
<style>
.viz-root {{
  color-scheme: light;
  --surface-1: #fcfcfb;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --grid: #e4e3df;
{cores}
}}
@media (prefers-color-scheme: dark) {{
  .viz-root {{
    color-scheme: dark;
    --surface-1: #1a1a19;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --grid: #3a3a37;
{cores_escuro}
  }}
}}
body {{ margin: 0; }}
.viz-root {{ background: var(--surface-1); color: var(--text-primary);
  font-family: system-ui, sans-serif; max-width: 760px; margin: 0 auto; padding: 24px; min-height: 100vh; }}
h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
.sub {{ color: var(--text-secondary); margin: 0 0 16px; }}
.legenda {{ list-style: none; display: flex; gap: 16px; padding: 0; margin: 0 0 8px; color: var(--text-secondary); }}
.chave {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }}
svg {{ width: 100%; height: auto; }}
.grade {{ stroke: var(--grid); stroke-width: 1; }}
.eixo {{ fill: var(--text-secondary); font-size: 12px; }}
.rotulo {{ fill: var(--text-primary); font-size: 12px; }}
.serie polyline {{ fill: none; stroke: var(--cor); stroke-width: 2; stroke-linejoin: round; }}
.serie circle {{ fill: var(--cor); stroke: var(--surface-1); stroke-width: 2; }}
.serie circle.alvo {{ fill: transparent; stroke: none; }}
.ponto:hover circle:not(.alvo) {{ r: 6; }}
table {{ border-collapse: collapse; font-size: 0.85rem; width: 100%; margin-top: 8px; }}
th, td {{ padding: 4px 6px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child {{ text-align: left; }}
details {{ margin: 8px 0 16px; color: var(--text-secondary); }}
p.conclusao {{ line-height: 1.5; }}
</style>
</head>
<body>
<main class="viz-root">
<h1>Receita mensal por região</h1>
<p class="sub">Vendas com loja cadastrada (inner join), {meses[0]} a {meses[-1]}, em R$</p>
<ul class="legenda">{legenda}</ul>
{svg_linhas(meses, pivot)}
<details><summary>Ver tabela</summary>
<table><thead><tr><th>Região</th>{cab}</tr></thead><tbody>{corpo}</tbody></table>
</details>
<p class="conclusao">{html.escape(texto)}</p>
</main>
</body>
</html>
"""
    caminho.write_text(pagina, encoding="utf-8")


def main():
    vendas = ler_csv(VENDAS)
    lojas = ler_csv(LOJAS)
    unidas, orfas = inner_join(vendas, lojas)
    campos = list(vendas[0].keys()) + ["nome_loja", "regiao", "uf"]
    gravar_csv(VENDAS_LOJAS, unidas, campos)
    meses, pivot = pivot_receita(ler_csv(VENDAS_LOJAS))
    gravar_pivot(PIVOT, meses, pivot)
    meses, pivot = ler_pivot(PIVOT)
    com_venda = {l["id_loja"] for l in unidas}
    sem_venda = [l for l in lojas if l["id_loja"] not in com_venda]
    texto = conclusao(meses, pivot, len(vendas), unidas, orfas, sem_venda)
    gravar_index(INDEX, meses, pivot, texto)

    print(f"Vendas de entrada: {len(vendas)}")
    print(f"Linhas após inner join: {len(unidas)}")
    print(f"Vendas órfãs descartadas: {len(orfas)} "
          f"(receita descartada: R$ {soma_receita(orfas):.2f})")
    print(f"Receita total no join: {soma_receita(unidas):.2f}")


if __name__ == "__main__":
    main()
