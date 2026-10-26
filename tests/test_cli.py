from __future__ import annotations

import pandas as pd

from sinapi_limpeza.cli import main


def test_cli_gera_csvs_e_totais(xlsx_fake, tmp_path):
    saida = tmp_path / "out"
    codigo = main([
        "--entrada",
        str(xlsx_fake),
        "--aba",
        "ISD",
        "--uf",
        "BA",
        "--referencia",
        "2026-02",
        "--saida",
        str(saida),
    ])
    assert codigo == 0
    csv_validos = pd.read_csv(saida / "insumos_limpos.csv", sep=';')
    csv_rejeitados = pd.read_csv(saida / "rejeitados.csv", sep=';')
    assert not csv_validos.empty
    assert len(csv_validos) + len(csv_rejeitados) > 0
    csv_validos_texto = pd.read_csv(
        saida / "insumos_limpos.csv", sep=";", encoding="utf-8-sig", dtype=str
    )
    assert "preco_centavos" not in csv_validos_texto.columns
    assert csv_validos_texto.loc[csv_validos_texto["codigo"] == "12345", "preco"].iloc[0] == "12,50"
    csv_rejeitados_texto = pd.read_csv(
        saida / "rejeitados.csv", sep=";", encoding="utf-8-sig", dtype=str
    )
    assert csv_rejeitados_texto.loc[
        csv_rejeitados_texto["codigo"] == "789", "preco_original"
    ].iloc[0] == "abc"


def test_cli_uf_inexistente_informa_ufs_disponiveis(xlsx_fake, tmp_path, capsys):
    saida = tmp_path / "out"
    codigo = main(
        [
            "--entrada",
            str(xlsx_fake),
            "--aba",
            "ISD",
            "--uf",
            "ZZ",
            "--saida",
            str(saida),
        ]
    )

    capturado = capsys.readouterr()
    assert codigo == 1
    assert capturado.out == ""
    assert (
        capturado.err
        == "Erro: UF 'ZZ' não existe na planilha. UFs disponíveis: AC, AL, BA, SP\n"
    )
    assert not saida.exists()


def test_cli_inspecionar_nao_grava_arquivos(xlsx_fake, tmp_path, capsys):
    saida = tmp_path / "nao_deve_criar"
    codigo = main([
        "--entrada",
        str(xlsx_fake),
        "--aba",
        "ISD",
        "--uf",
        "BA",
        "--saida",
        str(saida),
        "--inspecionar",
    ])
    capturado = capsys.readouterr()
    assert codigo == 0
    assert "Abas:" in capturado.out
    assert not (saida / "insumos_limpos.csv").exists()
    assert not (saida / "rejeitados.csv").exists()
