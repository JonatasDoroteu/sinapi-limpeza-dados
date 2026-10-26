from __future__ import annotations

from decimal import Decimal

import duckdb
import pytest

from sinapi_limpeza.cli import main
from sinapi_limpeza.extract import extrair
from sinapi_limpeza.load import carregar
from sinapi_limpeza.transform import limpar


def _limpar_fixture(xlsx_fake):
    df_largo = extrair(str(xlsx_fake), "ISD")
    df_valido, df_rejeitado = limpar(
        df_largo,
        "BA",
        "sem_desoneracao",
        "2026-02",
        xlsx_fake.name,
    )
    return df_largo, df_valido, df_rejeitado


def _consultar(caminho_banco, consulta, parametros=()):
    conexao = duckdb.connect(str(caminho_banco), read_only=True)
    try:
        return conexao.execute(consulta, parametros).fetchall()
    finally:
        conexao.close()


def test_carregar_cria_tabelas_e_grava_registros_especificos(xlsx_fake, tmp_path):
    _, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    caminho_banco = tmp_path / "sinapi.duckdb"

    assert carregar(
        df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao"
    ) == 0

    tabelas = {
        linha[0]
        for linha in _consultar(
            caminho_banco,
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'",
        )
    }
    assert {"dim_insumo", "fato_preco", "fato_rejeicao"}.issubset(tabelas)

    tipo_preco = _consultar(
        caminho_banco,
        "SELECT data_type, numeric_precision, numeric_scale "
        "FROM information_schema.columns "
        "WHERE table_name = 'fato_preco' AND column_name = 'preco'",
    )
    assert tipo_preco == [("DECIMAL(12,2)", 12, 2)]

    preco_codigo_com_zero = _consultar(
        caminho_banco,
        "SELECT codigo, preco FROM fato_preco WHERE codigo = '001' AND uf = 'BA'",
    )
    assert preco_codigo_com_zero == [("001", 46.0)]

    rejeicao_codigo_invalido = _consultar(
        caminho_banco,
        "SELECT codigo, motivo_rejeicao FROM fato_rejeicao "
        "WHERE codigo = 'ABC' AND uf = 'BA'",
    )
    assert rejeicao_codigo_invalido == [("ABC", "codigo inválido")]


def test_carregar_preco_grande_sem_perda_de_centavos(xlsx_fake, tmp_path):
    _, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    df_valido.loc[df_valido.index[0], "preco_centavos"] = 48855928
    caminho_banco = tmp_path / "sinapi.duckdb"

    carregar(df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao")

    preco = _consultar(
        caminho_banco,
        "SELECT preco FROM fato_preco WHERE codigo = '123' AND uf = 'BA'",
    )
    assert preco == [(Decimal("488559.28"),)]


def test_recarregar_mesmo_recorte_nao_duplica(xlsx_fake, tmp_path):
    _, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    caminho_banco = tmp_path / "sinapi.duckdb"

    for _ in range(2):
        carregar(
            df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao"
        )

    totais = _consultar(
        caminho_banco,
        "SELECT "
        "(SELECT COUNT(*) FROM fato_preco WHERE referencia = '2026-02' AND uf = 'BA'), "
        "(SELECT COUNT(*) FROM fato_rejeicao WHERE referencia = '2026-02' AND uf = 'BA')",
    )
    assert totais == [(len(df_valido), len(df_rejeitado))]

    duplicado = _consultar(
        caminho_banco,
        "SELECT codigo, motivo_rejeicao FROM fato_rejeicao "
        "WHERE codigo = '123' AND uf = 'BA'",
    )
    assert duplicado == [("123", "duplicado")]


def test_validos_mais_rejeitados_somam_entrada_e_preservam_motivos(
    xlsx_fake, tmp_path
):
    df_largo, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    caminho_banco = tmp_path / "sinapi.duckdb"
    carregar(
        df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao"
    )

    totais = _consultar(
        caminho_banco,
        "SELECT "
        "(SELECT COUNT(*) FROM fato_preco WHERE referencia = '2026-02' AND uf = 'BA'), "
        "(SELECT COUNT(*) FROM fato_rejeicao WHERE referencia = '2026-02' AND uf = 'BA')",
    )[0]
    assert sum(totais) == len(df_largo)

    rejeicao_preco_ausente = _consultar(
        caminho_banco,
        "SELECT codigo, motivo_rejeicao FROM fato_rejeicao "
        "WHERE codigo = '456' AND uf = 'BA'",
    )
    assert rejeicao_preco_ausente == [
        ("456", "preço ausente para a UF")
    ]


def test_conflito_de_dimensao_registrado_sem_sobrescrever(
    xlsx_fake, tmp_path
):
    _, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    caminho_banco = tmp_path / "sinapi.duckdb"
    carregar(
        df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao"
    )

    df_proximo_mes = df_valido.copy()
    df_proximo_mes.loc[df_proximo_mes["codigo"] == "123", "descricao"] = (
        "Descrição alterada"
    )
    conflitos = carregar(
        df_proximo_mes,
        df_rejeitado,
        caminho_banco,
        "2026-03",
        "sem_desoneracao",
    )

    assert conflitos == 1
    dimensao = _consultar(
        caminho_banco,
        "SELECT descricao, unidade, classificacao FROM dim_insumo "
        "WHERE codigo = '123'",
    )
    assert dimensao == [("Concreto de base", "m²", "Material")]

    conflito = _consultar(
        caminho_banco,
        "SELECT codigo, referencia, descricao_existente, descricao_recebida "
        "FROM dim_insumo_conflito WHERE codigo = '123'",
    )
    assert conflito == [
        ("123", "2026-03", "Concreto de base", "Descrição alterada")
    ]


def test_cli_sem_duckdb_nao_cria_banco(xlsx_fake, tmp_path):
    saida = tmp_path / "out"
    codigo = main(
        [
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
        ]
    )

    assert codigo == 0
    assert (saida / "insumos_limpos.csv").exists()
    assert (saida / "rejeitados.csv").exists()
    assert list(tmp_path.rglob("*.duckdb")) == []


def test_classificacao_nula_em_valido_gera_erro(xlsx_fake, tmp_path):
    _, df_valido, df_rejeitado = _limpar_fixture(xlsx_fake)
    df_valido.loc[df_valido.index[0], "classificacao"] = None
    caminho_banco = tmp_path / "sinapi.duckdb"

    with pytest.raises(ValueError, match="1 linhas válidas sem classificação"):
        carregar(
            df_valido, df_rejeitado, caminho_banco, "2026-02", "sem_desoneracao"
        )

    assert not caminho_banco.exists()
