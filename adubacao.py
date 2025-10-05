# adubacao_soja.py
# Lógica de adubação para soja (P2O5 e K2O): Correção (gradual), Manutenção e Reposição.
# Integração pensada para ser chamada por um orquestrador que já calculou as NECESSIDADES DE CORREÇÃO (P e K)
# a partir da análise de solo (isto é, o total necessário para elevar ao teor crítico).
# Observação: correção gradual aplica-se a níveis "Muito baixo" e "Baixo".
# Em "Médio", a correção é integral no 1º cultivo; em "Alto", apenas manutenção; em "Muito alto", usar reposição/0.

from typing import Literal, Dict, Tuple

Nivel = Literal["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
Modo  = Literal["correcao", "manutencao", "reposicao"]

# --------------------------
# Parâmetros (do capítulo)
# --------------------------

# Manutenção (rendimento de referência = 3 t/ha) e adicional por tonelada extra:
SOJA_MANTENCAO_BASE_P2O5 = 45  # kg/ha
SOJA_MANTENCAO_BASE_K2O  = 75  # kg/ha
SOJA_MANTENCAO_ADIC_P2O5 = 15  # kg/ha por tonelada adicional
SOJA_MANTENCAO_ADIC_K2O  = 25  # kg/ha por tonelada adicional

# Reposição (exportação por t de grão de soja):
SOJA_REPOSICAO_P2O5_POR_T = 14  # kg/ha por t
SOJA_REPOSICAO_K2O_POR_T  = 20  # kg/ha por t

# Regra operacional para aplicação em linha (segurança de salinidade do K):
K2O_MAX_LINHA = 80  # kg/ha por cultivo (excedente vai a lanço/cobertura)

# Tolerância operacional para arredondar doses às fórmulas comerciais:
AJUSTE_OPERACIONAL = 10  # kg/ha (+/-)

# --------------------------
# Helpers
# --------------------------

def arredondar_operacional(valor: float) -> int:
    """
    Ajuste operacional para aproximar à meia/dezena inteira (tolerância +/- 10 kg/ha).
    Mantém simplicidade: arredonda para o inteiro mais próximo.
    """
    return int(round(valor))

def manutencao_soja(yield_t_ha: float) -> Dict[str, int]:
    """
    Calcula a manutenção para soja em um cultivo.
    """
    if yield_t_ha <= 3:
        p = SOJA_MANTENCAO_BASE_P2O5
        k = SOJA_MANTENCAO_BASE_K2O
    else:
        extra = yield_t_ha - 3.0
        p = SOJA_MANTENCAO_BASE_P2O5 + extra * SOJA_MANTENCAO_ADIC_P2O5
        k = SOJA_MANTENCAO_BASE_K2O  + extra * SOJA_MANTENCAO_ADIC_K2O
    return {
        "P2O5": arredondar_operacional(p),
        "K2O":  arredondar_operacional(k),
    }

def reposicao_soja(yield_t_ha: float) -> Dict[str, int]:
    """
    Calcula a reposição (exportação) para soja em um cultivo.
    """
    p = yield_t_ha * SOJA_REPOSICAO_P2O5_POR_T
    k = yield_t_ha * SOJA_REPOSICAO_K2O_POR_T
    return {
        "P2O5": arredondar_operacional(p),
        "K2O":  arredondar_operacional(k),
    }

def fracionar_correcao_gradual(total: float, nivel: Nivel) -> Tuple[float, float]:
    """
    Retorna (dose_1o_cultivo, dose_2o_cultivo) para correção:
    - "muito_baixo" ou "baixo": 2/3 no 1º cultivo, 1/3 no 2º.
    - "medio": 100% no 1º cultivo, 0% no 2º (correção integral no 1º).
    - "alto": 0% / 0% (não há correção).
    - "muito_alto": 0% / 0% (não há correção).
    """
    if nivel in ("muito_baixo", "baixo"):
        return (total * (2/3), total * (1/3))
    if nivel == "medio":
        return (total, 0.0)
    return (0.0, 0.0)

def aplicar_limite_k_na_linha(k2o_cultivo: int) -> Dict[str, int]:
    """
    Impõe o teto de K2O na linha (80 kg/ha). Retorna dict com repartição:
    - K2O_linha: até 80
    - K2O_compl: excedente (a lanço pré-semeadura ou em cobertura)
    """
    k_linha = min(k2o_cultivo, K2O_MAX_LINHA)
    k_compl = max(0, k2o_cultivo - k_linha)
    return {"K2O_linha": k_linha, "K2O_compl": k_compl}

# --------------------------
# Correção (gradual) para soja
# --------------------------

def correcao_gradual_soja(
    nivel_p: Nivel,
    nivel_k: Nivel,
    necessidade_correcao_total_p2o5: float,
    necessidade_correcao_total_k2o: float,
    yield_t_ha: float,
) -> Dict[str, Dict[str, Dict[str, int]]]:
    """
    Retorna as doses para 1º e 2º cultivos, somando correção (conforme nível) + manutenção por cultivo.
    Entradas:
      - nivel_p, nivel_k: interpretação do solo para P e K ("muito_baixo","baixo","medio","alto","muito_alto")
      - necessidade_correcao_total_p2o5/k2o: total (kg/ha) necessário para levar ao teor crítico (fornecido pelo módulo de análise)
      - yield_t_ha: produtividade esperada (t/ha) para calcular manutenção
    Saída:
      {
        "1o_cultivo": {"P2O5_total":..., "P2O5_correcao":..., "P2O5_manutencao":..., "K2O_total":..., "K2O_correcao":..., "K2O_manutencao":..., "K2O_linha":..., "K2O_compl":...},
        "2o_cultivo": {...}
      }
    Observações:
      - Em "medio": correção integral no 1º cultivo (0 no 2º).
      - Em "alto": somente manutenção.
      - Em "muito_alto": não aplicar P/K na correção (usar reposição/0 conforme decisão técnica).
    """
    # Fracionamento da correção
    p1, p2 = fracionar_correcao_gradual(necessidade_correcao_total_p2o5, nivel_p)
    k1, k2 = fracionar_correcao_gradual(necessidade_correcao_total_k2o,  nivel_k)

    # Manutenção por cultivo (pode variar por safra/expectativa)
    mant = manutencao_soja(yield_t_ha)
    mant_p = mant["P2O5"]
    mant_k = mant["K2O"]

    # Cultivo 1
    p_tot_c1 = arredondar_operacional(p1 + mant_p)
    k_tot_c1 = arredondar_operacional(k1 + mant_k)
    k_split_c1 = aplicar_limite_k_na_linha(k_tot_c1)

    # Cultivo 2
    p_tot_c2 = arredondar_operacional(p2 + mant_p if (nivel_p in ("muito_baixo","baixo","medio")) else (mant_p if nivel_p=="alto" else 0))
    k_tot_c2 = arredondar_operacional(k2 + mant_k if (nivel_k in ("muito_baixo","baixo","medio")) else (mant_k if nivel_k=="alto" else 0))
    k_split_c2 = aplicar_limite_k_na_linha(k_tot_c2)

    return {
        "1o_cultivo": {
            "P2O5_total": p_tot_c1, "P2O5_correcao": arredondar_operacional(p1), "P2O5_manutencao": mant_p,
            "K2O_total":  k_tot_c1, "K2O_correcao":  arredondar_operacional(k1), "K2O_manutencao":  mant_k,
            "K2O_linha":  k_split_c1["K2O_linha"], "K2O_compl": k_split_c1["K2O_compl"],
        },
        "2o_cultivo": {
            "P2O5_total": p_tot_c2, "P2O5_correcao": arredondar_operacional(p2), "P2O5_manutencao": (mant_p if p_tot_c2>0 else 0),
            "K2O_total":  k_tot_c2, "K2O_correcao":  arredondar_operacional(k2), "K2O_manutencao":  (mant_k if k_tot_c2>0 else 0),
            "K2O_linha":  k_split_c2["K2O_linha"], "K2O_compl": k_split_c2["K2O_compl"],
        },
    }

# --------------------------
# Interface principal
# --------------------------

def gerar_recomendacao_soja(
    modo: Modo,
    yield_t_ha: float,
    nivel_p: Nivel = "alto",
    nivel_k: Nivel = "alto",
    necessidade_correcao_total_p2o5: float = 0.0,
    necessidade_correcao_total_k2o: float = 0.0,
) -> Dict:
    """
    Roteia para o tipo de adubação escolhido:
      - modo="correcao": retorna doses por cultivo (1º e 2º) com correção (gradual, quando aplicável) + manutenção.
      - modo="manutencao": retorna dose de manutenção para um cultivo.
      - modo="reposicao":  retorna dose de reposição (exportação) para um cultivo.

    Parâmetros mínimos por modo:
      - correcao: informar nivel_p, nivel_k e necessidades totais de correção (P2O5/K2O) calculadas pela análise.
      - manutencao: informar yield_t_ha.
      - reposicao:  informar yield_t_ha.
    """
    modo = modo.lower()
    if modo == "correcao":
        return correcao_gradual_soja(
            nivel_p=nivel_p,
            nivel_k=nivel_k,
            necessidade_correcao_total_p2o5=necessidade_correcao_total_p2o5,
            necessidade_correcao_total_k2o=necessidade_correcao_total_k2o,
            yield_t_ha=yield_t_ha,
        )
    elif modo == "manutencao":
        return {"manutencao": manutencao_soja(yield_t_ha)}
    elif modo == "reposicao":
        return {"reposicao": reposicao_soja(yield_t_ha)}
    else:
        raise ValueError("modo inválido. Use: 'correcao', 'manutencao' ou 'reposicao'.")


# --------------------------
# Exemplo rápido de uso:
# (remova/ajuste conforme integração ao seu software)
# --------------------------
if __name__ == "__main__":
    # Exemplo 1: Correção (gradual) + manutenção, níveis muito baixos
    ex1 = gerar_recomendacao_soja(
        modo="correcao",
        yield_t_ha=3.0,
        nivel_p="muito_baixo",
        nivel_k="muito_baixo",
        necessidade_correcao_total_p2o5=160.0,  # vindo do módulo de análise
        necessidade_correcao_total_k2o=120.0,   # vindo do módulo de análise
    )
    print("Correção gradual + manutenção:", ex1)

    # Exemplo 2: Manutenção (3,5 t/ha)
    ex2 = gerar_recomendacao_soja(modo="manutencao", yield_t_ha=3.5)
    print("Manutenção:", ex2)

    # Exemplo 3: Reposição (exportação) para 3,0 t/ha
    ex3 = gerar_recomendacao_soja(modo="reposicao", yield_t_ha=3.0)
    print("Reposição:", ex3)
