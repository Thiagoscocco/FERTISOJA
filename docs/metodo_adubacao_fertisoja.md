# Metodo de adubacao da aba "Recomendacao de adubacao"

Este arquivo descreve, em portugues, toda a logica usada pelo Fertisoja para transformar as "necessidades brutas" de nutrientes nas recomendacoes exibidas na aba **Recomendacao de adubacao -> Metodo de adubacao**. A mesma logica devera ser reproduzida no FertiCalc.

## 1. Entradas e normalizacoes

As rotinas estao em `core/adubacao_dados.py`. As informacoes chegam pela classe `EntradaSoja`; os campos relevantes para o metodo sao:

- `p_class`, `k_class`: classificacao do solo para fosforo e potassio (`"muito baixo"`, `"baixo"`, `"medio"`, `"alto"`, `"muito alto"`). O texto e normalizado (acentos removidos, minusculas) por `_normalizar`.
- `produtividade`: produtividade alvo em t/ha.
- `cultivo`: numero do cultivo dentro da sequencia (1 = primeira safra, 2 = segunda, etc.).
- `argila_pct`, `ctc`: usados para decidir correcoes graduais em solos arenosos ou com baixa CTC.
- `teor_s_mg_dm3`, `ph_agua`: base para recomendar S, Mo e Co.
- `estrategia_muito_alto`: define o que fazer quando o nivel e "muito alto" (`"zero_e_manutencao"`, `"repor"`, `"zero_e_zero"`).
- `starter_p2o5_kg_ha`, `starter_k2o_kg_ha`: doses ja aplicadas via starter.
- `rounding`: modo de arredondamento (padrao `"nearest5"` para multiplos de 5 kg/ha).

## 2. Blocos de calculo principais

### 2.1 Manutencao (`_manutencao`)

```
extra = max(0, produtividade - 3)
manutencao_P2O5 = 45 + 15 * extra
manutencao_K2O  = 75 + 25 * extra
```

Mantem o teor do solo quando ele ja esta adequado.

### 2.2 Reposicao (`_reposicao`)

```
reposicao_P2O5 = 14 * produtividade
reposicao_K2O  = 20 * produtividade
```

Utilizada quando o usuario escolhe explicitamente "Reposicao" ou quando a estrategia para nivel "muito alto" for "repor".

### 2.3 Correcao total (`_correcao_total`)

Valores fixos (CQFS-RS/SC 2016):

| Classe      | P2O5 (kg/ha) | K2O (kg/ha) |
| ----------- | ------------ | ----------- |
| muito baixo | 160          | 120         |
| baixo       | 80           | 60          |
| medio       | 40           | 30          |

Para "alto" e "muito alto" a funcao retorna 0.

### 2.4 Correcao gradual (`_usar_gradual`)

Quando `argila_pct < 20` ou `ctc < 7.5` e a classe e `muito baixo` ou `baixo`, aplica-se parcela em duas safras:

- 1a safra: `2/3` da correcao + manutencao.
- 2a safra: `1/3` restante + manutencao.

Sem restricoes, o 1o cultivo recebe `correcao total + manutencao`; cultivos seguintes recebem apenas manutencao.

### 2.5 Estrategias por nivel

**Fosforo (`descricao_p`, `p_total`):**

- `muito baixo` ou `baixo`: correcao total (gradual ou completa, conforme item 2.4).
- `medio`: correcao parcial -> 1o cultivo recebe `correcao(medio) + manutencao`; demais cultivos ficam com manutencao.
- `alto`: apenas manutencao.
- `muito alto`: depende de `estrategia_muito_alto`:
  - `"zero_e_manutencao"` (padrao): 1o cultivo recebe 0; o seguinte recebe `min(manutencao, reposicao)`.
  - `"repor"`: usa a dose de reposicao.
  - `"zero_e_zero"`: zera em ambos.
  - Sempre soma `starter_p2o5_kg_ha`.

**Potassio (`descricao_k`, `k_total`):** mesma logica, trocando os valores de correcao e `starter_k2o_kg_ha`.

### 2.6 Nutrientes complementares (`_nutrientes_complementares`)

- `S_SO4 = 20 kg/ha` se `teor_s_mg_dm3 < 10`; caso contrario 0.
- `Mo_g_ha = 35 g/ha` se `ph_agua < 5.5`; caso contrario 0.
- `Co_g_ha = 3 g/ha` em qualquer situacao (dose base para inoculacao).

### 2.7 Limite de K na linha (`_limite_k_linha`)

```
K2O_linha = min(K2O_total, 80)
K2O_lanco = max(0, K2O_total - 80)
```

Garante que nao seja recomendado mais de 80 kg/ha de K2O no sulco; o excedente vai a lanco/cobertura.

### 2.8 Arredondamento (`_arredondar`)

No modo `"nearest5"`, cada dose de P2O5 e K2O vira `round(valor / 5) * 5`. Outras opcoes existem, mas a interface usa essa.

## 3. Resultado consolidado (`ResultadoAdubacao`)

A funcao `recomendar_adubacao_soja` devolve:

- `totais`: com `P2O5_total`, `K2O_total`, `K2O_linha`, `K2O_lanco`, `S_SO4`, `Mo_g_ha`, `Co_g_ha` (P e K ja arredondados).
- `descricao_p`, `descricao_k`: resumo textual da estrategia adotada para cada nutriente.
- `manutencao`: mapa com as doses calculadas no item 2.1.
- `reposicao`: mapa com as doses do item 2.2.
- `observacoes`: avisos (solo arenoso, CTC baixa etc.).

O resultado fica guardado em `ctx.adubacao_controls['ultimo_resultado']` para reuso.

## 4. Metodo selecionado pelo usuario (`core/aba_adubacao.py`)

Fluxo:

1. O usuario calcula as necessidades; `calcular_adubacao` chama `recomendar_adubacao_soja`.
2. Na secao "Definir adubacao" ele escolhe `metodo`:
   - `Correcao` (com opcao adicional `Correcao total` ou `Duas safras`);
   - `Manutencao`;
   - `Reposicao`.
3. `aplicar_metodo` interpreta a escolha e ajusta os textos exibidos.

### 4.1 Metodo "Correcao"

- **Correcao total:** usa `resultado.totais['P2O5_total']` e `['K2O_total']`.
- **Duas safras:** reparte a parte de correcao pura entre dois ciclos:
  ```
  corr_P = max(total_P - manutencao_P, 0)
  corr_K = max(total_K - manutencao_K, 0)
  safra1_P = 0.75 * corr_P + manutencao_P
  safra2_P = (1.0 / 3.0) * corr_P + manutencao_P
  safra1_K = 0.75 * corr_K + manutencao_K
  safra2_K = (1.0 / 3.0) * corr_K + manutencao_K
  ```
  O texto exibido mostra "Safra 1" e "Safra 2" para cada nutriente.
- Mensagens complementares:
  - "Nao ultrapassar 80 kg/ha de K2O na linha; aplicar excedente a lanco ou cobertura."
  - Se o usuario optar por correcao total em uma unica vez, aparecem alertas sobre solos arenosos (lixiviacao, salinidade) e a necessidade de incorporar.

### 4.2 Metodo "Manutencao"

- Exibe `resultado.manutencao['P2O5']` e `['K2O']`.
- Recomenda considerar perdas (20 a 30 % em plantio direto, ate 50 % no convencional) e ajustar +-10 kg/ha conforme a formula comercial.

### 4.3 Metodo "Reposicao"

- Exibe `resultado.reposicao['P2O5']` e `['K2O']`.
- Sugere reamostrar o solo apos dois cultivos para confirmar se o nivel chegou a "alto".

### 4.4 Mensagens gerais

As mensagens sao capitalizadas e agrupadas em `recomendacao_var`. Se o usuario tentar aplicar o metodo antes de calcular as necessidades, o sistema avisa que e preciso calcular primeiro.

## 5. Pontos de atencao ao portar para o FertiCalc

- **Entradas iguais:** produtividade, niveis de P e K, textura/CTC, pH e S quando for necessario sugerir S/Mo/Co.
- **Sequencia de cultivos:** respeitar que o 1o cultivo pode receber correcao e os seguintes ficam com manutencao conforme a classe.
- **Parcelamento em duas safras:** manter os fatores (75 % na safra inicial, 33 % na seguinte) e somar manutencao em ambas.
- **Limite de K no sulco:** replicar a conta de linha versus lanco.
- **Arredondamento:** manter multiplos de 5 kg/ha para as doses apresentadas.
- **Nutrientes complementares:** considerar os gatilhos para S (<10 mg/dm3) e Mo (pH < 5.5) e manter o cobalto fixo em 3 g/ha.

Com este resumo sera possivel reproduzir a mesma matematica no outro projeto a partir das necessidades brutas informadas pelo usuario.
