"""Carga dos dados limpos do SINAPI em DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


def _coluna_texto(df: pd.DataFrame, coluna: str) -> pd.Series:
    if coluna not in df.columns:
        return pd.Series(pd.NA, index=range(len(df)), dtype="string")
    return df[coluna].reset_index(drop=True).astype("string")


def _criar_tabelas(conexao: duckdb.DuckDBPyConnection) -> None:
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_insumo (
            codigo VARCHAR PRIMARY KEY,
            descricao VARCHAR,
            unidade VARCHAR,
            classificacao VARCHAR
        )
        """
    )
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS fato_preco (
            codigo VARCHAR,
            uf VARCHAR,
            referencia VARCHAR,
            regime VARCHAR,
            preco DECIMAL(12, 2),
            origem_preco VARCHAR,
            arquivo_origem VARCHAR,
            PRIMARY KEY (codigo, uf, referencia, regime)
        )
        """
    )
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS fato_rejeicao (
            referencia VARCHAR,
            regime VARCHAR,
            uf VARCHAR,
            codigo VARCHAR,
            linha_origem BIGINT,
            descricao VARCHAR,
            unidade VARCHAR,
            origem_preco VARCHAR,
            preco_original VARCHAR,
            motivo_rejeicao VARCHAR
        )
        """
    )
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_insumo_conflito (
            codigo VARCHAR,
            referencia VARCHAR,
            regime VARCHAR,
            descricao_existente VARCHAR,
            unidade_existente VARCHAR,
            classificacao_existente VARCHAR,
            descricao_recebida VARCHAR,
            unidade_recebida VARCHAR,
            classificacao_recebida VARCHAR,
            PRIMARY KEY (
                codigo, referencia, regime, descricao_existente, unidade_existente,
                classificacao_existente, descricao_recebida, unidade_recebida,
                classificacao_recebida
            )
        )
        """
    )


def carregar(
    df_valido: pd.DataFrame,
    df_rejeitado: pd.DataFrame,
    caminho_banco: str | Path,
    referencia: str,
    regime: str,
) -> int:
    """Substitui o recorte carregado e devolve a quantidade de conflitos dimensionais."""
    if "classificacao" in df_valido.columns:
        classificacoes_ausentes = df_valido["classificacao"].isna() | (
            df_valido["classificacao"].astype("string").str.strip() == ""
        )
        quantidade_sem_classificacao = int(classificacoes_ausentes.sum())
        if quantidade_sem_classificacao:
            raise ValueError(
                f"{quantidade_sem_classificacao} linhas válidas sem classificação; "
                "carga cancelada."
            )

    ufs = sorted(
        {
            str(uf)
            for df in (df_valido, df_rejeitado)
            if "uf" in df.columns
            for uf in df["uf"].dropna().unique()
        }
    )

    dados_validos = pd.DataFrame(
        {
            "codigo": _coluna_texto(df_valido, "codigo"),
            "uf": _coluna_texto(df_valido, "uf"),
            "descricao": _coluna_texto(df_valido, "descricao"),
            "unidade": _coluna_texto(df_valido, "unidade"),
            "classificacao": _coluna_texto(df_valido, "classificacao"),
            "origem_preco": _coluna_texto(df_valido, "origem_preco"),
            "arquivo_origem": _coluna_texto(df_valido, "arquivo_origem"),
            "preco": pd.to_numeric(
                _coluna_texto(df_valido, "preco"), errors="raise"
            ).round(2),
            "ordem": np.arange(len(df_valido)),
        }
    )
    origens_rejeitadas = pd.to_numeric(
        _coluna_texto(df_rejeitado, "linha_origem"), errors="raise"
    )
    dados_rejeitados = pd.DataFrame(
        {
            "uf": _coluna_texto(df_rejeitado, "uf"),
            "codigo": _coluna_texto(df_rejeitado, "codigo"),
            "linha_origem": np.trunc(origens_rejeitadas).astype("Int64"),
            "descricao": _coluna_texto(df_rejeitado, "descricao"),
            "unidade": _coluna_texto(df_rejeitado, "unidade"),
            "origem_preco": _coluna_texto(df_rejeitado, "origem_preco"),
            "preco_original": _coluna_texto(df_rejeitado, "preco_original"),
            "motivo_rejeicao": _coluna_texto(df_rejeitado, "motivo_rejeicao"),
        }
    )

    caminho = str(caminho_banco)
    if caminho != ":memory:":
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conexao = duckdb.connect(caminho)
    try:
        conexao.execute("BEGIN TRANSACTION")
        _criar_tabelas(conexao)

        conexao.register("sinapi_validos", dados_validos)
        conexao.register("sinapi_rejeitados", dados_rejeitados)

        if ufs:
            placeholders = ", ".join("?" for _ in ufs)
            parametros = [referencia, regime, *ufs]
            conexao.execute(
                f"DELETE FROM fato_preco WHERE referencia = ? AND regime = ? AND uf IN ({placeholders})",
                parametros,
            )
            conexao.execute(
                f"DELETE FROM fato_rejeicao WHERE referencia = ? AND regime = ? AND uf IN ({placeholders})",
                parametros,
            )

        conexao.execute(
            """
            CREATE TEMP TABLE sinapi_dim_primeira AS
            SELECT codigo, descricao, unidade, classificacao
            FROM sinapi_validos
            WHERE codigo IS NOT NULL AND classificacao IS NOT NULL
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY codigo ORDER BY ordem
            ) = 1
            """
        )
        conexao.execute(
            """
            CREATE TEMP TABLE sinapi_dim_base AS
            SELECT p.codigo, d.descricao, d.unidade, d.classificacao
            FROM sinapi_dim_primeira p
            JOIN dim_insumo d USING (codigo)
            UNION ALL
            SELECT p.codigo, p.descricao, p.unidade, p.classificacao
            FROM sinapi_dim_primeira p
            WHERE NOT EXISTS (
                SELECT 1 FROM dim_insumo d WHERE d.codigo = p.codigo
            )
            """
        )
        conexao.execute(
            """
            INSERT INTO dim_insumo
            SELECT codigo, descricao, unidade, classificacao
            FROM sinapi_dim_primeira
            ON CONFLICT (codigo) DO NOTHING
            """
        )
        conexao.execute(
            """
            CREATE TEMP TABLE sinapi_conflitos AS
            SELECT DISTINCT
                i.codigo,
                ?,
                ?,
                COALESCE(b.descricao, ''),
                COALESCE(b.unidade, ''),
                COALESCE(b.classificacao, ''),
                COALESCE(i.descricao, ''),
                COALESCE(i.unidade, ''),
                COALESCE(i.classificacao, '')
            FROM sinapi_validos i
            JOIN sinapi_dim_base b USING (codigo)
            WHERE i.codigo IS NOT NULL
              AND i.classificacao IS NOT NULL
              AND (
                COALESCE(b.descricao, '') IS DISTINCT FROM COALESCE(i.descricao, '')
                OR COALESCE(b.unidade, '') IS DISTINCT FROM COALESCE(i.unidade, '')
                OR COALESCE(b.classificacao, '') IS DISTINCT FROM COALESCE(i.classificacao, '')
              )
            """,
            [referencia, regime],
        )
        conexao.execute(
            """
            INSERT INTO dim_insumo_conflito
            SELECT * FROM sinapi_conflitos
            ON CONFLICT DO NOTHING
            """
        )

        conexao.execute(
            """
            INSERT INTO fato_preco
            SELECT
                codigo, uf, ?, ?,
                CAST(round(preco, 2) AS DECIMAL(12, 2)),
                origem_preco, arquivo_origem
            FROM sinapi_validos
            """,
            [referencia, regime],
        )
        conexao.execute(
            """
            INSERT INTO fato_rejeicao
            SELECT
                ?, ?, uf, codigo, linha_origem, descricao, unidade,
                origem_preco, preco_original, motivo_rejeicao
            FROM sinapi_rejeitados
            """,
            [referencia, regime],
        )

        quantidade_conflitos = conexao.execute(
            "SELECT COUNT(*) FROM sinapi_conflitos"
        ).fetchone()[0]
        conexao.execute("COMMIT")
        return quantidade_conflitos
    except Exception:
        conexao.execute("ROLLBACK")
        raise
    finally:
        conexao.close()
