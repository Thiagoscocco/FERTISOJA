from __future__ import annotations

import unicodedata
from typing import Sequence

import customtkinter as ctk

from .design_constants import (
    ANALYSIS_COLOR,
    ANALYSIS_HOVER,
    BUTTON_HEIGHT_PRIMARY,
    CALC_COLOR,
    CALC_HOVER,
    CARD_BORDER_COLOR,
    CARD_BORDER_WIDTH,
    CARD_CORNER_RADIUS,
    CARD_GAP,
    ENTRY_WIDTH_SMALL,
    ENTRY_WIDTH_STANDARD,
    FERTILIZER_COLOR,
    FERTILIZER_HOVER,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADING,
    FONT_SIZE_SMALL,
    PADX_MICRO,
    PADX_SMALL,
    PADX_STANDARD,
    PADY_SMALL,
    PADY_STANDARD,
    PANEL_DARK,
    PANEL_LIGHT,
    PLANT_HOVER,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
    SUCCESS_GREEN,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_ORANGE,
    STRAW_HOVER,
)


def _spacing_small() -> int:
    return max(PADY_SMALL - 2, 0)


def make_section(parent: ctk.CTkBaseClass, title: str, heading_font: ctk.CTkFont, *, wrap: int | None = 420) -> ctk.CTkFrame:
    """Cria uma seção com cartão e título estilizado."""
    wrapper = ctk.CTkFrame(
        parent,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        corner_radius=CARD_CORNER_RADIUS,
        border_width=CARD_BORDER_WIDTH,
        border_color=CARD_BORDER_COLOR,
    )
    wrapper.pack(fill="x", expand=False, pady=(PADY_SMALL, 0))
    wrapper.grid_columnconfigure(0, weight=1)

    header = ctk.CTkLabel(
        wrapper,
        text=title,
        font=heading_font,
        anchor="w",
        justify="left",
        wraplength=wrap,
        text_color=(TEXT_PRIMARY, "#4a9eff"),
    )
    header.grid(row=0, column=0, sticky="ew", padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))

    body = ctk.CTkFrame(wrapper, fg_color="transparent")
    body.grid(row=1, column=0, sticky="nsew", padx=PADX_STANDARD, pady=(0, PADY_STANDARD))
    body.grid_columnconfigure(0, weight=1)
    return body


def create_compact_form(
    parent: ctk.CTkBaseClass,
    items: Sequence[Sequence],
    store: dict | None = None,
    defaults: dict | None = None,
    *,
    columns: int = 2,
    entry_width: int | None = None,
) -> dict[str, ctk.CTkEntry]:
    """
    Cria uma grade compacta de rótulos e campos de entrada, ideal para telas mais estreitas.
    `items` deve ser uma sequência com (rótulo, chave_campos, largura_opcional).
    """
    if columns <= 0:
        columns = 1
    if entry_width is None:
        entry_width = ENTRY_WIDTH_STANDARD

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="x", expand=True, pady=(0, CARD_GAP))
    for col in range(columns):
        container.grid_columnconfigure(col, weight=1, uniform="compact")

    created: dict[str, ctk.CTkEntry] = {}

    spacing_y = _spacing_small()

    for idx, item in enumerate(items):
        if len(item) < 2:
            raise ValueError("Cada item deve conter pelo menos (label, chave).")
        label_text = item[0]
        key = item[1]
        width = item[2] if len(item) >= 3 and item[2] is not None else entry_width

        row = idx // columns
        column = idx % columns

        tile = ctk.CTkFrame(container, fg_color="transparent")
        tile.grid(row=row, column=column, sticky="nsew", padx=PADX_SMALL, pady=PADY_SMALL)
        tile.grid_columnconfigure(0, weight=1)

        label = create_label(
            tile,
            label_text,
            weight="bold",
            anchor="w",
            justify="left",
            wraplength=280,
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, spacing_y))

        entry = create_entry_field(tile, width=width)
        entry.grid(row=1, column=0, sticky="ew")

        created[key] = entry
        if store is not None:
            store[key] = entry
        if defaults and key in defaults and defaults[key]:
            entry.insert(0, defaults[key])

    return created


def add_value_row(parent: ctk.CTkBaseClass, text: str, store: dict) -> None:
    """Adiciona uma linha de valor seguindo o padrão do design."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=PADY_SMALL)

    label = ctk.CTkLabel(
        row,
        text=f"{text}:",
        font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
        text_color=(TEXT_PRIMARY, "#4a9eff"),
    )
    label.pack(side="left")

    value = ctk.CTkLabel(
        row,
        text="",
        anchor="w",
        font=ctk.CTkFont(size=FONT_SIZE_SMALL),
        text_color=TEXT_SECONDARY,
    )
    value.pack(side="left", padx=PADX_SMALL)
    store[text] = value


def parse_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def lookup_value(entradas: dict, keyword: str):
    alvo = keyword.lower()
    for chave, valor in entradas.items():
        if normalize_key(chave).startswith(alvo):
            return valor
    return None


def coletar_diagnostico_entradas(entradas: dict) -> dict:
    return {
        "pH_H2O": parse_float(lookup_value(entradas, "ph (")),
        "argila_percent": parse_float(lookup_value(entradas, "argila")),
        "CTC_pH7": parse_float(lookup_value(entradas, "ctc")),
        "MO_percent": parse_float(lookup_value(entradas, "m.o")),
        "P_mg_dm3": parse_float(lookup_value(entradas, "p (mg")),
        "K_mg_dm3": parse_float(lookup_value(entradas, "k (mg")),
        "Ca_cmolc_dm3": parse_float(lookup_value(entradas, "ca (cmol")),
        "Mg_cmolc_dm3": parse_float(lookup_value(entradas, "mg (cmol")),
        "S_mg_dm3": parse_float(lookup_value(entradas, "s (mg")),
        "Cu_mg_dm3": parse_float(lookup_value(entradas, "cu (mg")),
        "Zn_mg_dm3": parse_float(lookup_value(entradas, "zn (mg")),
        "B_mg_dm3": parse_float(lookup_value(entradas, "b (mg")),
        "Mn_mg_dm3": parse_float(lookup_value(entradas, "mn (mg")),
    }


def create_primary_button(parent, text, command, **kwargs):
    """Cria um botão primário seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=PRIMARY_BLUE,
        hover_color=PRIMARY_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_success_button(parent, text, command, **kwargs):
    """Cria um botão de sucesso seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=SUCCESS_GREEN,
        hover_color=PLANT_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_warning_button(parent, text, command, **kwargs):
    """Cria um botão de aviso seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=WARNING_ORANGE,
        hover_color=STRAW_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_fertilizer_button(parent, text, command, **kwargs):
    """Cria um botão específico para fertilizantes."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=FERTILIZER_COLOR,
        hover_color=FERTILIZER_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_calc_button(parent, text, command, **kwargs):
    """Cria um botão específico para cálculos."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=CALC_COLOR,
        hover_color=CALC_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_analysis_button(parent, text, command, **kwargs):
    """Cria um botão específico para análises."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),
        command=command,
        fg_color=ANALYSIS_COLOR,
        hover_color=ANALYSIS_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs,
    )


def create_entry_field(parent, width=ENTRY_WIDTH_STANDARD, **kwargs):
    """Cria um campo de entrada seguindo o padrão do design guide."""
    return ctk.CTkEntry(
        parent,
        width=width,
        font=ctk.CTkFont(size=FONT_SIZE_BODY),
        **kwargs,
    )


def create_label(parent, text, font_size=FONT_SIZE_BODY, weight="normal", **kwargs):
    """Cria um label seguindo o padrão do design guide."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=font_size, weight=weight),
        text_color=(TEXT_PRIMARY, "#4a9eff") if weight == "bold" else TEXT_SECONDARY,
        **kwargs,
    )


__all__ = [
    "add_value_row",
    "coletar_diagnostico_entradas",
    "create_analysis_button",
    "create_calc_button",
    "create_compact_form",
    "create_entry_field",
    "create_fertilizer_button",
    "create_label",
    "create_primary_button",
    "create_success_button",
    "create_warning_button",
    "lookup_value",
    "make_section",
    "normalize_key",
    "parse_float",
]
