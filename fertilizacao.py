"""Rotinas de cálculo para a aba de fertilização."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Fertilizante:
    codigo: str
    nome: str
    p2o5: float = 0.0
    k2o: float = 0.0
    s: float = 0.0
    mo: float = 0.0
    n: float = 0.0


def _normalize_name(texto: str | None) -> str:
    if not texto:
        return ""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower().strip()


_FOSFATADOS_SEQ: Tuple[Fertilizante, ...] = (
    Fertilizante('TSP', 'Superfosfato Triplo (TSP)', p2o5=0.46),
    Fertilizante('SSP', 'Superfosfato Simples (SSP)', p2o5=0.18, s=0.12),
    Fertilizante('MAP', 'MAP', p2o5=0.52, n=0.11),
    Fertilizante('DAP', 'DAP', p2o5=0.46, n=0.18),
)
FOSFATADOS: Dict[str, Fertilizante] = {item.codigo: item for item in _FOSFATADOS_SEQ}
_FOSFATADO_POR_NOME = {item.nome: item for item in _FOSFATADOS_SEQ}
_FOSFATADO_POR_NORMALIZED = {_normalize_name(item.nome): item for item in _FOSFATADOS_SEQ}
FOSFATADOS_CHOICES: Tuple[str, ...] = tuple(item.nome for item in _FOSFATADOS_SEQ)

_POTASSICOS_SEQ: Tuple[Fertilizante, ...] = (
    Fertilizante('KCl', 'Cloreto de Potássio (KCl)', k2o=0.60),
    Fertilizante('K2SO4', 'Sulfato de Potássio (K2SO4)', k2o=0.50, s=0.18),
)
POTASSICOS: Dict[str, Fertilizante] = {item.codigo: item for item in _POTASSICOS_SEQ}
_POTASSICO_POR_NOME = {item.nome: item for item in _POTASSICOS_SEQ}
_POTASSICO_POR_NORMALIZED = {_normalize_name(item.nome): item for item in _POTASSICOS_SEQ}
POTASSICOS_CHOICES: Tuple[str, ...] = tuple(item.nome for item in _POTASSICOS_SEQ)

GESSO_PADRAO = Fertilizante('GESSO', 'Gesso agrícola', s=0.17)
MOLIBDATO_PADRAO = Fertilizante('MOLIBDATO', 'Molibdato de sódio (Mo)', mo=0.39)

FORMULADO_COMPLEMENTO_P = FOSFATADOS['TSP']
FORMULADO_COMPLEMENTO_K = POTASSICOS['KCl']


@dataclass
class FertilizacaoResultado:
    produtos: List[Tuple[str, float]]
    alertas: List[str]
    faltantes: Dict[str, float]


def obter_fosfatado_por_nome(nome: str | None) -> Fertilizante | None:
    if not nome:
        return None
    chave = _normalize_name(nome)
    return _FOSFATADO_POR_NOME.get(nome) or _FOSFATADO_POR_NORMALIZED.get(chave)


def obter_potassico_por_nome(nome: str | None) -> Fertilizante | None:
    if not nome:
        return None
    chave = _normalize_name(nome)
    return _POTASSICO_POR_NOME.get(nome) or _POTASSICO_POR_NORMALIZED.get(chave)


def _adicionar_produto(destino: List[Tuple[str, float]], nome: str, quantidade: float, minimo: float = 1e-6) -> None:
    if quantidade <= minimo:
        return
    destino.append((nome, quantidade))


def _complementar_enxofre(restante_s: float, produtos: List[Tuple[str, float]]) -> float:
    if restante_s <= 0:
        return 0.0
    if GESSO_PADRAO.s <= 0:
        raise ValueError('Fertilizante padrão de enxofre inválido.')
    kg = restante_s / GESSO_PADRAO.s
    _adicionar_produto(produtos, GESSO_PADRAO.nome, kg)
    return kg


def _complementar_molibdenio(restante_mo: float, produtos: List[Tuple[str, float]]) -> float:
    if restante_mo <= 0:
        return 0.0
    if MOLIBDATO_PADRAO.mo <= 0:
        raise ValueError('Fertilizante padrão de molibdênio inválido.')
    kg = restante_mo / MOLIBDATO_PADRAO.mo
    _adicionar_produto(produtos, MOLIBDATO_PADRAO.nome, kg)
    return kg


def _alerta_nitrogenio(fert: Fertilizante | None) -> str | None:
    if fert is None or fert.n <= 0:
        return None
    return f"{fert.nome} fornece nitrogênio; utilizar com cautela em soja."


def calcular_formulado(
    demanda: Dict[str, float],
    grade: Dict[str, float],
    nome_formulado: str,
) -> FertilizacaoResultado:
    produtos: List[Tuple[str, float]] = []
    alertas: List[str] = []

    p_req = max(demanda.get('P2O5', 0.0), 0.0)
    k_req = max(demanda.get('K2O', 0.0), 0.0)
    s_req = max(demanda.get('S', 0.0), 0.0)
    mo_req = max(demanda.get('Mo', 0.0), 0.0)

    p_frac = max(grade.get('P2O5', 0.0), 0.0) / 100.0
    k_frac = max(grade.get('K2O', 0.0), 0.0) / 100.0

    massa_opcoes: List[Tuple[str, float]] = []
    if p_req > 0 and p_frac > 0:
        massa_opcoes.append(('P2O5', p_req / p_frac))
    if k_req > 0 and k_frac > 0:
        massa_opcoes.append(('K2O', k_req / k_frac))

    if massa_opcoes:
        _, kg_formulado = min(massa_opcoes, key=lambda item: item[1])
    else:
        kg_formulado = 0.0

    if kg_formulado > 0:
        _adicionar_produto(produtos, nome_formulado, kg_formulado)

    p_suprido = kg_formulado * p_frac
    k_suprido = kg_formulado * k_frac

    p_restante = max(p_req - p_suprido, 0.0)
    k_restante = max(k_req - k_suprido, 0.0)

    if p_restante > 0:
        kg_tsp = p_restante / FORMULADO_COMPLEMENTO_P.p2o5
        _adicionar_produto(produtos, FORMULADO_COMPLEMENTO_P.nome, kg_tsp)
    if k_restante > 0:
        kg_kcl = k_restante / FORMULADO_COMPLEMENTO_K.k2o
        _adicionar_produto(produtos, FORMULADO_COMPLEMENTO_K.nome, kg_kcl)

    _complementar_enxofre(s_req, produtos)
    _complementar_molibdenio(mo_req, produtos)

    return FertilizacaoResultado(produtos=produtos, alertas=alertas, faltantes={})


def calcular_individual_usuario(
    demanda: Dict[str, float],
    fosfatado_codigo: str | None,
    potassico_codigo: str | None,
) -> FertilizacaoResultado:
    produtos: List[Tuple[str, float]] = []
    alertas: List[str] = []
    faltantes: Dict[str, float] = {}

    p_req = max(demanda.get('P2O5', 0.0), 0.0)
    k_req = max(demanda.get('K2O', 0.0), 0.0)
    s_req = max(demanda.get('S', 0.0), 0.0)
    mo_req = max(demanda.get('Mo', 0.0), 0.0)

    fert_p = FOSFATADOS.get(fosfatado_codigo or '')
    if p_req > 0:
        if fert_p is None or fert_p.p2o5 <= 0:
            faltantes['P2O5'] = p_req
            if fert_p is None:
                alertas.append('Selecione um fertilizante fosfatado para atender ao P2O5.')
            else:
                alertas.append(f"O fertilizante '{fert_p.nome}' não fornece P2O5 suficiente.")
        else:
            kg_p = p_req / fert_p.p2o5
            _adicionar_produto(produtos, fert_p.nome, kg_p)
            alerta_n = _alerta_nitrogenio(fert_p)
            if alerta_n:
                alertas.append(alerta_n)
            s_req = max(s_req - kg_p * fert_p.s, 0.0)
    elif fosfatado_codigo:
        alertas.append('Nenhuma necessidade de P2O5 foi identificada.')

    fert_k = POTASSICOS.get(potassico_codigo or '')
    if k_req > 0:
        if fert_k is None or fert_k.k2o <= 0:
            faltantes['K2O'] = k_req
            if fert_k is None:
                alertas.append('Selecione um fertilizante potássico para atender ao K2O.')
            else:
                alertas.append(f"O fertilizante '{fert_k.nome}' não fornece K2O suficiente.")
        else:
            kg_k = k_req / fert_k.k2o
            _adicionar_produto(produtos, fert_k.nome, kg_k)
            s_req = max(s_req - kg_k * fert_k.s, 0.0)
    elif potassico_codigo:
        alertas.append('Nenhuma necessidade de K2O foi identificada.')

    if s_req > 0:
        _complementar_enxofre(s_req, produtos)
    if mo_req > 0:
        _complementar_molibdenio(mo_req, produtos)

    return FertilizacaoResultado(produtos=produtos, alertas=alertas, faltantes=faltantes)


def calcular_individual_software(demanda: Dict[str, float]) -> FertilizacaoResultado:
    produtos: List[Tuple[str, float]] = []
    alertas: List[str] = []

    p_req = max(demanda.get('P2O5', 0.0), 0.0)
    k_req = max(demanda.get('K2O', 0.0), 0.0)
    s_req = max(demanda.get('S', 0.0), 0.0)
    mo_req = max(demanda.get('Mo', 0.0), 0.0)

    fosfatado: Fertilizante | None = None
    potassico: Fertilizante | None = None

    if p_req > 0:
        fosfatado = FOSFATADOS['TSP']
        if s_req > 0 and k_req == 0:
            fosfatado = FOSFATADOS['SSP']

    if k_req > 0:
        potassico = POTASSICOS['KCl']
        if s_req > 0:
            potassico = POTASSICOS['K2SO4']

    if fosfatado is not None:
        kg_p = p_req / fosfatado.p2o5
        _adicionar_produto(produtos, fosfatado.nome, kg_p)
        alerta_n = _alerta_nitrogenio(fosfatado)
        if alerta_n:
            alertas.append(alerta_n)
        s_req = max(s_req - kg_p * fosfatado.s, 0.0)

    if potassico is not None:
        kg_k = k_req / potassico.k2o
        _adicionar_produto(produtos, potassico.nome, kg_k)
        s_req = max(s_req - kg_k * potassico.s, 0.0)

    if s_req > 0:
        _complementar_enxofre(s_req, produtos)
    if mo_req > 0:
        _complementar_molibdenio(mo_req, produtos)

    return FertilizacaoResultado(produtos=produtos, alertas=alertas, faltantes={})


__all__ = [
    'Fertilizante',
    'FertilizacaoResultado',
    'FOSFATADOS',
    'FOSFATADOS_CHOICES',
    'POTASSICOS',
    'POTASSICOS_CHOICES',
    'GESSO_PADRAO',
    'MOLIBDATO_PADRAO',
    'calcular_formulado',
    'calcular_individual_usuario',
    'calcular_individual_software',
    'obter_fosfatado_por_nome',
    'obter_potassico_por_nome',
]
