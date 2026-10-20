"""CLI para processar arquivos XLSX do SINAPI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from sinapi_limpeza.extract import detectar_layout, extrair, listar_abas, ler_aba_bruta
from sinapi_limpeza.load import carregar
from sinapi_limpeza.transform import limpar, referencia_do_arquivo, regime_da_aba


def _imprimir_inspecao(caminho: str, aba: str) -> None:
    abas = listar_abas(caminho)
    print(f"Abas: {', '.join(abas)}")
    df = ler_aba_bruta(caminho, aba)
    print(f"Primeiras 15 linhas da aba '{aba}':")
    print(df.head(15).to_string(index=False, header=False))
    layout = detectar_layout(df)
    print(f"Linha do cabeçalho detectada: {layout['linha_cabecalho']}")
    print(f"Colunas detectadas: {layout['colunas']}")
    print(f"UFs detectadas: {layout['ufs']}")


def main(argv: list[str] | None = None) -> int:
    """Processa a entrada do usuário via linha de comando."""
    parser = argparse.ArgumentParser(description="Limpeza de dados do SINAPI.")
    parser.add_argument("--entrada", required=True, help="Caminho do arquivo XLSX de entrada")
    parser.add_argument("--aba", default="ISD", help="Aba do arquivo do SINAPI")
    parser.add_argument("--uf", default="BA", help="UF a filtrar ou 'TODAS'")
    parser.add_argument("--referencia", default=None, help="Referência no formato AAAA-MM")
    parser.add_argument("--saida", default="data/processed", help="Pasta para gravar os CSVs")
    parser.add_argument("--duckdb", default=None, help="Caminho opcional do banco DuckDB")
    parser.add_argument("--inspecionar", action="store_true", help="Mostra o layout e encerra sem salvar")
    args = parser.parse_args(argv)

    try:
        caminho_entrada = str(Path(args.entrada))
        if args.inspecionar:
            _imprimir_inspecao(caminho_entrada, args.aba)
            return 0

        df_largo = extrair(caminho_entrada, args.aba)
        regime = regime_da_aba(args.aba)
        referencia = args.referencia or referencia_do_arquivo(Path(caminho_entrada).name)
        df_valido, df_rejeitado = limpar(df_largo, args.uf, regime, referencia, Path(caminho_entrada).name)

        pasta_saida = Path(args.saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        caminho_limpos = pasta_saida / "insumos_limpos.csv"
        caminho_rejeitados = pasta_saida / "rejeitados.csv"
        df_valido.to_csv(caminho_limpos, sep=';', index=False, encoding='utf-8-sig', decimal=',')
        df_rejeitado.to_csv(caminho_rejeitados, sep=';', index=False, encoding='utf-8-sig', decimal=',')

        if args.duckdb:
            conflitos = carregar(df_valido, df_rejeitado, args.duckdb, referencia, regime)
            print(f"Conflitos na dimensão dim_insumo: {conflitos}")

        motivos = df_rejeitado["motivo_rejeicao"].fillna("").str.split("; ").explode()
        contagem_motivos = motivos[~motivos.isna() & (motivos != "")].value_counts().to_dict()
        origem_fora = (
            pd.concat([df_valido, df_rejeitado], ignore_index=True)["origem_preco"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.replace(" ", "", regex=False)
            .isin(["C", "CR", "AS"])
        )
        origem_fora_count = int((~origem_fora).sum())

        print(
            f"Arquivo: {Path(caminho_entrada).name} | Aba: {args.aba} | UF: {args.uf} | "
            f"Referência: {referencia} | Regime: {regime}"
        )
        print(f"Lidos: {len(df_valido) + len(df_rejeitado)} | Válidos: {len(df_valido)} | Rejeitados: {len(df_rejeitado)}")
        print("Rejeições por motivo:")
        if contagem_motivos:
            for motivo, quantidade in contagem_motivos.items():
                print(f"  - {motivo}: {quantidade}")
        print(f"Origem de preço fora de C/CR/AS: {origem_fora_count}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
