# Cobertura de preços por UF: o caso de SP e as ausências na BA

Em setembro de 2026, a BA teve a segunda menor contagem de rejeições: 362.
Só SP teve zero; o ponto anômalo é SP. Ainda assim, **271 das 362 linhas
rejeitadas na BA ficam sem preço em 21 a 26 das 27 UFs** (88 + 115 + 37 + 9 +
22). Os dados mostram essas diferenças de cobertura, mas não determinam a
causa.

Escopo: abas `ISD`, referências 2026-06 a 2026-09, regime
`sem_desoneracao`. As contagens por categoria abaixo são apenas da BA em
setembro de 2026. As análises de cobertura entre UFs carregam todas as 27 UFs.

## O que os dados mostram

### Rejeições por UF em setembro de 2026

| UF | Válidos | Rejeitados |
|---|---:|---:|
| AC | 3.948 | 930 |
| AL | 3.256 | 1.622 |
| AM | 3.013 | 1.865 |
| AP | 3.172 | 1.706 |
| BA | 4.516 | 362 |
| CE | 3.304 | 1.574 |
| DF | 3.453 | 1.425 |
| ES | 4.285 | 593 |
| GO | 3.712 | 1.166 |
| MA | 3.078 | 1.800 |
| MG | 4.422 | 456 |
| MS | 3.690 | 1.188 |
| MT | 3.772 | 1.106 |
| PA | 4.048 | 830 |
| PB | 2.959 | 1.919 |
| PE | 3.475 | 1.403 |
| PI | 3.629 | 1.249 |
| PR | 3.385 | 1.493 |
| RJ | 3.481 | 1.397 |
| RN | 3.696 | 1.182 |
| RO | 4.142 | 736 |
| RR | 2.848 | 2.030 |
| RS | 4.344 | 534 |
| SC | 4.135 | 743 |
| SE | 3.099 | 1.779 |
| SP | 4.878 | 0 |
| TO | 3.411 | 1.467 |
| **Total** | **99.151** | **32.555** |

Cada UF tem 4.878 linhas de entrada. Em todas as UFs, o motivo de rejeição
observado foi `preço ausente para a UF`. BA tem a segunda menor contagem de
rejeições; o extremo inferior é SP, com zero.

### Ausências compartilhadas entre UFs

O cruzamento usa `linha_origem` na mesma planilha de setembro. Para cada linha
rejeitada na BA, a tabela mostra em quantas UFs há ausência de preço naquela
linha:

| UFs sem preço na mesma linha | Linhas da BA |
|---:|---:|
| 26 | 88 |
| 25 | 115 |
| 24 | 37 |
| 23 | 9 |
| 21 | 22 |
| 11 | 91 |
| **Total** | **362** |

Assim, 271 linhas (88 + 115 + 37 + 9 + 22) ficam sem preço em 21 a 26 UFs.
As outras 91 ficam sem preço em 11 UFs. Nenhuma das 362 linhas é exclusiva da
BA. SP tem preço nas 362 linhas, por isso nenhuma linha chega a 27 UFs sem
preço.

### Contagens de rejeições por categoria na BA

As quatro tabelas a seguir mostram contagens absolutas de rejeições, sem
comparação com o total de cada categoria; portanto, não indicam padrão.

#### Classificação

| Classificação | Rejeitados |
|---|---:|
| ENCARGOS COMPLEMENTARES | 0 |
| EQUIPAMENTO (AQUISIÇÃO) | 49 |
| EQUIPAMENTO (LOCAÇÃO) | 2 |
| ESPECIAIS | 0 |
| MAO DE OBRA | 0 |
| MATERIAL | 297 |
| SERVIÇOS | 14 |
| **Total** | **362** |

#### Unidade

| Unidade como aparece na planilha | Rejeitados |
|---|---:|
| 100M | 0 |
| 310ML | 0 |
| CENTO | 0 |
| CJ | 0 |
| H | 2 |
| JG | 0 |
| KG | 8 |
| KWH | 0 |
| L | 0 |
| M | 35 |
| M2 | 32 |
| M2XMES | 0 |
| M3 | 6 |
| MES | 0 |
| MIL | 0 |
| MXMES | 0 |
| PAR | 0 |
| SC25KG | 4 |
| T | 0 |
| UN | 275 |
| UNXMES | 0 |
| **Total** | **362** |

#### Origem do preço

| Origem | Rejeitados |
|---|---:|
| C | 32 |
| CR | 330 |
| **Total** | **362** |

#### Faixa de código

| Faixa numérica | Rejeitados |
|---|---:|
| 0-999 | 7 |
| 1000-9999 | 28 |
| 10000-99999 | 327 |
| **Total** | **362** |

### Histograma de UFs com preço por insumo

Cada linha conta insumos com preço em exatamente aquela quantidade de UFs.
`Rejeitados na BA` é o subconjunto que não tem preço na BA.

| UFs com preço | Insumos | Rejeitados na BA |
|---:|---:|---:|
| 1 | 88 | 88 |
| 2 | 128 | 115 |
| 3 | 68 | 37 |
| 4 | 128 | 9 |
| 5 | 24 | 0 |
| 6 | 127 | 22 |
| 7 | 53 | 0 |
| 8 | 30 | 0 |
| 9 | 81 | 0 |
| 10 | 43 | 0 |
| 11 | 129 | 0 |
| 12 | 35 | 0 |
| 13 | 71 | 0 |
| 14 | 38 | 0 |
| 15 | 296 | 0 |
| 16 | 244 | 91 |
| 17 | 40 | 0 |
| 18 | 134 | 0 |
| 19 | 113 | 0 |
| 20 | 84 | 0 |
| 21 | 26 | 0 |
| 22 | 109 | 0 |
| 23 | 116 | 0 |
| 24 | 102 | 0 |
| 25 | 170 | 0 |
| 26 | 255 | 0 |
| 27 | 2.146 | 0 |
| **Total** | **4.878** | **362** |

Os 362 rejeitados da BA distribuem-se nos grupos com preço em 1, 2, 3, 4, 6
ou 16 UFs. Os 271 que faltam em 21 a 26 UFs são os grupos com preço em 1 a 6
UFs, exceto o grupo com preço em 5 UFs.

### Evolução dos 80 códigos recuperados na BA

Foram considerados os 80 códigos com preço ausente na BA em junho e preço
válido em setembro. As quatro referências foram processadas com `--uf TODAS`
na aba `ISD`:

| Referência | Linhas de entrada | Válidos | Rejeitados |
|---|---:|---:|---:|
| 2026-06 | 131.652 | 97.820 | 33.832 |
| 2026-07 | 131.652 | 97.844 | 33.808 |
| 2026-08 | 131.652 | 98.881 | 32.771 |
| 2026-09 | 131.706 | 99.151 | 32.555 |

O primeiro mês em que os códigos passaram a ter preço na BA foi:

| Primeiro mês com preço na BA | Códigos |
|---|---:|
| Julho | 14 |
| Agosto | 66 |
| Setembro | 0 |
| **Total** | **80** |

Entre os 14 códigos recuperados na BA em julho, nenhum teve novo preço em
outra UF naquele mês. O mesmo vale para os 66 recuperados na BA em agosto.
Considerando os mesmos 80 códigos de junho a setembro, houve uma nova
combinação código-UF fora da BA: o código `4090` passou a ter preço em RR em
setembro. Esse ganho ocorreu depois do mês em que o código voltou a ter preço
na BA; não houve novos ganhos em outras UFs nos meses dos ganhos na BA.

### Dimensão dos rejeitados

O `LEFT JOIN` dos 362 rejeitados da BA com `dim_insumo` resultou em **0 sem
dimensão** e **0 sem classificação**. Esse resultado só vale porque foram
carregadas as 27 UFs; SP tem preço em todas as 4.878 linhas. Os rejeitados da
BA têm dimensão por meio de preços válidos em outras UFs; não se deve inferir
que rejeitados de uma carga isolada de BA sempre terão dimensão.

## O que não consegui determinar

- A causa de SP ter preço em todas as linhas e das diferenças de cobertura
  entre as UFs: **NÃO VERIFICADA**.
- A causa de os 80 códigos passarem a ter preço na BA entre junho e agosto, ou
  de o código `4090` ganhar preço em RR em setembro: **NÃO VERIFICADA**.
- Se preço ausente indica disponibilidade local, regra de coleta,
  característica do insumo ou outro motivo: **NÃO VERIFICADA**.

As planilhas mostram presença e ausência de valores, mas não registram suas
causas. Para determinar metodologia ou causa de coleta, é necessária
documentação da Caixa ou esclarecimento da instituição.
