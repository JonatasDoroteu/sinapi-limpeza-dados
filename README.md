# sinapi-limpeza-dados

[![Tests](https://github.com/JonatasDoroteu/sinapi-limpeza-dados/actions/workflows/tests.yml/badge.svg)](https://github.com/JonatasDoroteu/sinapi-limpeza-dados/actions/workflows/tests.yml)

Pipeline ETL em Python/pandas que lê a planilha oficial de preços de insumos do SINAPI (Caixa Econômica Federal), converte do formato largo (uma coluna por UF) para o longo, valida cada linha e grava dois CSVs: os dados limpos e os rejeitados, com a **linha de origem na planilha** e o **motivo** de cada rejeição. Para UFs presentes na planilha, cada linha processada é classificada como válida ou rejeitada.

**Stack:** Python 3.11+, pandas, openpyxl, DuckDB, Pytest.

## Resultado em uma execução real

Arquivo `SINAPI_Referência_2026_09.xlsx` (13 MB), aba `ISD`, UF `BA`:

| Métrica | Valor |
|---|---|
| Linhas lidas (insumo × UF) | 4.878 |
| Válidas | 4.516 (92,6%) |
| Rejeitadas | 362 (7,4%) |
| Motivo das rejeições | preço ausente para a UF (362) |
| Origem de preço fora de C/CR/AS | 0 |
| Testes automatizados | 27 testes em Pytest |

Saída do terminal:

```text
Arquivo: SINAPI_Referência_2026_09.xlsx | Aba: ISD | UF: BA | Referência: 2026-09 | Regime: sem_desoneracao
Lidos: 4878 | Válidos: 4516 | Rejeitados: 362
Rejeições por motivo:
  - preço ausente para a UF: 362
Origem de preço fora de C/CR/AS: 0
```

## Execuções em quatro meses (aba ISD, UF BA)

O mesmo comando processou as quatro referências mais recentes:

| Referência | Lidas | Válidas | Rejeitadas | Motivo |
|---|---|---|---|---|
| 2026-06 | 4.876 | 4.434 (90,9%) | 442 (9,1%) | preço ausente para a UF |
| 2026-07 | 4.876 | 4.448 (91,2%) | 428 (8,8%) | preço ausente para a UF |
| 2026-08 | 4.876 | 4.514 (92,6%) | 362 (7,4%) | preço ausente para a UF |
| 2026-09 | 4.878 | 4.516 (92,6%) | 362 (7,4%) | preço ausente para a UF |

Em cada mês, lidas = válidas + rejeitadas. A quantidade de insumos sem preço na Bahia caiu de 442 para 362 entre junho e setembro; o projeto registra isso, mas não investiga a causa.

Nos quatro meses, o resumo lista um único motivo de rejeição. As demais regras (`codigo inválido`, duplicidade, preço negativo ou não numérico) estão cobertas por testes com planilha sintética, mas não foram exercitadas por dados reais.

## Execuções adicionais (referência 2026-09)

| Execução | Lidas | Válidas | Rejeitadas | Motivo |
|---|---|---|---|---|
| Aba ICD, UF BA | 4.878 | 4.516 (92,6%) | 362 (7,4%) | preço ausente para a UF |
| Aba ISD, UF SP | 4.878 | 4.878 (100%) | 0 | nenhuma rejeição |
| Aba ISD, `--uf TODAS` | 131.706 | 99.151 (75,3%) | 32.555 (24,7%) | preço ausente para a UF |

No `TODAS`, 131.706 = 4.878 insumos × 27 UFs, e válidas + rejeitadas fecham o total. A cobertura de preço varia bastante entre UFs (SP sem rejeições, BA com 362); o projeto registra isso, mas não investiga a causa.

## O problema

A planilha de referência do SINAPI traz linhas de título antes do cabeçalho, um preço por coluna de UF e valores em formato numérico brasileiro, com células vazias ou "-" quando não há preço. Isso a torna ruim para análise direta. O projeto detecta o cabeçalho automaticamente (sem fixar número de linha nem nomes de colunas), padroniza os campos e entrega uma tabela longa, com uma linha por insumo e UF.

## Como funciona

```text
XLSX (largo)          extract.py                     transform.py                       saída
SINAPI_Ref_AAAA_MM -> lê a aba como texto,       ->  melt (largo -> longo),        ->  insumos_limpos.csv
                      detecta cabeçalho,             aplica regras de limpeza,         rejeitados.csv
                      colunas e UFs                  separa válidos e rejeitados
```

- `extract.py`: lista abas, lê a aba bruta, detecta o layout (linha do cabeçalho, colunas de código, descrição, unidade, origem e as UFs) e devolve um DataFrame largo com a coluna `linha_origem`.
- `transform.py`: uma função pequena e pura por regra de limpeza, mais `limpar(...)`, que devolve `(df_valido, df_rejeitado)`.
- `cli.py`: interface de linha de comando com `argparse`.

## Instalação e uso

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Baixe a planilha de referência no site da Caixa (página do SINAPI, área de downloads), extraia o XLSX e coloque em `data/raw/`.

Inspecionar o layout antes de processar (não grava nada):

```bash
python -m sinapi_limpeza.cli --entrada "data/raw/SINAPI_Referência_2026_09.xlsx" --aba ISD --inspecionar
```

Executar:

```bash
python -m sinapi_limpeza.cli --entrada "data/raw/SINAPI_Referência_2026_09.xlsx" --aba ISD --uf BA --saida data/processed
```

Opções: `--aba` (ISD, ICD ou ISE; padrão ISD), `--uf` (sigla ou `TODAS`; padrão BA), `--referencia AAAA-MM` (se omitido, é extraída do nome do arquivo), `--saida` e `--duckdb` (caminho opcional para carregar os DataFrames no banco após gravar os CSVs).

## Carga e consultas

A carga opcional recebe os DataFrames produzidos pela limpeza e grava as tabelas abaixo. Não relê os CSVs, que usam vírgula como separador decimal.

```text
dim_insumo (codigo PK)
    1 ─── N fato_preco (codigo, uf, referencia, regime; preco DECIMAL(12,2))
    1 ─── N fato_rejeicao (codigo, referencia, regime, uf, motivo)

    1 ─── N dim_insumo_conflito (metadados divergentes)
```

Exemplo PowerShell para carregar duas referências no mesmo banco:

```bash
$env:PYTHONPATH = "$PWD\src"
python -m sinapi_limpeza.cli --entrada "data\raw\SINAPI_Referência_2026_06.xlsx" --aba ISD --uf BA --saida "data\processed\2026_06" --duckdb "data\processed\sinapi.duckdb"
python -m sinapi_limpeza.cli --entrada "data\raw\SINAPI_Referência_2026_09.xlsx" --aba ISD --uf BA --saida "data\processed\2026_09" --duckdb "data\processed\sinapi.duckdb"
```

Cada chamada substitui em uma transação os fatos apenas para a referência, o regime e as UFs presentes nos DataFrames. Assim, repetir a mesma carga não duplica registros e carregar `TODAS` não remove UFs de outras cargas.

`dim_insumo` conserva o primeiro valor carregado para cada código. Os metadados de cargas posteriores são comparados com esse valor inicial; divergências são gravadas em `dim_insumo_conflito` sem sobrescrever a dimensão. A dimensão não é um histórico mensal: preços e rejeições são fatos.

As quatro consultas SQL estão em [`sql/consultas.sql`](sql/consultas.sql). Para executar cada consulta no banco:

```python
import duckdb
from pathlib import Path

conexao = duckdb.connect("data/processed/sinapi.duckdb", read_only=True)
for consulta in Path("sql/consultas.sql").read_text(encoding="utf-8").split(";"):
    if consulta.strip():
        print(conexao.execute(consulta).fetchdf().to_string(index=False))
```

Resultados das quatro consultas, executadas sobre as saídas reais de BA, abas `ISD`, regime `sem_desoneracao`, referências 2026-06 e 2026-09:

1. **Preço médio por classificação em setembro:**

   | Classificação | Preço médio | Linhas |
   |---|---:|---:|
   | ENCARGOS COMPLEMENTARES | 84,66 | 56 |
   | EQUIPAMENTO (AQUISIÇÃO) | 488.559,28 | 176 |
   | EQUIPAMENTO (LOCAÇÃO) | 739,22 | 18 |
   | ESPECIAIS | 8,22 | 3 |
   | MAO DE OBRA | 3.247,55 | 184 |
   | MATERIAL | 443,66 | 4.068 |
   | SERVIÇOS | 653,71 | 11 |

2. **Variação percentual junho-setembro:** entre as dez maiores altas, o código `4408` passou de 2,36 para 2,95 (+25,00%); entre as dez maiores quedas, `39569` passou de 5,27 para 4,08 (-22,58%). Não houve variações absolutas acima de 100%.

3. **Mudança de cobertura de preço válido:** 82 códigos ganharam preço na BA e 0 perderam. Exemplos dos ganhos: `11615`, `13109`, `13110`, `3408` e `3409`.

4. **Ranking da variação por classificação:** em MATERIAL, posições 1 a 3 foram `4408` (+25,00%), `4415` (+24,95%) e `6189` (+24,93%); em SERVIÇOS, posição 1 foi `3275` (+12,98%); em EQUIPAMENTO (AQUISIÇÃO), posições 1 a 3 foram `43194`, `39555` e `39551` (+8,23% cada); em MAO DE OBRA, `4094` (+4,62%), `20020` (+4,59%) e `4096` (+4,58%). `RANK` mantém empates, inclusive valores sem variação.

## Achados

Em setembro de 2026, BA teve 362 rejeições e SP teve zero. Das rejeições na BA, 271 linhas não têm preço em 21 a 26 UFs. Entre junho e setembro, 80 códigos passaram de rejeitados a válidos na BA; não foi determinada a causa. Detalhes em [`docs/achados.md`](docs/achados.md).

Testes:

```bash
python -m pytest -q
```

Abas suportadas: `ISD` (sem desoneração), `ICD` (com desoneração) e `ISE` (sem encargos sociais). Composições ficam fora do escopo.

## Regras de limpeza

| Regra | O que faz |
|---|---|
| Texto | Remove espaços nas pontas e duplicados; vazio vira nulo |
| Nulos | `""`, `-`, `N/A`, `NA`, `NULL`, `NAN` (qualquer caixa) viram nulo |
| Código | Só dígitos; remove espaços e o sufixo `.0` que o Excel deixa |
| Preço | Com vírgula: formato brasileiro (`1.234,56` vira `1234.56`). Sem vírgula: decimal com ponto (`12.5` continua `12.5`, nunca `125`). Resultado em float arredondado a 2 casas |
| Unidade | Dicionário pequeno e explícito (`M2`/`m²` → `m²`, `UND`/`un` → `un` etc.); unidade desconhecida é mantida em maiúsculas |
| Origem do preço | Maiúsculas e sem espaços (C, CR, AS); valores fora disso não são rejeitados, apenas contados no resumo |

Uma linha é **rejeitada** quando: código inválido (o texto literal do motivo é `codigo inválido`), descrição vazia, preço ausente para a UF, preço não numérico, preço negativo ou zero, ou duplicidade da chave (código, UF, regime, referência), caso em que a primeira ocorrência é mantida. Uma linha pode ter vários motivos, separados por `; `.

## Formato das saídas

Separador `;`, encoding `utf-8-sig`, decimal `,`.

`insumos_limpos.csv`: `codigo, descricao, unidade, origem_preco, classificacao, uf, preco, regime, referencia, arquivo_origem`

`rejeitados.csv`: `linha_origem, uf, codigo, descricao, unidade, origem_preco, preco_original, motivo_rejeicao`

## Decisões de projeto

- **Formato longo:** uma linha por insumo e UF facilita filtros e agregações.
- **Rastreabilidade:** `linha_origem` leva direto à linha da planilha, e o CSV de rejeitados registra o motivo.
- **Layout por heurística:** o projeto não depende de número de linha nem de nomes fixos de colunas, então tolera pequenas mudanças de layout. Se não conseguir detectar, falha com mensagem em português mostrando as primeiras linhas da aba.
- **Funções pequenas e puras:** cada regra é testável isoladamente.

## Comprovado / Não comprovado

| Comprovado | Não comprovado |
|---|---|
| Execução completa em quatro arquivos reais (referências 2026-06 a 2026-09), aba ISD, UF BA; em cada um, lidas = válidas + rejeitadas | Meses fora desse intervalo e versões antigas do layout |
| Detecção automática do cabeçalho e das colunas nesses quatro arquivos | Aba ISE em arquivo real |
| Aba ICD (2026-09, BA), UF SP e `--uf TODAS` (27 UFs, 2026-09) executados em arquivo real, com contagens que fecham | Rejeições por código inválido, duplicidade, preço negativo ou não numérico em dado real (0 ocorrências nas execuções realizadas) |
| Carga DuckDB executada para BA em 2026-06 a 2026-09; contagens em `fato_preco` e `fato_rejeicao` batem com as saídas, e recarga de setembro manteve 4.516 e 362 linhas | Execuções em versões Python ou DuckDB diferentes das usadas localmente |
| Consultas SQL executadas sobre dados reais: médias, variações, mudanças de cobertura e ranking por classificação | Resultados em outros meses, abas ou UFs |
| Distribuição de rejeições por UF para `--uf TODAS` (2026-09) e comparação de códigos da BA entre junho e setembro documentadas em [`docs/achados.md`](docs/achados.md) | Causas das diferenças de cobertura entre UFs e da recuperação de preços |
| 27 testes passaram localmente, incluindo fixture sintética `xlsx_fake` e UF inexistente | Workflow do GitHub Actions não executado; não há repositório remoto |
| Verificação de preço em formato texto sem vírgula na referência 2026-09, BA | Verificação desse formato em outras referências, abas ou UFs |
|  | Aba ISE em arquivo real |

## Limitações conhecidas

- Só insumos; composições não são suportadas.
- Preço em float arredondado a 2 casas; para dinheiro, o ideal seria `Decimal` ou centavos inteiros.
- Detecção de layout por heurística, validada em quatro arquivos reais consecutivos (2026-06 a 2026-09); outros meses não foram testados.
- A estrutura da planilha foi levantada de fontes públicas, não do manual oficial da Caixa.
- Uma UF que não existe como coluna no arquivo gera erro com a lista das UFs disponíveis; use uma UF presente ou `TODAS`.

## Próximos passos (planejados, ainda não implementados)

- Trocar float por `Decimal` ou centavos.

## Autor

Jonatas Doroteu | [GitHub](https://github.com/JonatasDoroteu) | [LinkedIn](https://linkedin.com/in/jonatas-doroteu)