from __future__ import annotations

import pandas as pd
import pytest

from sinapi_limpeza.extract import detectar_layout, extrair, ler_aba_bruta, listar_abas


def test_listar_abas(xlsx_fake):
    abas = listar_abas(xlsx_fake)
    assert abas == ["ISD", "ICD"]


def test_ler_aba_bruta_arquivo_inexistente():
    with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
        ler_aba_bruta("arquivo_que_nao_existe.xlsx", "ISD")


def test_ler_aba_bruta_aba_inexistente(xlsx_fake):
    with pytest.raises(ValueError, match="Aba 'XYZ' não existe"):
        ler_aba_bruta(xlsx_fake, "XYZ")


def test_detectar_layout_acha_cabecalho_e_ufs(xlsx_fake):
    df = ler_aba_bruta(xlsx_fake, "ISD")
    layout = detectar_layout(df)
    assert layout["linha_cabecalho"] == 4
    assert layout["colunas"]["codigo"] == 1
    assert layout["colunas"]["descricao"] == 2
    assert layout["colunas"]["unidade"] == 3
    assert layout["ufs"][:4] == ["AC", "AL", "BA", "SP"]


def test_detectar_layout_falha_sem_cabecalho():
    df = pd.DataFrame([["sem", "valor"], ["sem", "outro"]])
    with pytest.raises(ValueError, match="Não foi possível detectar o cabeçalho"):
        detectar_layout(df)


def test_extrair_remove_linha_vazia_e_cabecalho_repetido(xlsx_fake):
    df = extrair(xlsx_fake, "ISD")
    assert "linha_origem" in df.columns
    assert len(df) == 12
    assert set(df.columns[:5]) == {"classificacao", "codigo", "descricao", "unidade", "origem_preco"}
