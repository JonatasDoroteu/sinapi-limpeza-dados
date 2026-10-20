"""Limpeza e validação dos dados do SINAPI."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

UF_SINAPI = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG",
    "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
    "RS", "SC", "SE", "SP", "TO",
]


def normalizar_texto(valor: Any) -> str | pd._libs.missing.NAType:
    """Tira espaços extras e converte strings vazias em nulo."""
    if valor is None or pd.isna(valor):
        return pd.NA
    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto if texto else pd.NA


def normalizar_nulos(valor: Any) -> str | pd._libs.missing.NAType:
    """Converte valores nulos ou marcadores usados pelo Excel em nulo."""
    if valor is None or pd.isna(valor):
        return pd.NA
    texto = str(valor).strip()
    if texto == "" or texto.upper() in {"-", "N/A", "NA", "NULL", "NAN"}:
        return pd.NA
    return texto


def normalizar_codigo(valor: Any) -> str | pd._libs.missing.NAType:
    """Padroniza números de código, removendo espaços e sufixo de Excel."""
    texto = normalizar_nulos(valor)
    if pd.isna(texto):
        return pd.NA
    codigo = str(texto).replace(" ", "")
    if codigo.endswith(".0"):
        codigo = codigo[:-2]
    if not codigo.isdigit():
        return pd.NA
    return codigo


def converter_preco(valor: Any) -> float | pd._libs.missing.NAType:
    """Converte preços em formato brasileiro ou decimal simples para float arredondado."""
    texto = normalizar_nulos(valor)
    if pd.isna(texto):
        return pd.NA
    texto = str(texto).strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
        return round(float(texto), 2)
    if re.fullmatch(r"\d+(\.\d+)?", texto):
        return round(float(texto), 2)
    return pd.NA


def normalizar_unidade(valor: Any) -> str | pd._libs.missing.NAType:
    """Padroniza nomes de unidade para o conjunto pequeno de valores aceitos."""
    texto = normalizar_texto(valor)
    if pd.isna(texto):
        return pd.NA
    chave = re.sub(r"\s+", "", texto)
    mapa = {
        "M2": "m²",
        "M²": "m²",
        "M3": "m³",
        "M³": "m³",
        "UN": "un",
        "UND": "un",
        "KG": "kg",
        "H": "h",
        "M": "m",
        "L": "l",
        "m²": "m²",
        "m³": "m³",
        "un": "un",
        "kg": "kg",
        "h": "h",
        "m": "m",
        "l": "l",
    }
    chave_mai = chave.upper()
    if chave_mai in mapa:
        return mapa[chave_mai]
    if chave in mapa:
        return mapa[chave]
    return chave.upper()


def normalizar_origem(valor: Any) -> str:
    """Padroniza a origem do preço em maiúsculas sem espaços extras."""
    texto = normalizar_nulos(valor)
    if pd.isna(texto):
        return ""
    return str(texto).strip().upper().replace(" ", "")


def regime_da_aba(aba: str) -> str:
    """Converte o nome da aba para o regime correspondente."""
    mapa = {
        "ISD": "sem_desoneracao",
        "ICD": "com_desoneracao",
        "ISE": "sem_encargos",
    }
    if aba not in mapa:
        raise ValueError("Só insumos são suportados. As abas aceitas são: ISD, ICD e ISE.")
    return mapa[aba]


def referencia_do_arquivo(nome_arquivo: str | None) -> str | None:
    """Extrai a referência AAAA-MM do nome do arquivo, se existir."""
    if not nome_arquivo:
        return None
    padrao = re.search(r"(\d{4})[_-](\d{2})", nome_arquivo)
    if not padrao:
        return None
    return f"{padrao.group(1)}-{padrao.group(2)}"


def limpar(df_largo: pd.DataFrame, uf: str, regime: str, referencia: str | None, arquivo_origem: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida as linhas de insumo e separa válidas de rejeitadas."""
    df = df_largo.copy()
    ufs_disponiveis = [coluna for coluna in UF_SINAPI if coluna in df.columns]
    if uf == "TODAS":
        ufs_ativas = ufs_disponiveis
    else:
        if uf not in ufs_disponiveis:
            disponiveis = ", ".join(ufs_disponiveis)
            raise ValueError(
                f"UF '{uf}' não existe na planilha. "
                f"UFs disponíveis: {disponiveis}"
            )
        ufs_ativas = [uf]

    linhas: list[dict[str, Any]] = []
    for _, linha in df.iterrows():
        for uf_atual in ufs_ativas:
            preco_original = linha.get(uf_atual)
            linhas.append(
                {
                    "classificacao": linha.get("classificacao"),
                    "codigo": linha.get("codigo"),
                    "descricao": linha.get("descricao"),
                    "unidade": linha.get("unidade"),
                    "origem_preco": linha.get("origem_preco"),
                    "preco_original": preco_original,
                    "uf": uf_atual,
                    "linha_origem": linha.get("linha_origem"),
                }
            )

    df_longo = pd.DataFrame(linhas)
    if df_longo.empty:
        return (
            pd.DataFrame(columns=["codigo", "descricao", "unidade", "origem_preco", "classificacao", "uf", "preco", "regime", "referencia", "arquivo_origem"]),
            pd.DataFrame(columns=["linha_origem", "uf", "codigo", "descricao", "unidade", "origem_preco", "preco_original", "motivo_rejeicao"]),
        )

    validados: list[dict[str, Any]] = []
    rejeitados: list[dict[str, Any]] = []
    chaves_vistas: set[tuple[str, str, str, str | None]] = set()

    for _, linha in df_longo.iterrows():
        motivos: list[str] = []
        codigo = normalizar_codigo(linha.get("codigo"))
        if pd.isna(codigo):
            motivos.append("codigo inválido")
        descricao = normalizar_texto(linha.get("descricao"))
        if pd.isna(descricao):
            motivos.append("descrição vazia")
        unidade = normalizar_unidade(linha.get("unidade"))
        if pd.isna(unidade):
            unidade = pd.NA
        origem = normalizar_origem(linha.get("origem_preco"))
        preco_original = linha.get("preco_original")
        preco_raw = normalizar_nulos(preco_original)
        if pd.isna(preco_raw):
            motivos.append("preço ausente para a UF")
        preco = converter_preco(preco_original)
        if not pd.isna(preco_raw) and pd.isna(preco):
            motivos.append("preço não numérico")
        if not pd.isna(preco) and preco <= 0:
            motivos.append("preço negativo ou zero")

        chave = (str(codigo) if not pd.isna(codigo) else "", str(linha.get("uf")), regime, referencia or "")
        if not motivos and not pd.isna(codigo):
            if chave in chaves_vistas:
                motivos.append("duplicado")
            else:
                chaves_vistas.add(chave)

        if motivos:
            rejeitados.append(
                {
                    "linha_origem": linha.get("linha_origem"),
                    "uf": linha.get("uf"),
                    "codigo": linha.get("codigo"),
                    "descricao": linha.get("descricao"),
                    "unidade": linha.get("unidade"),
                    "origem_preco": linha.get("origem_preco"),
                    "preco_original": preco_original,
                    "motivo_rejeicao": "; ".join(motivos),
                }
            )
            continue

        validados.append(
            {
                "codigo": str(codigo),
                "descricao": str(descricao),
                "unidade": str(unidade),
                "origem_preco": origem,
                "classificacao": linha.get("classificacao"),
                "uf": linha.get("uf"),
                "preco": round(float(preco), 2),
                "regime": regime,
                "referencia": referencia,
                "arquivo_origem": arquivo_origem,
            }
        )

    df_valido = pd.DataFrame(
        validados,
        columns=["codigo", "descricao", "unidade", "origem_preco", "classificacao", "uf", "preco", "regime", "referencia", "arquivo_origem"],
    )
    df_rejeitado = pd.DataFrame(
        rejeitados,
        columns=["linha_origem", "uf", "codigo", "descricao", "unidade", "origem_preco", "preco_original", "motivo_rejeicao"],
    )
    return df_valido, df_rejeitado
