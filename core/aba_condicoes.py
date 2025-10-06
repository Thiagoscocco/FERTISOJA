from __future__ import annotations

import customtkinter as ctk

from .context import AppContext, TabHost
from . import diagnostico
from .ui import make_section, add_value_row, coletar_diagnostico_entradas


def add_tab(tabhost: TabHost, ctx: AppContext):
    heading_font = getattr(ctx, 'heading_font', ctk.CTkFont(size=13, weight='bold'))

    aba = tabhost.add_tab('Condições do Solo')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=16, pady=16)
    outer.grid_columnconfigure(0, weight=1)

    sec_prop = make_section(outer, 'PROPRIEDADES GERAIS DO SOLO', heading_font)
    for nome in ['Classe do teor de Argila', 'CTC', 'M.O.']:
        add_value_row(sec_prop, nome, ctx.labels_classificacao)

    sec_macro = make_section(outer, 'MACRONUTRIENTES', heading_font)
    for nome in ['Fósforo (P)', 'Potássio (K)', 'Cálcio (Ca)', 'Magnésio (Mg)', 'Enxofre (S)']:
        add_value_row(sec_macro, nome, ctx.labels_classificacao)

    sec_micro = make_section(outer, 'MICRONUTRIENTES', heading_font)
    for nome in ['Zinco (Zn)', 'Cobre (Cu)', 'Boro (B)', 'Manganês (Mn)']:
        add_value_row(sec_micro, nome, ctx.labels_classificacao)

    body_font = ctk.CTkFont(size=11)
    bold_font = ctk.CTkFont(size=11, weight='bold')

    resumo_section = make_section(outer, 'RESUMO DO DIAGNÓSTICO', heading_font)
    resumo_section.grid_columnconfigure(0, weight=0)
    resumo_section.grid_columnconfigure(1, weight=1)
    summary_vars = {
        'textura': ctk.StringVar(value='Classe de argila: - | CTC: -'),
        'mo': ctk.StringVar(value='Matéria orgânica: -'),
        'p': ctk.StringVar(value='-'),
        'k': ctk.StringVar(value='-'),
        'tecnica': ctk.StringVar(value='Informe os dados e calcule na aba principal para obter o diagnóstico.'),
    }
    resumo_rows = [
        ('Textura e CTC:', 'textura'),
        ('Matéria orgânica:', 'mo'),
        ('Resposta ao P:', 'p'),
        ('Resposta ao K:', 'k'),
        ('Recomendação:', 'tecnica'),
    ]
    for idx, (rotulo, chave) in enumerate(resumo_rows):
        ctk.CTkLabel(resumo_section, text=rotulo, font=bold_font).grid(row=idx, column=0, sticky='w', pady=2)
        ctk.CTkLabel(resumo_section, textvariable=summary_vars[chave], font=body_font, anchor='w', justify='left').grid(row=idx, column=1, sticky='w', pady=2)

    alertas_section = make_section(outer, 'ALERTAS', heading_font)
    alertas_label = ctk.CTkLabel(alertas_section, text='Preencha os dados para gerar alertas.', font=body_font, anchor='w', justify='left', wraplength=520, text_color='#F4B942')
    alertas_label.pack(fill='x')

    notas_section = make_section(outer, 'NOTAS', heading_font)
    observacoes_label = ctk.CTkLabel(notas_section, text='', font=body_font, anchor='w', justify='left', wraplength=520)
    observacoes_label.pack(fill='x')

    if getattr(ctx, 'logo_image', None) is not None:
        logo_label = ctk.CTkLabel(aba, image=ctx.logo_image, text='')
        logo_label.pack(anchor='se', padx=12, pady=12)
        logo_label.image = ctx.logo_image

    ctx.condicoes_controls = {
        'summary': summary_vars,
        'alertas_label': alertas_label,
        'observacoes_label': observacoes_label,
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

    classe_argila = props.get('classe_argila_num')
    classe_ctc = props.get('classe_ctc') or '-'
    classe_desc = {1: 'Muito argilosa', 2: 'Argilosa', 3: 'Média', 4: 'Arenosa'}
    if classe_argila:
        textura_txt = f"Classe de argila: {classe_argila} ({classe_desc.get(classe_argila, '-')}) | CTC: {classe_ctc}"
    else:
        textura_txt = f"Classe de argila: - | CTC: {classe_ctc}"
    summary['textura'].set(textura_txt)

    mo_valor = dados_diag.get('MO_percent')
    mo_classe = props.get('classe_mo')
    if mo_classe and mo_valor is not None:
        summary['mo'].set(f"Matéria orgânica: {mo_classe} ({mo_valor:.1f}%)")
    elif mo_classe:
        summary['mo'].set(f"Matéria orgânica: {mo_classe}")
    else:
        summary['mo'].set('Matéria orgânica: -')

    p_prob = macros['P'].get('prob_resposta')
    summary['p'].set(p_prob if p_prob else '-')

    k_prob = macros['K'].get('prob_resposta')
    summary['k'].set(k_prob if k_prob else '-')

    if macros['P'].get('classe') in ('Muito Baixo', 'Baixo') or macros['K'].get('classe') in ('Muito Baixo', 'Baixo'):
        summary['tecnica'].set('Repetir a análise na próxima safra.\nAlta chance de resposta a P/K.')
    else:
        summary['tecnica'].set('Repetir a análise na próxima safra para monitoramento.')

    if alertas:
        controles['alertas_label'].configure(text='\n'.join(f'- {msg}' for msg in alertas))
    else:
        controles['alertas_label'].configure(text='Nenhum alerta específico identificado.')

    observacoes_texto = '\n'.join(f'• {valor}' for valor in observacoes.values())
    controles['observacoes_label'].configure(text=observacoes_texto)


