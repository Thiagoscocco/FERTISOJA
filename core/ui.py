from __future__ import annotations

import unicodedata

import customtkinter as ctk


def make_section(parent, title, heading_font):
    wrapper = ctk.CTkFrame(parent, fg_color='transparent')
    wrapper.pack(fill='x', pady=(8, 0))
    header = ctk.CTkLabel(wrapper, text=title, font=heading_font, anchor='w')
    header.pack(anchor='w', padx=10, pady=(10, 6))
    body = ctk.CTkFrame(wrapper, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    return body


def add_value_row(parent, text, store):
    row = ctk.CTkFrame(parent, fg_color='transparent')
    row.pack(fill='x', pady=3)
    label = ctk.CTkLabel(row, text=f"{text}:", font=ctk.CTkFont(size=11, weight='bold'))
    label.pack(side='left')
    value = ctk.CTkLabel(row, text='', anchor='w')
    value.pack(side='left', padx=10)
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


