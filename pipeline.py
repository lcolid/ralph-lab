"""Pipeline do CSV ao gráfico: vendas.csv + lojas.csv -> vendas_lojas.csv."""
import csv
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENDAS = RAIZ / "vendas.csv"
LOJAS = RAIZ / "lojas.csv"
VENDAS_LOJAS = RAIZ / "vendas_lojas.csv"


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


def main():
    vendas = ler_csv(VENDAS)
    lojas = ler_csv(LOJAS)
    unidas, orfas = inner_join(vendas, lojas)
    campos = list(vendas[0].keys()) + ["nome_loja", "regiao", "uf"]
    gravar_csv(VENDAS_LOJAS, unidas, campos)

    print(f"Vendas de entrada: {len(vendas)}")
    print(f"Linhas após inner join: {len(unidas)}")
    print(f"Vendas órfãs descartadas: {len(orfas)} "
          f"(receita descartada: R$ {soma_receita(orfas):.2f})")
    print(f"Receita total no join: {soma_receita(unidas):.2f}")


if __name__ == "__main__":
    main()
