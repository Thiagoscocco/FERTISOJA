# -*- coding: utf-8 -*-
"""Aba de resultados consolidados."""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, List, Sequence, Tuple

import customtkinter as ctk

from fertilizacao import GESSO_PADRAO, MOLIBDATO_PADRAO

from .context import AppContext, TabHost
from .design_constants import (
    FONT_SIZE_BODY,
    FONT_SIZE_HEADING,
    PANEL_DARK,
    PANEL_LIGHT,
    PADX_SMALL,
    PADX_STANDARD,
    PADY_SMALL,
    PADY_STANDARD,
    PRIMARY_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


SUPPLEMENT_NAMES: set[str] = {GESSO_PADRAO.nome, MOLIBDATO_PADRAO.nome}
SACA_PESO_KG = 50.0
FRAME_BORDER_COLOR = "#1f1f1f"


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().strip()


def _parse_number(text: str | None) -> float:
    if not text:
        return 0.0
    match = re.search(r"([-+]?\d+(?:[.,]\d+)?)", text)
    if not match:
        return 0.0
    return float(match.group(1).replace(",", "."))


def _format_number(valor: float) -> str:
    abs_val = abs(valor)
    if abs_val >= 1000:
        return f"{valor:.0f}"
    if abs_val >= 100:
        return f"{valor:.1f}"
    if abs_val >= 10:
        return f"{valor:.2f}"
    if abs_val >= 1:
        return f"{valor:.2f}"
    return f"{valor:.3f}"


def _format_mass(valor_kg: float, unidade: str, por_area: bool) -> str:
    unidade = (unidade or "kg").lower()
    if unidade.startswith("saca"):
        numero = valor_kg / SACA_PESO_KG
        sufixo = " sacas/ha" if por_area else " sacas"
    elif unidade == "t":
        numero = valor_kg / 1000.0
        sufixo = " t/ha" if por_area else " t"
    else:
        numero = valor_kg
        sufixo = " kg/ha" if por_area else " kg"
    return f"{_format_number(numero)}{sufixo}"


def _get_area_ha(ctx: AppContext) -> float:
    campo = ctx.campos.get("Area (Ha)")
    if campo is None:
        return 0.0
    try:
        texto = str(campo.get()).strip().replace(",", ".")
        return float(texto) if texto else 0.0
    except Exception:
        return 0.0


def _obter_calcario(ctx: AppContext) -> Dict[str, float | str]:
    dados = getattr(ctx, "calagem_resultado", None)
    if isinstance(dados, dict):
        return dados

    texto_dose = ""
    label = ctx.labels_resultado.get("Calcario (PRNT 100%)")
    if label is not None:
        try:
            texto_dose = str(label.cget("text"))
        except Exception:
            texto_dose = ""

    dose_t_ha = max(_parse_number(texto_dose), 0.0)
    dose_kg_ha = dose_t_ha * 1000.0
    area = _get_area_ha(ctx)
    return {
        "dose_t_ha": dose_t_ha,
        "kg_ha": dose_kg_ha,
        "kg_total": dose_kg_ha * max(area, 0.0),
        "modo": "",
        "epoca": "",
        "tipo": "",
        "tecnica": "",
    }


def _selecionar_produtos(produtos: Sequence[Tuple[str, float]]) -> List[Tuple[str, float]]:
    return list(produtos)


def _obter_fertilizantes(ctx: AppContext) -> Dict[str, object]:
    controles = getattr(ctx, "fertilizacao_controls", None)
    if not isinstance(controles, dict):
        return {"produtos": [], "suplementos": [], "alertas": [], "faltantes": {}, "modo": "", "submodo": ""}

    resultado = controles.get("ultimo_resultado")
    modo = controles.get("modo_var").get() if controles.get("modo_var") is not None else ""
    submodo = controles.get("submodo_var").get() if controles.get("submodo_var") is not None else ""
    produtos_base = resultado.produtos if resultado is not None else []
    produtos = _selecionar_produtos(produtos_base)
    alertas = list(getattr(resultado, "alertas", []) or [])
    faltantes = dict(getattr(resultado, "faltantes", {}) or {})
    suplementos = [(nome, qtd) for nome, qtd in produtos_base if nome in SUPPLEMENT_NAMES]
    return {
        "produtos": produtos,
        "suplementos": suplementos,
        "alertas": alertas,
        "faltantes": faltantes,
        "modo": modo,
        "submodo": submodo,
    }


def _limpar_conteudo(container: ctk.CTkFrame) -> None:
    for widget in container.winfo_children():
        widget.destroy()


def _preencher_linhas(
    container: ctk.CTkFrame,
    itens: Iterable[Tuple[str, str]],
    label_font: ctk.CTkFont,
    value_font: ctk.CTkFont,
    *,
    align_right: bool = False,
) -> None:
    _limpar_conteudo(container)
    for idx, (rotulo, valor) in enumerate(itens):
        linha = ctk.CTkFrame(container, fg_color="transparent")
        sticky = "e" if align_right else "ew"
        linha.grid(row=idx, column=0, sticky=sticky, padx=PADX_STANDARD, pady=(PADY_SMALL, PADY_SMALL + 8))
        if align_right:
            linha.grid_columnconfigure(0, weight=1)
            linha.grid_columnconfigure(1, weight=0)
            label_sticky = "e"
            value_sticky = "e"
            label_anchor = "e"
            value_anchor = "e"
        else:
            linha.grid_columnconfigure(0, weight=1)
            linha.grid_columnconfigure(1, weight=0)
            label_sticky = "w"
            value_sticky = "e"
            label_anchor = "w"
            value_anchor = "e"
        rotulo_label = ctk.CTkLabel(
            linha,
            text=rotulo,
            font=label_font,
            anchor=label_anchor,
            text_color=(TEXT_PRIMARY, "#4a9eff"),
        )
        rotulo_label.grid(row=0, column=0, sticky=label_sticky)
        valor_label = ctk.CTkLabel(
            linha,
            text=valor,
            font=value_font,
            anchor=value_anchor,
            text_color=TEXT_SECONDARY,
        )
        valor_label.grid(row=0, column=1, sticky=value_sticky, padx=(PADX_SMALL, 0))


def _montar_itens_per_area(
    calcario: Dict[str, float | str],
    fertilizantes: Dict[str, object],
    unidade: str,
) -> List[Tuple[str, str]]:
    itens: List[Tuple[str, str]] = []
    valor_calcario = _format_mass(float(calcario.get("kg_ha", 0.0)), "kg", por_area=True)
    itens.append(("Calcario", valor_calcario))

    for nome, quantidade in fertilizantes.get("produtos", []):
        valor = _format_mass(float(quantidade), unidade, por_area=True)
        itens.append((nome, valor))
    return itens


def _montar_itens_totais(
    calcario: Dict[str, float | str],
    fertilizantes: Dict[str, object],
    unidade: str,
    area: float,
) -> List[Tuple[str, str]]:
    itens: List[Tuple[str, str]] = []
    kg_total_calcario = float(calcario.get("kg_total", 0.0))
    valor_calcario = _format_mass(kg_total_calcario, "kg", por_area=False)
    itens.append(("Calcario", valor_calcario))

    for nome, quantidade in fertilizantes.get("produtos", []):
        total_kg = float(quantidade) * max(area, 0.0)
        valor = _format_mass(total_kg, unidade, por_area=False)
        itens.append((nome, valor))
    return itens


def _texto_calcario(calcario: Dict[str, float | str]) -> str:
    partes: List[str] = []
    modo = str(calcario.get("modo", "")).strip()
    epoca = str(calcario.get("epoca", "")).strip()
    tipo = str(calcario.get("tipo", "")).strip()
    tecnica = str(calcario.get("tecnica", "")).strip()

    if modo:
        partes.append(modo)
    if epoca:
        partes.append(epoca)
    if tipo:
        partes.append(tipo)
    if tecnica:
        partes.append(tecnica)

    if not partes:
        return "Calcule a recomendação de calagem para visualizar orientações específicas."
    return "\n".join(partes)


def _texto_fertilizantes(
    fertilizantes: Dict[str, object],
    area: float,
) -> str:
    partes: List[str] = []
    modo_norm = _normalize(fertilizantes.get("modo"))
    submodo_norm = _normalize(fertilizantes.get("submodo"))

    if modo_norm.startswith("fertilizantes form"):
        partes.append("Formulado selecionado com complementos calculados automaticamente.")
    elif submodo_norm.startswith("escolha do usuario"):
        partes.append("Fertilizantes individuais definidos pelo usuário.")
    elif modo_norm:
        partes.append("Aplicando fertilizantes individuais sugeridos pelo software.")

    alertas: List[str] = fertilizantes.get("alertas", []) or []
    faltantes: Dict[str, float] = fertilizantes.get("faltantes", {}) or {}
    if alertas:
        partes.extend(alertas)
    for nutriente, restante in faltantes.items():
        partes.append(f"Atenção: {nutriente} não atendido ({_format_number(float(restante))} kg/ha).")

    suplementos: List[Tuple[str, float]] = fertilizantes.get("suplementos", []) or []
    if suplementos:
        for nome, qtd in suplementos:
            if nome == MOLIBDATO_PADRAO.nome:
                partes.append(f"Incluir {nome}: {_format_number(qtd * 1000)} g/ha.")
            else:
                partes.append(f"Incluir {nome}: {_format_number(qtd)} kg/ha.")

    if area <= 0:
        partes.append("Informe a área total na aba de dados para calcular quantidades totais.")

    if not partes:
        return "Calcule a adubação e configure os fertilizantes para visualizar recomendações."
    return "\n".join(partes)


def _coletar_dados(ctx: AppContext) -> Tuple[Dict[str, float | str], Dict[str, object], float]:
    calcario = _obter_calcario(ctx)
    fertilizantes = _obter_fertilizantes(ctx)
    area = _get_area_ha(ctx)
    return calcario, fertilizantes, area


def _render_per_area(ctx: AppContext) -> None:
    controles = getattr(ctx, "resultados_controls", None)
    if not isinstance(controles, dict):
        return
    cache = controles.get("dados_cache")
    if cache is None:
        cache = _coletar_dados(ctx)
        controles["dados_cache"] = cache
    calcario, fertilizantes, area = cache
    unidade = controles["unidade_ha"].get()
    itens_ha = _montar_itens_per_area(calcario, fertilizantes, unidade)
    _preencher_linhas(
        controles["lista_ha"],
        itens_ha,
        controles["label_font"],
        controles["value_font"],
        align_right=False,
    )


def _render_total(ctx: AppContext) -> None:
    controles = getattr(ctx, "resultados_controls", None)
    if not isinstance(controles, dict):
        return
    cache = controles.get("dados_cache")
    if cache is None:
        cache = _coletar_dados(ctx)
        controles["dados_cache"] = cache
    calcario, fertilizantes, area = cache
    unidade = controles["unidade_total"].get()
    itens_total = _montar_itens_totais(calcario, fertilizantes, unidade, area)
    _preencher_linhas(
        controles["lista_total"],
        itens_total,
        controles["label_font"],
        controles["value_font"],
        align_right=True,
    )


def _refresh_all(ctx: AppContext) -> None:
    controles = getattr(ctx, "resultados_controls", None)
    if not isinstance(controles, dict):
        return
    calcario, fertilizantes, area = _coletar_dados(ctx)
    controles["dados_cache"] = (calcario, fertilizantes, area)
    itens_ha = _montar_itens_per_area(calcario, fertilizantes, controles["unidade_ha"].get())
    itens_total = _montar_itens_totais(calcario, fertilizantes, controles["unidade_total"].get(), area)
    _preencher_linhas(
        controles["lista_ha"],
        itens_ha,
        controles["label_font"],
        controles["value_font"],
        align_right=False,
    )
    _preencher_linhas(
        controles["lista_total"],
        itens_total,
        controles["label_font"],
        controles["value_font"],
        align_right=True,
    )
    controles["calcario_var"].set(_texto_calcario(calcario))
    controles["fertilizantes_var"].set(_texto_fertilizantes(fertilizantes, area))


def atualizar(ctx: AppContext) -> None:
    _refresh_all(ctx)


def add_tab(tabhost: TabHost, ctx: AppContext):
    heading_font = getattr(ctx, "heading_font", ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"))
    section_font = ctk.CTkFont(size=FONT_SIZE_HEADING + 1, weight="bold")
    label_font = ctk.CTkFont(size=FONT_SIZE_BODY + 2, weight="bold")
    value_font = ctk.CTkFont(size=FONT_SIZE_BODY + 1)

    aba = tabhost.add_tab("Resultados")
    outer = ctk.CTkScrollableFrame(aba, fg_color="transparent")
    outer.pack(fill="both", expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)
    outer.grid_columnconfigure(0, weight=1)

    titulo_global = ctk.CTkLabel(
        outer,
        text="RESULTADOS FINAIS",
        font=section_font,
        text_color=(TEXT_PRIMARY, "#4a9eff"),
        anchor="center",
    )
    titulo_global.pack(fill="x", pady=(0, PADY_STANDARD))

    quadro_principal = ctk.CTkFrame(
        outer,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        border_width=2,
        border_color=FRAME_BORDER_COLOR,
        corner_radius=18,
    )
    quadro_principal.pack(fill="x", pady=(0, PADY_STANDARD))
    quadro_principal.grid_columnconfigure(0, weight=1)
    quadro_principal.grid_columnconfigure(1, weight=1)

    def _add_title(parent: ctk.CTkFrame, column: int, texto: str, sticky_title: str) -> None:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=0, column=column, sticky=sticky_title, padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)
        container.grid_columnconfigure(2, weight=1)

        barra_esq = ctk.CTkFrame(container, fg_color=PRIMARY_BLUE, height=4, corner_radius=2, width=50)
        barra_esq.grid(row=0, column=0, sticky="ew", padx=(0, PADX_SMALL))
        barra_esq.grid_propagate(False)
        titulo_label = ctk.CTkLabel(
            container,
            text=texto,
            font=heading_font,
            text_color=(TEXT_PRIMARY, "#4a9eff"),
            anchor="center",
        )
        titulo_label.grid(row=0, column=1, sticky="n")
        barra_dir = ctk.CTkFrame(container, fg_color=PRIMARY_BLUE, height=4, corner_radius=2, width=50)
        barra_dir.grid(row=0, column=2, sticky="ew", padx=(PADX_SMALL, 0))
        barra_dir.grid_propagate(False)

    _add_title(quadro_principal, 0, "POR HECTARE", "w")
    _add_title(quadro_principal, 1, "ÁREA TOTAL", "e")

    unidade_ha = ctk.StringVar(value="kg")
    unidade_total = ctk.StringVar(value="kg")

    unidade_ha_btn = ctk.CTkSegmentedButton(
        quadro_principal,
        values=["kg", "t", "sacas"],
        variable=unidade_ha,
        command=lambda _: _render_per_area(ctx),
    )
    unidade_ha_btn.grid(row=1, column=0, pady=(0, PADY_SMALL), sticky="n")

    unidade_total_btn = ctk.CTkSegmentedButton(
        quadro_principal,
        values=["kg", "t", "sacas"],
        variable=unidade_total,
        command=lambda _: _render_total(ctx),
    )
    unidade_total_btn.grid(row=1, column=1, pady=(0, PADY_SMALL), sticky="n")

    lista_ha = ctk.CTkFrame(quadro_principal, fg_color="transparent")
    lista_ha.grid(row=2, column=0, sticky="nsew", padx=(PADX_STANDARD, PADX_SMALL), pady=(PADY_SMALL, PADY_STANDARD))
    lista_total = ctk.CTkFrame(quadro_principal, fg_color="transparent")
    lista_total.grid(row=2, column=1, sticky="nsew", padx=(PADX_SMALL, PADX_STANDARD), pady=(PADY_SMALL, PADY_STANDARD))

    quadro_recomendacoes = ctk.CTkFrame(
        outer,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        border_width=2,
        border_color=FRAME_BORDER_COLOR,
        corner_radius=18,
    )
    quadro_recomendacoes.pack(fill="x", pady=(0, PADY_STANDARD))
    quadro_recomendacoes.grid_columnconfigure(0, weight=1)
    quadro_recomendacoes.grid_columnconfigure(1, weight=1)

    _add_title(quadro_recomendacoes, 0, "CALCÁRIO", "w")
    _add_title(quadro_recomendacoes, 1, "FERTILIZANTES", "e")

    calcario_txt = ctk.StringVar(value="Calcule a calagem para ver orientações.")
    fert_txt = ctk.StringVar(value="Configure os fertilizantes para ver orientações.")

    calcario_label = ctk.CTkLabel(
        quadro_recomendacoes,
        textvariable=calcario_txt,
        font=value_font,
        text_color=TEXT_SECONDARY,
        wraplength=420,
        justify="left",
        anchor="w",
    )
    calcario_label.grid(row=1, column=0, sticky="nsew", padx=PADX_STANDARD, pady=(PADY_SMALL, PADY_STANDARD))

    fert_label = ctk.CTkLabel(
        quadro_recomendacoes,
        textvariable=fert_txt,
        font=value_font,
        text_color=TEXT_SECONDARY,
        wraplength=420,
        justify="right",
        anchor="e",
    )
    fert_label.grid(row=1, column=1, sticky="nsew", padx=PADX_STANDARD, pady=(PADY_SMALL, PADY_STANDARD))

    controles = {
        "unidade_ha": unidade_ha,
        "unidade_total": unidade_total,
        "lista_ha": lista_ha,
        "lista_total": lista_total,
        "calcario_var": calcario_txt,
        "fertilizantes_var": fert_txt,
        "label_font": label_font,
        "value_font": value_font,
        "dados_cache": None,
    }

    ctx.resultados_controls = controles
    ctx.atualizar_resultados = lambda: _refresh_all(ctx)

    _refresh_all(ctx)


__all__ = ["add_tab", "atualizar"]
