import csv
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import pipeline  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def rodar_pipeline():
    pipeline.main()


def ler(nome):
    with (RAIZ / nome).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_vendas_lojas_tem_420_linhas():
    assert len(ler("vendas_lojas.csv")) == 420


def test_receita_total_do_join():
    linhas = ler("vendas_lojas.csv")
    total = sum(Decimal(l["receita_brl"]) for l in linhas)
    assert abs(total - Decimal("931274.06")) <= Decimal("0.50")


def test_orfas_e_loja_108_fora_do_join():
    linhas = ler("vendas_lojas.csv")
    assert not {"V00421", "V00422", "V00423"} & {l["id_venda"] for l in linhas}
    assert "108" not in {l["id_loja"] for l in linhas}


def ler_linhas(nome):
    with (RAIZ / nome).open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_pivot_cabecalho():
    assert ler_linhas("pivot_receita.csv")[0] == [
        "regiao", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]


def test_pivot_forma_4x7_regioes_ordenadas():
    dados = ler_linhas("pivot_receita.csv")[1:]
    assert len(dados) == 4
    assert all(len(l) == 7 for l in dados)
    assert [l[0] for l in dados] == ["Centro-Oeste", "Nordeste", "Sudeste", "Sul"]


def test_pivot_total_e_formato():
    dados = ler_linhas("pivot_receita.csv")[1:]
    celulas = [c for l in dados for c in l[1:]]
    assert all(re.fullmatch(r"\d+\.\d{2}", c) for c in celulas)
    total = sum(Decimal(c) for c in celulas)
    assert abs(total - Decimal("931274.06")) <= Decimal("0.50")


def ler_index():
    return (RAIZ / "index.html").read_text(encoding="utf-8")


def test_index_tem_grafico():
    pagina = ler_index()
    assert "<svg" in pagina or ("<canvas" in pagina and "chart.js" in pagina.lower())


def test_index_conclusao_300_caracteres():
    pagina = ler_index()
    paragrafos = re.findall(r"<p[^>]*>(.*?)</p>", pagina, re.S)
    longos = [p for p in paragrafos if len(p) >= 300]
    assert longos
    texto = longos[0]
    assert "R$ 931.274,06" in texto
    assert "Sudeste" in texto and "R$ 265.077,49" in texto
    assert "3 vendas órfãs" in texto and "R$ 8.120,00" in texto
    assert "108" in texto


def test_readme_documenta_join_e_exclusoes():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    for trecho in ["python3 pipeline.py", "python3 -m pytest -q", "INNER JOIN",
                   "423", "420", "8.120,00", "108", "931274.06", "939394.06"]:
        assert trecho in texto
