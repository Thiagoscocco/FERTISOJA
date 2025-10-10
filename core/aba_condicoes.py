from __future__ import annotations

import customtkinter as ctk
import re

from .context import AppContext, TabHost
from . import diagnostico
from .ui import make_section, add_value_row, coletar_diagnostico_entradas, create_label
from .design_constants import *


def _criar_alerta_widgets(container, alertas, body_font, bold_font):
    """Cria widgets individuais para cada alerta com formatação adequada seguindo o design guide."""
    # Limpa widgets existentes
    for widget in container.winfo_children():
        widget.destroy()
    
    if not alertas:
        label = create_label(container, 'Nenhum alerta específico identificado.', 
                           font_size=FONT_SIZE_BODY, weight='normal')
        label.configure(anchor='w', justify='left', wraplength=520, text_color=WARNING_ORANGE)
        label.pack(fill='x', pady=PADY_SMALL)
        return
    
    for alerta in alertas:
        # Remove o traço inicial se existir
        alerta = alerta.lstrip('- ')
        
        # Encontra texto em maiúscula antes dos dois pontos
        pattern = r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+):'
        match = re.search(pattern, alerta)
        
        if match:
            uppercase_part = match.group(1).strip()
            rest_of_text = alerta[match.end():].strip()
            
            # Cria um frame para o alerta
            alerta_frame = ctk.CTkFrame(container, fg_color='transparent')
            alerta_frame.pack(fill='x', pady=PADY_SMALL)
            
            # Label em negrito para a parte em maiúscula
            bold_label = create_label(alerta_frame, f"{uppercase_part}:", 
                                    font_size=FONT_SIZE_BODY, weight='bold')
            bold_label.configure(text_color=WARNING_ORANGE)
            bold_label.pack(side='left')
            
            # Label normal para o resto do texto
            normal_label = create_label(alerta_frame, f" {rest_of_text}", 
                                      font_size=FONT_SIZE_BODY, weight='normal')
            normal_label.configure(text_color=WARNING_ORANGE, anchor='w', justify='left', wraplength=520)
            normal_label.pack(side='left', fill='x', expand=True)
        else:
            # Se não há padrão de maiúscula, cria um label simples
            label = create_label(container, alerta, font_size=FONT_SIZE_BODY, weight='normal')
            label.configure(anchor='w', justify='left', wraplength=520, text_color=WARNING_ORANGE)
            label.pack(fill='x', pady=PADY_SMALL)


def add_tab(tabhost: TabHost, ctx: AppContext):
    heading_font = getattr(ctx, 'heading_font', ctk.CTkFont(size=FONT_SIZE_HEADING, weight='bold'))

    aba = tabhost.add_tab('🌍 Condições do Solo')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)
    outer.grid_columnconfigure(0, weight=1)

    sec_prop = make_section(outer, '🏗️ PROPRIEDADES GERAIS DO SOLO', heading_font)
    for nome in ['Classe do teor de Argila', 'CTC', 'M.O.']:
        add_value_row(sec_prop, nome, ctx.labels_classificacao)

    sec_macro = make_section(outer, '🌿 MACRONUTRIENTES', heading_font)
    for nome in ['Fósforo (P)', 'Potássio (K)', 'Cálcio (Ca)', 'Magnésio (Mg)', 'Enxofre (S)']:
        add_value_row(sec_macro, nome, ctx.labels_classificacao)

    sec_micro = make_section(outer, '⚗️ MICRONUTRIENTES', heading_font)
    for nome in ['Zinco (Zn)', 'Cobre (Cu)', 'Boro (B)', 'Manganês (Mn)']:
        add_value_row(sec_micro, nome, ctx.labels_classificacao)

    body_font = ctk.CTkFont(size=FONT_SIZE_SMALL)
    bold_font = ctk.CTkFont(size=FONT_SIZE_SMALL, weight='bold')

    resumo_section = make_section(outer, '📋 RESUMO DO DIAGNÓSTICO', heading_font)
    resumo_section.grid_columnconfigure(0, weight=0)
    resumo_section.grid_columnconfigure(1, weight=1)
    summary_vars = {
        'p': ctk.StringVar(value='-'),
        'k': ctk.StringVar(value='-'),
        'tecnica': ctk.StringVar(value='Informe os dados e calcule na aba principal para obter o diagnóstico.'),
    }
    resumo_rows = [
        ('Resposta ao P:', 'p'),
        ('Resposta ao K:', 'k'),
        ('Recomendação:', 'tecnica'),
    ]
    for idx, (rotulo, chave) in enumerate(resumo_rows):
        create_label(resumo_section, rotulo, font_size=FONT_SIZE_SMALL, weight='bold').grid(row=idx, column=0, sticky='w', pady=PADY_SMALL)
        value_label = create_label(resumo_section, '', font_size=FONT_SIZE_SMALL, weight='normal')
        value_label.configure(textvariable=summary_vars[chave], anchor='w', justify='left')
        value_label.grid(row=idx, column=1, sticky='w', pady=PADY_SMALL)

    alertas_section = make_section(outer, '⚠️ ALERTAS', heading_font)
    alertas_container = ctk.CTkFrame(alertas_section, fg_color='transparent')
    alertas_container.pack(fill='x')

    if getattr(ctx, 'logo_image', None) is not None:
        logo_label = ctk.CTkLabel(aba, image=ctx.logo_image, text='')
        logo_label.pack(anchor='se', padx=PADX_STANDARD, pady=PADY_STANDARD)
        logo_label.image = ctx.logo_image

    ctx.condicoes_controls = {
        'summary': summary_vars,
        'alertas_container': alertas_container,
    }
    return ctx.condicoes_controls


def atualizar(ctx: AppContext):
    controles = getattr(ctx, 'condicoes_controls', None)
    if not controles:
        return

    entradas = ctx.get_entradas()
    dados_diag = coletar_diagnostico_entradas(entradas)
    diag = diagnostico.diagnosticar_soja(dados_diag)
    ctx._diag_cache = diag  # reutilizado por outras abas

    summary = controles['summary']
    props = diag['propriedades']
    macros = diag['macronutrientes']
    alertas = diag['alertas']
    observacoes = diag['observacoes']

    p_prob = macros['P'].get('prob_resposta')
    summary['p'].set(p_prob if p_prob else '-')

    k_prob = macros['K'].get('prob_resposta')
    summary['k'].set(k_prob if k_prob else '-')

    if macros['P'].get('classe') in ('Muito Baixo', 'Baixo') or macros['K'].get('classe') in ('Muito Baixo', 'Baixo'):
        summary['tecnica'].set(' Repetir a análise na próxima safra.')
    else:
        summary['tecnica'].set(' Repetir a análise na próxima safra para monitoramento.')

    body_font = ctk.CTkFont(size=FONT_SIZE_SMALL)
    bold_font = ctk.CTkFont(size=FONT_SIZE_SMALL, weight='bold')
    _criar_alerta_widgets(controles['alertas_container'], alertas, body_font, bold_font)


