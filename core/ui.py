from __future__ import annotations

import unicodedata

import customtkinter as ctk
from .design_constants import *


def make_section(parent, title, heading_font):
    """Cria uma seção com título seguindo o padrão do design guide."""
    wrapper = ctk.CTkFrame(parent, fg_color=(PANEL_LIGHT, PANEL_DARK))
    wrapper.pack(fill='x', pady=(PADY_SMALL, 0))
    
    # Header com emoji e texto em maiúsculo
    header = ctk.CTkLabel(wrapper, 
                         text=title, 
                         font=heading_font, 
                         anchor='w',
                         text_color=(TEXT_PRIMARY, "#4a9eff"))
    header.pack(anchor='w', padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))
    
    # Body da seção
    body = ctk.CTkFrame(wrapper, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=(0, PADY_STANDARD))
    return body


def add_value_row(parent, text, store):
    """Adiciona uma linha de valor seguindo o padrão do design guide."""
    row = ctk.CTkFrame(parent, fg_color='transparent')
    row.pack(fill='x', pady=PADY_SMALL)
    
    label = ctk.CTkLabel(row, 
                        text=f"{text}:", 
                        font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight='bold'),
                        text_color=(TEXT_PRIMARY, "#4a9eff"))
    label.pack(side='left')
    
    value = ctk.CTkLabel(row, 
                        text='', 
                        anchor='w',
                        font=ctk.CTkFont(size=FONT_SIZE_SMALL),
                        text_color=TEXT_SECONDARY)
    value.pack(side='left', padx=PADX_SMALL)
    store[text] = value


def parse_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '.')
    if text == '':
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_key(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text or '')
    return normalized.encode('ascii', 'ignore').decode('ascii').lower()


def lookup_value(entradas: dict, keyword: str):
    alvo = keyword.lower()
    for chave, valor in entradas.items():
        if normalize_key(chave).startswith(alvo):
            return valor
    return None


def coletar_diagnostico_entradas(entradas: dict) -> dict:
    return {
        'pH_H2O': parse_float(lookup_value(entradas, 'ph (')),
        'argila_percent': parse_float(lookup_value(entradas, 'argila')),
        'CTC_pH7': parse_float(lookup_value(entradas, 'ctc')),
        'MO_percent': parse_float(lookup_value(entradas, 'm.o')),
        'P_mg_dm3': parse_float(lookup_value(entradas, 'p (mg')),
        'K_mg_dm3': parse_float(lookup_value(entradas, 'k (mg')),
        'Ca_cmolc_dm3': parse_float(lookup_value(entradas, 'ca (cmol')),
        'Mg_cmolc_dm3': parse_float(lookup_value(entradas, 'mg (cmol')),
        'S_mg_dm3': parse_float(lookup_value(entradas, 's (mg')),
        'Cu_mg_dm3': parse_float(lookup_value(entradas, 'cu (mg')),
        'Zn_mg_dm3': parse_float(lookup_value(entradas, 'zn (mg')),
        'B_mg_dm3': parse_float(lookup_value(entradas, 'b (mg')),
        'Mn_mg_dm3': parse_float(lookup_value(entradas, 'mn (mg')),
    }


def create_primary_button(parent, text, command, **kwargs):
    """Cria um botão primário seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=PRIMARY_BLUE,
        hover_color=PRIMARY_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_success_button(parent, text, command, **kwargs):
    """Cria um botão de sucesso seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=SUCCESS_GREEN,
        hover_color=PLANT_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_warning_button(parent, text, command, **kwargs):
    """Cria um botão de aviso seguindo o padrão do design guide."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=WARNING_ORANGE,
        hover_color=STRAW_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_fertilizer_button(parent, text, command, **kwargs):
    """Cria um botão específico para fertilizantes."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=FERTILIZER_COLOR,
        hover_color=FERTILIZER_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_calc_button(parent, text, command, **kwargs):
    """Cria um botão específico para cálculos."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=CALC_COLOR,
        hover_color=CALC_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_analysis_button(parent, text, command, **kwargs):
    """Cria um botão específico para análises."""
    return ctk.CTkButton(
        parent,
        text=text.upper(),  # Texto em maiúsculo
        command=command,
        fg_color=ANALYSIS_COLOR,
        hover_color=ANALYSIS_HOVER,
        font=ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"),
        height=BUTTON_HEIGHT_PRIMARY,
        **kwargs
    )


def create_entry_field(parent, width=ENTRY_WIDTH_STANDARD, **kwargs):
    """Cria um campo de entrada seguindo o padrão do design guide."""
    return ctk.CTkEntry(
        parent,
        width=width,
        font=ctk.CTkFont(size=FONT_SIZE_BODY),
        **kwargs
    )


def create_label(parent, text, font_size=FONT_SIZE_BODY, weight="normal", **kwargs):
    """Cria um label seguindo o padrão do design guide."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=font_size, weight=weight),
        text_color=(TEXT_PRIMARY, "#4a9eff") if weight == "bold" else TEXT_SECONDARY,
        **kwargs
    )


