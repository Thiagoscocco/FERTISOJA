# -*- coding: utf-8 -*-
"""Rotinas de recomendacao de adubacao para a soja (CQFS-RS/SC, 2016)."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Dict, Literal, Optional

NivelSolo = Literal['muito baixo', 'baixo', 'medio', 'alto', 'muito alto']
EstrategiaMuitoAlto = Literal['zero_e_manutencao', 'repor', 'zero_e_zero']
RoundingMode = Literal['nenhum', 'nearest5']


def _normalizar(texto: str) -> str:
    return unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower().strip()


def _nivel(texto: str) -> NivelSolo:
    mapa = {
        'muito baixo': 'muito baixo',
        'baixo': 'baixo',
        'medio': 'medio',
        'alto': 'alto',
        'muito alto': 'muito alto',
    }
    return mapa.get(_normalizar(texto), 'medio')


def _arredondar(valor: float, modo: RoundingMode) -> float:
    if modo == 'nearest5':
        return round(valor / 5.0) * 5.0
    return round(valor, 1)


def _manutencao(produtividade: float) -> Dict[str, float]:
    extra = max(0.0, produtividade - 3.0)
    return {
        'P2O5': 45.0 + 15.0 * extra,
        'K2O': 75.0 + 25.0 * extra,
    }


def _reposicao(produtividade: float) -> Dict[str, float]:
    return {
        'P2O5': 14.0 * produtividade,
        'K2O': 20.0 * produtividade,
    }


def _correcao_total(nivel: NivelSolo) -> Dict[str, float]:
    p_map = {'muito baixo': 160.0, 'baixo': 80.0, 'medio': 40.0}
    k_map = {'muito baixo': 120.0, 'baixo': 60.0, 'medio': 30.0}
    if nivel not in p_map:
        return {'P2O5': 0.0, 'K2O': 0.0}
    return {'P2O5': p_map[nivel], 'K2O': k_map[nivel]}


def _usar_gradual(argila_pct: Optional[float], ctc: Optional[float]) -> bool:
    if argila_pct is not None and argila_pct < 20.0:
        return True
    if ctc is not None and ctc < 7.5:
        return True
    return False


def _limite_k_linha(k_total: float) -> Dict[str, float]:
    k_linha = min(k_total, 80.0)
    k_lanco = max(0.0, k_total - k_linha)
    return {'K2O_linha': k_linha, 'K2O_lanco': k_lanco}


def _nutrientes_complementares(s_mg_dm3: Optional[float], ph_agua: Optional[float]) -> Dict[str, float]:
    s_so4 = 20.0 if (s_mg_dm3 is not None and s_mg_dm3 < 10.0) else 0.0
    mo = 35.0 if (ph_agua is not None and ph_agua < 5.5) else 0.0
    co = 3.0
    return {'S_SO4': s_so4, 'Mo_g_ha': mo, 'Co_g_ha': co}


@dataclass
class EntradaSoja:
    p_class: NivelSolo
    k_class: NivelSolo
    produtividade: float
    cultivo: int = 1
    argila_pct: Optional[float] = None
    ctc: Optional[float] = None
    teor_s_mg_dm3: Optional[float] = None
    ph_agua: Optional[float] = None
    estrategia_muito_alto: EstrategiaMuitoAlto = 'zero_e_manutencao'
    starter_p2o5_kg_ha: float = 0.0
    starter_k2o_kg_ha: float = 0.0
    rounding: RoundingMode = 'nearest5'


@dataclass
class ResultadoAdubacao:
    totais: Dict[str, float]
    descricao_p: str
    descricao_k: str
    manutencao: Dict[str, float]
    reposicao: Dict[str, float]
    observacoes: list[str]

    @property
    def estrategia_p(self) -> str:
        return self.descricao_p

    @property
    def estrategia_k(self) -> str:
        return self.descricao_k


def recomendar_adubacao_soja(entrada: EntradaSoja) -> ResultadoAdubacao:
    p_class = _nivel(entrada.p_class)
    k_class = _nivel(entrada.k_class)

    gradual_p = _usar_gradual(entrada.argila_pct, entrada.ctc) and p_class in {'muito baixo', 'baixo'}
    gradual_k = _usar_gradual(entrada.argila_pct, entrada.ctc) and k_class in {'muito baixo', 'baixo'}

    manutencao = _manutencao(entrada.produtividade)
    reposicao = _reposicao(entrada.produtividade)
    observacoes: list[str] = []

    if entrada.argila_pct is not None and entrada.argila_pct < 20:
        observacoes.append('Solo arenoso: parcelar P e K.')
    if entrada.ctc is not None and entrada.ctc < 7.5:
        observacoes.append('CTC baixa: atencao ao parcelamento de K.')

    descricao_p = 'Sem adubacao'
    p_total = 0.0
    if p_class in {'muito baixo', 'baixo'}:
        descricao_p = 'Correcao total'
        p_corr = _correcao_total(p_class)['P2O5']
        if gradual_p:
            descricao_p = 'Correcao gradual'
            frac = 2.0 / 3.0 if entrada.cultivo == 1 else 1.0 / 3.0
            p_total = frac * p_corr + manutencao['P2O5']
        else:
            p_total = (p_corr + manutencao['P2O5']) if entrada.cultivo == 1 else manutencao['P2O5']
    elif p_class == 'medio':
        descricao_p = 'Correcao parcial'
        p_corr = _correcao_total('medio')['P2O5']
        p_total = (p_corr + manutencao['P2O5']) if entrada.cultivo == 1 else manutencao['P2O5']
    elif p_class == 'alto':
        descricao_p = 'Manutencao'
        p_total = manutencao['P2O5']
    elif p_class == 'muito alto':
        if entrada.estrategia_muito_alto == 'repor':
            descricao_p = 'Reposicao'
            p_total = reposicao['P2O5']
        elif entrada.estrategia_muito_alto == 'zero_e_zero':
            descricao_p = 'Sem adubacao (muito alto)'
            p_total = 0.0
        else:
            descricao_p = 'Zero no 1o cultivo, manutencao no seguinte'
            p_total = 0.0 if entrada.cultivo == 1 else min(manutencao['P2O5'], reposicao['P2O5'])
        p_total += entrada.starter_p2o5_kg_ha

    descricao_k = 'Sem adubacao'
    k_total = 0.0
    if k_class in {'muito baixo', 'baixo'}:
        descricao_k = 'Correcao total'
        k_corr = _correcao_total(k_class)['K2O']
        if gradual_k:
            descricao_k = 'Correcao gradual'
            frac = 2.0 / 3.0 if entrada.cultivo == 1 else 1.0 / 3.0
            k_total = frac * k_corr + manutencao['K2O']
        else:
            k_total = (k_corr + manutencao['K2O']) if entrada.cultivo == 1 else manutencao['K2O']
    elif k_class == 'medio':
        descricao_k = 'Correcao parcial'
        k_corr = _correcao_total('medio')['K2O']
        k_total = (k_corr + manutencao['K2O']) if entrada.cultivo == 1 else manutencao['K2O']
    elif k_class == 'alto':
        descricao_k = 'Manutencao'
        k_total = manutencao['K2O']
    elif k_class == 'muito alto':
        if entrada.estrategia_muito_alto == 'repor':
            descricao_k = 'Reposicao'
            k_total = reposicao['K2O']
        elif entrada.estrategia_muito_alto == 'zero_e_zero':
            descricao_k = 'Sem adubacao (muito alto)'
            k_total = 0.0
        else:
            descricao_k = 'Zero no 1o cultivo, manutencao no seguinte'
            k_total = 0.0 if entrada.cultivo == 1 else min(manutencao['K2O'], reposicao['K2O'])
        k_total += entrada.starter_k2o_kg_ha

    complementares = _nutrientes_complementares(entrada.teor_s_mg_dm3, entrada.ph_agua)
    k_partes = _limite_k_linha(k_total)

    totais = {
        'P2O5_total': _arredondar(p_total, entrada.rounding),
        'K2O_total': _arredondar(k_total, entrada.rounding),
        'K2O_linha': _arredondar(k_partes['K2O_linha'], entrada.rounding),
        'K2O_lanco': _arredondar(k_partes['K2O_lanco'], entrada.rounding),
        'S_SO4': complementares['S_SO4'],
        'Mo_g_ha': complementares['Mo_g_ha'],
        'Co_g_ha': complementares['Co_g_ha'],
    }

    return ResultadoAdubacao(
        totais=totais,
        descricao_p=descricao_p,
        descricao_k=descricao_k,
        manutencao=manutencao,
        reposicao=reposicao,
        observacoes=observacoes,
    )