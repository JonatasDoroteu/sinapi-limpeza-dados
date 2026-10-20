"""Funções para leitura e detecção do layout do XLSX do SINAPI."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

UF_SINAPI = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG",
    "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
    "RS", "SC", "SE", "SP", "TO",
]


def _normalizar_celula(valor: Any) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = re.sub(r"\s+", " ", texto)
    return texto.lower()


def _mostrar_15_linhas(df: pd.DataFrame) -> str:
    return df.head(15).to_string(index=False, header=False)


def listar_abas(caminho: str) -> list[str]:
    """Lista as abas disponíveis no arquivo XLSX."""
    xlsx = pd.ExcelFile(caminho)
    return xlsx.sheet_names


def ler_aba_bruta(caminho: str, aba: str) -> pd.DataFrame:
    """Lê a aba solicitada como texto puro, sem cabeçalho, para análise do layout."""
    try:
        return pd.read_excel(caminho, sheet_name=aba, header=None, dtype=str)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}") from exc
    except ValueError as exc:
        abas = listar_abas(caminho)
        lista = ", ".join(abas) if abas else "nenhuma"
        raise ValueError(f"Aba '{aba}' não existe. Abas disponíveis: {lista}") from exc


def detectar_layout(df_bruto: pd.DataFrame) -> dict[str, Any]:
    """Detecta automaticamente a linha de cabeçalho e os campos relevantes da aba."""
    limite = min(len(df_bruto), 40)
    linha_cabecalho = None
    mapa_colunas: dict[str, int | None] = {"codigo": None, "descricao": None, "unidade": None, "origem_preco": None, "classificacao": None}
    ufs: list[str] = []

    for indice in range(limite):
        linha = df_bruto.iloc[indice]
        valores = [_normalizar_celula(valor) for valor in linha.tolist()]
        tem_codigo = any(valor.startswith("codigo") for valor in valores if valor)
        tem_descricao = any(valor.startswith("descri") for valor in valores if valor)
        if not (tem_codigo and tem_descricao):
            continue

        linha_cabecalho = indice
        for posicao, valor in enumerate(valores):
            if valor.startswith("codigo") and mapa_colunas["codigo"] is None:
                mapa_colunas["codigo"] = posicao
            if valor.startswith("descri") and mapa_colunas["descricao"] is None:
                mapa_colunas["descricao"] = posicao
            if valor.startswith("unid") and mapa_colunas["unidade"] is None:
                mapa_colunas["unidade"] = posicao
            if "origem" in valor and mapa_colunas["origem_preco"] is None:
                mapa_colunas["origem_preco"] = posicao
            if "classifica" in valor and mapa_colunas["classificacao"] is None:
                mapa_colunas["classificacao"] = posicao
            if valor.upper() in UF_SINAPI and valor.upper() not in ufs:
                ufs.append(valor.upper())

        break

    if linha_cabecalho is None or mapa_colunas["codigo"] is None or mapa_colunas["descricao"] is None or not ufs:
        raise ValueError(
            "Não foi possível detectar o cabeçalho do SINAPI. As 15 primeiras linhas da aba foram:\n"
            f"{_mostrar_15_linhas(df_bruto)}"
        )

    return {
        "linha_cabecalho": linha_cabecalho,
        "colunas": mapa_colunas,
        "ufs": ufs,
    }


def extrair(caminho: str, aba: str) -> pd.DataFrame:
    """Extrai uma aba do XLSX e devolve o DataFrame largo já padronizado."""
    df_bruto = ler_aba_bruta(caminho, aba)
    layout = detectar_layout(df_bruto)
    linha_cabecalho = layout["linha_cabecalho"]
    header = df_bruto.iloc[linha_cabecalho]
    descricao_colunas = {chave: pos for chave, pos in layout["colunas"].items() if pos is not None}

    registros: list[dict[str, Any]] = []
    for indice, linha in df_bruto.iloc[linha_cabecalho + 1 :].iterrows():
        valores = linha.tolist()
        if all(pd.isna(valor) or str(valor).strip() == "" for valor in valores):
            continue

        linha_normalizada = [_normalizar_celula(valor) for valor in valores]
        cabecalho_normalizado = [_normalizar_celula(valor) for valor in header.tolist()]
        if len(linha_normalizada) >= len(cabecalho_normalizado) and linha_normalizada[: len(cabecalho_normalizado)] == cabecalho_normalizado[: len(linha_normalizada)]:
            continue

        registro: dict[str, Any] = {"linha_origem": int(indice) + 1}
        for nome, posicao in descricao_colunas.items():
            valor = linha.iloc[posicao] if posicao < len(linha) else None
            registro[nome] = valor
        for uf in layout["ufs"]:
            posicao_uf = header.tolist().index(uf) if uf in header.tolist() else None
            if posicao_uf is None:
                continue
            registro[uf] = linha.iloc[posicao_uf] if posicao_uf < len(linha) else None
        registros.append(registro)

    if not registros:
        raise ValueError(f"Nenhuma linha de insumo foi encontrada na aba '{aba}'.")

    colunas_saida = ["classificacao", "codigo", "descricao", "unidade", "origem_preco", *layout["ufs"], "linha_origem"]
    df_largo = pd.DataFrame(registros, columns=colunas_saida)
    return df_largo
