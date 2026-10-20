from __future__ import annotations

import pandas as pd
import pytest

from sinapi_limpeza.extract import extrair
from sinapi_limpeza.transform import (
    converter_preco,
    normalizar_codigo,
    normalizar_nulos,
    normalizar_texto,
    normalizar_unidade,
    referencia_do_arquivo,
    regime_da_aba,
    limpar,
)


def test_normalizar_texto():
    assert normalizar_texto("  Concreto   de  base  ") == "Concreto de base"
    assert pd.isna(normalizar_texto("   "))


def test_normalizar_nulos():
    for valor in ["", "-", "N/A", "NA", "NULL", "NAN"]:
        assert pd.isna(normalizar_nulos(valor))
    assert normalizar_nulos("123") == "123"


def test_normalizar_codigo():
    assert normalizar_codigo(" 12345.0 ") == "12345"
    assert normalizar_codigo(" 001 ") == "001"
    assert pd.isna(normalizar_codigo("ABC"))


def test_converter_preco():
    assert converter_preco("1.234,56") == 1234.56
    assert converter_preco("12.5") == 12.5
    assert converter_preco("12") == 12.0
    assert pd.isna(converter_preco("abc"))


def test_normalizar_unidade():
    assert normalizar_unidade("M2") == "m²"
    assert normalizar_unidade("m²") == "m²"
    assert normalizar_unidade("UN") == "un"
    assert normalizar_unidade("cm") == "CM"


def test_regime_da_aba():
    assert regime_da_aba("ISD") == "sem_desoneracao"
    assert regime_da_aba("ICD") == "com_desoneracao"
    assert regime_da_aba("ISE") == "sem_encargos"
    with pytest.raises(ValueError, match="Só insumos são suportados"):
        regime_da_aba("XYZ")


def test_referencia_do_arquivo():
    assert referencia_do_arquivo("SINAPI_Referência_2026_02.xlsx") == "2026-02"
    assert referencia_do_arquivo("arquivo_sem_referencia.xlsx") is None


def test_rejeicao_por_codigo_invalido(xlsx_fake):
    df_largo = extrair(xlsx_fake, "ISD")
    _, rejeitado = limpar(df_largo, "BA", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert "codigo inválido" in "\n".join(rejeitado["motivo_rejeicao"].astype(str))


def test_rejeicao_por_preco_ausente(xlsx_fake):
    df_largo = extrair(xlsx_fake, "ISD")
    _, rejeitado = limpar(df_largo, "BA", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert "preço ausente para a UF" in "\n".join(rejeitado["motivo_rejeicao"].astype(str))


def test_rejeicao_por_preco_negativo(xlsx_fake):
    df_largo = extrair(xlsx_fake, "ISD")
    _, rejeitado = limpar(df_largo, "BA", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert "preço negativo ou zero" in "\n".join(rejeitado["motivo_rejeicao"].astype(str))


def test_rejeicao_por_duplicado(xlsx_fake):
    df_largo = extrair(xlsx_fake, "ISD")
    _, rejeitado = limpar(df_largo, "BA", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert "duplicado" in "\n".join(rejeitado["motivo_rejeicao"].astype(str))


def test_filtro_por_uf(xlsx_fake):
    df_largo = extrair(xlsx_fake, "ISD")
    df_valido, df_rejeitado = limpar(df_largo, "BA", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert set(df_valido["uf"]).issubset({"BA"})
    assert set(df_rejeitado["uf"]).issubset({"BA"})

    df_valido_todas, _ = limpar(df_largo, "TODAS", "sem_desoneracao", "2026-02", "SINAPI_Referência_2026_02.xlsx")
    assert set(df_valido_todas["uf"]).issuperset({"AC", "AL", "BA", "SP"})
