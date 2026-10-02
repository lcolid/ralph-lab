import csv
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
