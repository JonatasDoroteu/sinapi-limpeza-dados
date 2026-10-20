from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def xlsx_fake(tmp_path: Path) -> Path:
    arquivo = tmp_path / "SINAPI_Referência_2026_02.xlsx"
    abas = {
        "ISD": [
            ["Metadado", "", "", "", ""],
            ["resumo", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["Classificação", "Código", "Descrição", "Unidade", "Origem de Preço", "AC", "AL", "BA", "SP"],
            ["Material", "123", "Concreto  de  base", "M2", "C", 100, 110, "1.234,56", 220],
            ["Material", "12345.0", "Cimento  Portland", "m²", "CR", 10, 11, "12.5", 12],
            ["Material", "456", "Areia   lavada", "UN", "AS", 50, 60, "-", 70],
            ["Material", "789", "Argamassa", "KG", "C", 80, 90, "abc", 100],
            ["Material", "790", "Sem    preço", "L", "C", None, None, "", 1],
            ["Material", "791", "Preço  negativo", "M", "C", 5, 5, "-123,45", 5],
            ["Material", "ABC", "Código inválido", "M", "C", 5, 5, 5, 5],
            ["Material", " 001 ", "Piso  cerâmico", "M3", "AS", 44, 45, 46, 47],
            ["Material", "2222", "Descrição  com  espacos", "M3", "AS", "1.234", 200, "2.500,00", 220],
            ["Material", "123", "Duplicado  código", "M2", "C", 90, 100, "1.000,00", 110],
            ["Material", "9999", "Balde", "H", "C", None, None, "12.5", None],
            ["", "", "", "", "", "", "", "", ""],
            ["Classificação", "Código", "Descrição", "Unidade", "Origem de Preço", "AC", "AL", "BA", "SP"],
            ["Material", "1000", "Linha  repetida", "M", "C", 10, 11, 12, 13],
        ],
        "ICD": [
            ["Titulo", "", "", "", ""],
            ["Classificação", "Código", "Descrição", "Unidade", "Origem de Preço", "AC", "AL", "BA", "SP"],
            ["Material", "2000", "Cimento  de  alta", "M2", "CR", 1, 2, 3, 4],
        ],
    }

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        for nome_aba, linhas in abas.items():
            pd.DataFrame(linhas).to_excel(writer, sheet_name=nome_aba, index=False, header=False)
    return arquivo
