from __future__ import annotations

from typing import Dict, Optional, Tuple, List

CLASS_ORDER: List[str] = ["Muito baixo", "Baixo", "Medio", "Alto", "Muito alto"]
PH_BAIXO_ALERTA = 5.5
PH_ALTO_ALERTA = 6.5

GRUPO_P_SOJA = 2
GRUPO_K_SOJA = 2


def classificar_classe_argila(argila_percent: Optional[float]) -> int:
    if argila_percent is None:
        return 0
    if argila_percent > 60:
        return 1
    if argila_percent >= 41:
        return 2
    if argila_percent >= 21:
        return 3
    return 4


def classificar_mo(mo_percent: Optional[float]) -> str:
    if mo_percent is None:
        return ""
    if mo_percent <= 2.5:
        return "Baixo"
    if mo_percent <= 5.0:
        return "Medio"
    return "Alto"


def classificar_ctc(ctc_ph7: Optional[float]) -> str:
    if ctc_ph7 is None:
        return ""
    if ctc_ph7 <= 7.5:
        return "Baixa"
    if ctc_ph7 <= 15.0:
        return "Media"
    if ctc_ph7 <= 30.0:
        return "Alta"
    return "Muito alta"


P_TABLE_G2 = {
    1: [("Muito baixo", 3.0), ("Baixo", 6.0), ("Medio", 9.0), ("Alto", 18.0), ("Muito alto", float("inf"))],
    2: [("Muito baixo", 4.0), ("Baixo", 8.0), ("Medio", 12.0), ("Alto", 24.0), ("Muito alto", float("inf"))],
    3: [("Muito baixo", 6.0), ("Baixo", 12.0), ("Medio", 18.0), ("Alto", 36.0), ("Muito alto", float("inf"))],
    4: [("Muito baixo",10.0), ("Baixo", 20.0), ("Medio", 30.0), ("Alto", 60.0), ("Muito alto", float("inf"))],
}


def classificar_p(p_mg_dm3: Optional[float], argila_percent: Optional[float]) -> Tuple[str, int, int]:
    if p_mg_dm3 is None or argila_percent is None:
        return ("", -1, 0)
    classe_argila = classificar_classe_argila(argila_percent)
    tabela = P_TABLE_G2.get(classe_argila, P_TABLE_G2[4])
    for idx, (rotulo, limite) in enumerate(tabela):
        if p_mg_dm3 <= limite:
            return (rotulo, idx, classe_argila)
    return ("Muito alto", CLASS_ORDER.index("Muito alto"), classe_argila)


K_TABLE_G2 = {
    "Baixa":     [("Muito baixo", 20), ("Baixo", 40), ("Medio", 60), ("Alto", 120), ("Muito alto", float("inf"))],
    "Media":     [("Muito baixo", 30), ("Baixo", 60), ("Medio", 90), ("Alto", 180), ("Muito alto", float("inf"))],
    "Alta":      [("Muito baixo", 40), ("Baixo", 80), ("Medio", 120), ("Alto", 240), ("Muito alto", float("inf"))],
    "Muito alta":[("Muito baixo", 45), ("Baixo", 90), ("Medio", 135), ("Alto", 270), ("Muito alto", float("inf"))],
}


def classificar_k(k_mg_dm3: Optional[float], ctc_ph7: Optional[float]) -> Tuple[str, int, str]:
    if k_mg_dm3 is None or ctc_ph7 is None:
        return ("", -1, "")
    classe_ctc = classificar_ctc(ctc_ph7)
    tabela = K_TABLE_G2.get(classe_ctc, K_TABLE_G2["Media"])
    for idx, (rotulo, limite) in enumerate(tabela):
        if k_mg_dm3 <= limite:
            return (rotulo, idx, classe_ctc)
    return ("Muito alto", CLASS_ORDER.index("Muito alto"), classe_ctc)


def _classificar_tres_faixas(valor: Optional[float], lim_baixo: float, lim_medio: float) -> str:
    if valor is None:
        return ""
    if valor < lim_baixo:
        return "Baixo"
    if valor <= lim_medio:
        return "Medio"
    return "Alto"


def classificar_ca(ca_cmolc_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(ca_cmolc_dm3, 2.0, 4.0)


def classificar_mg(mg_cmolc_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(mg_cmolc_dm3, 0.5, 1.0)


def classificar_s(s_mg_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(s_mg_dm3, 2.0, 5.0)


def s_adequado_para_soja(s_mg_dm3: Optional[float]) -> bool:
    if s_mg_dm3 is None:
        return False
    return s_mg_dm3 >= 10.0


def classificar_cu(cu_mg_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(cu_mg_dm3, 0.2, 0.4)


def classificar_zn(zn_mg_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(zn_mg_dm3, 0.5, 1.0)


def classificar_b(b_mg_dm3: Optional[float]) -> str:
    if b_mg_dm3 is None:
        return ""
    if b_mg_dm3 <= 0.2:
        return "Baixo"
    if b_mg_dm3 <= 0.5:
        return "Medio"
    return "Alto"


def classificar_mn(mn_mg_dm3: Optional[float]) -> str:
    return _classificar_tres_faixas(mn_mg_dm3, 2.5, 5.0)


PROB_RESPOSTA = {
    "Muito baixo": "Muito alta",
    "Baixo": "Alta",
    "Medio": "Media",
    "Alto": "Baixa",
    "Muito alto": "Baixa",
}


def prob_resposta_por_classe(classe: str) -> str:
    return PROB_RESPOSTA.get(classe, "")


def alertas_micros(pH_H2O: Optional[float], mo_percent: Optional[float], argila_percent: Optional[float]) -> List[str]:
    alertas: List[str] = []
    if mo_percent is not None and mo_percent < 2.0 and argila_percent is not None and argila_percent < 20:
        alertas.append("Matéria orgânica baixa: atenção para B em solos arenosos")
    if pH_H2O is not None and pH_H2O < PH_BAIXO_ALERTA:
        alertas.append("pH baixo: risco de deficiência de Mo e B")
    if pH_H2O is not None and pH_H2O > PH_ALTO_ALERTA:
        alertas.append("pH alto: risco de deficiência de Zn, Cu, Fe e Mn")
    return alertas


def diagnosticar_soja(entradas: Dict[str, Optional[float]]) -> Dict[str, object]:
    pH = entradas.get('pH_H2O')
    argila = entradas.get('argila_percent')
    ctc = entradas.get('CTC_pH7')
    mo = entradas.get('MO_percent')

    P = entradas.get('P_mg_dm3')
    K = entradas.get('K_mg_dm3')

    Ca = entradas.get('Ca_cmolc_dm3')
    Mg = entradas.get('Mg_cmolc_dm3')
    S = entradas.get('S_mg_dm3')

    Cu = entradas.get('Cu_mg_dm3')
    Zn = entradas.get('Zn_mg_dm3')
    B = entradas.get('B_mg_dm3')
    Mn = entradas.get('Mn_mg_dm3')

    classe_argila_num = classificar_classe_argila(argila) if argila is not None else 0
    classe_mo = classificar_mo(mo)
    classe_ctc = classificar_ctc(ctc)

    classe_p, idx_p, classe_argila_usada = classificar_p(P, argila)
    classe_k, idx_k, classe_ctc_usada = classificar_k(K, ctc)
    prob_p = prob_resposta_por_classe(classe_p) if classe_p else ""
    prob_k = prob_resposta_por_classe(classe_k) if classe_k else ""

    classe_ca = classificar_ca(Ca)
    classe_mg = classificar_mg(Mg)
    classe_s = classificar_s(S)
    adequado_s = s_adequado_para_soja(S)

    classe_cu = classificar_cu(Cu)
    classe_zn = classificar_zn(Zn)
    classe_b = classificar_b(B)
    classe_mn = classificar_mn(Mn)

    alertas = alertas_micros(pH, mo, argila)

    return {
        'propriedades': {
            'classe_argila_num': classe_argila_num,
            'classe_mo': classe_mo,
            'classe_ctc': classe_ctc,
        },
        'macronutrientes': {
            'P': {
                'classe': classe_p,
                'indice': idx_p,
                'grupo': GRUPO_P_SOJA,
                'classe_argila_usada': classe_argila_usada,
                'prob_resposta': prob_p,
            },
            'K': {
                'classe': classe_k,
                'indice': idx_k,
                'grupo': GRUPO_K_SOJA,
                'classe_ctc_usada': classe_ctc_usada,
                'prob_resposta': prob_k,
            },
            'Ca': {'classe': classe_ca},
            'Mg': {'classe': classe_mg},
            'S': {'classe': classe_s, 'adequado_para_soja': adequado_s},
        },
        'micronutrientes': {
            'Cu': {'classe': classe_cu},
            'Zn': {'classe': classe_zn},
            'B': {'classe': classe_b},
            'Mn': {'classe': classe_mn},
        },
        'alertas': alertas,
        'observacoes': {
            'teor_critico_def': "O limite superior da classe 'Medio' é considerado o teor crítico para P e K.",
            'contexto_prob_resposta': "Probabilidade de resposta: Muito baixo -> muito alta; Baixo -> alta; Medio -> media; Alto/Muito alto -> baixa.",
            'metodo_extracao': "Classificações de P e K assumem Mehlich-1.",
        },
    }