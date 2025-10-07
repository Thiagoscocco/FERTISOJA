from __future__ import annotations

import customtkinter as ctk

from .context import AppContext, TabHost
from .ui import make_section, parse_float, normalize_key
from .adubacao_dados import EntradaSoja, recomendar_adubacao_soja


def add_tab(tabhost: TabHost, ctx: AppContext):
    heading_font = getattr(ctx, 'heading_font', ctk.CTkFont(size=13, weight='bold'))
    body_font = ctk.CTkFont(size=11)
    bold_font = ctk.CTkFont(size=11, weight='bold')

    aba = tabhost.add_tab('Recomendação de Adubação')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=16, pady=16)
    outer.grid_columnconfigure(0, weight=1)

    sec_summary = make_section(outer, 'NECESSIDADES DE NUTRIENTES', heading_font)
    sec_summary.grid_columnconfigure(0, weight=0)
    sec_summary.grid_columnconfigure(1, weight=1)

    summary_vars = {
        'P2O5': ctk.StringVar(value='-'),
        'K2O': ctk.StringVar(value='-'),
        'S': ctk.StringVar(value='-'),
        'Mo': ctk.StringVar(value='-'),
    }
    summary_rows = [
        ('Fósforo (P2O5):', 'P2O5'),
        ('Potássio (K2O):', 'K2O'),
        ('Enxofre (S-SO4):', 'S'),
        ('Molibdênio (Mo):', 'Mo'),
    ]
    for idx, (rotulo, chave) in enumerate(summary_rows):
        ctk.CTkLabel(sec_summary, text=rotulo, font=bold_font).grid(row=idx, column=0, sticky='w', pady=3)
        ctk.CTkLabel(sec_summary, textvariable=summary_vars[chave], font=body_font, anchor='w').grid(row=idx, column=1, sticky='w', pady=3)

    status_var = ctk.StringVar(value='')
    ctk.CTkLabel(outer, textvariable=status_var, font=body_font, anchor='w', justify='left', wraplength=520).pack(fill='x', pady=(12, 0))

    metodo_section = make_section(outer, 'DEFINIR ADUBAÇÃO', heading_font)
    metodo_section.grid_columnconfigure(0, weight=0)
    metodo_section.grid_columnconfigure(1, weight=1)
    metodo_section.grid_columnconfigure(2, weight=0)

    metodo_var = ctk.StringVar(value='Correção')
    ctk.CTkLabel(metodo_section, text='Método de adubação:', font=bold_font).grid(row=0, column=0, sticky='w', pady=3)
    metodo_box = ctk.CTkComboBox(metodo_section, values=['Correção', 'Manutenção', 'Reposição'], variable=metodo_var, state='readonly', width=160)
    metodo_box.grid(row=0, column=1, sticky='w', padx=(0, 8))

    correcao_var = ctk.StringVar(value='Correção total')
    correcao_label = ctk.CTkLabel(metodo_section, text='Tipo de correção:', font=bold_font)
    correcao_box = ctk.CTkComboBox(metodo_section, values=['Correção total', 'Duas safras'], variable=correcao_var, state='readonly', width=160)

    resultado_metodo = {
        'P': ctk.StringVar(value='-'),
        'K': ctk.StringVar(value='-'),
    }
    ctk.CTkLabel(metodo_section, text='P2O5 (kg/ha):', font=bold_font).grid(row=2, column=0, sticky='w', pady=3)
    ctk.CTkLabel(metodo_section, textvariable=resultado_metodo['P'], font=body_font, anchor='w').grid(row=2, column=1, sticky='w', pady=3, columnspan=2)
    ctk.CTkLabel(metodo_section, text='K2O (kg/ha):', font=bold_font).grid(row=3, column=0, sticky='w', pady=3)
    ctk.CTkLabel(metodo_section, textvariable=resultado_metodo['K'], font=body_font, anchor='w').grid(row=3, column=1, sticky='w', pady=3, columnspan=2)

    recomendacao_section = make_section(outer, 'RECOMENDAÇÕES TÉCNICAS', heading_font)
    recomendacao_var = ctk.StringVar(value='')
    ctk.CTkLabel(recomendacao_section, textvariable=recomendacao_var, font=body_font, anchor='w', justify='left', wraplength=520).pack(fill='x', pady=(0, 0))

    ctk.CTkButton(outer, text='DEFINIR ADUBAÇÃO', command=lambda: aplicar_metodo(ctx)).pack(pady=(12, 0))

    def atualizar_opcoes_correcao(*_):
        if normalize_key(metodo_var.get()) == 'correcao':
            correcao_label.grid(row=1, column=0, sticky='w', pady=3)
            correcao_box.grid(row=1, column=1, sticky='w', padx=(0, 8))
        else:
            correcao_label.grid_remove()
            correcao_box.grid_remove()

    metodo_box.configure(command=lambda _: (atualizar_opcoes_correcao(), aplicar_metodo(ctx)))
    correcao_box.configure(command=lambda _: aplicar_metodo(ctx))
    atualizar_opcoes_correcao()

    if getattr(ctx, 'logo_image', None) is not None:
        logo_label = ctk.CTkLabel(aba, image=ctx.logo_image, text='')
        logo_label.pack(anchor='se', padx=12, pady=12)
        logo_label.image = ctx.logo_image

    ctx.adubacao_controls = {
        'summary': summary_vars,
        'status': status_var,
        'metodo': metodo_var,
        'resultado_metodo': resultado_metodo,
        'recomendacao': recomendacao_var,
        'recomendacao_section': recomendacao_section,
        'ultimo_resultado': None,
        'correcao_var': correcao_var,
        'correcao_label': correcao_label,
        'correcao_box': correcao_box,
        'mostrar_correcao': atualizar_opcoes_correcao,
    }
    return ctx.adubacao_controls


def atualizar(ctx: AppContext):
    controles = getattr(ctx, 'adubacao_controls', None)
    if not controles:
        return

    summary_vars = controles.get('summary', {})
    status_var = controles.get('status')
    resultado_metodo = controles.get('resultado_metodo', {})
    recomendacao_var = controles.get('recomendacao')
    metodo_var = controles.get('metodo')
    correcao_var = controles.get('correcao_var')
    mostrar_correcao = controles.get('mostrar_correcao')

    controles['ultimo_resultado'] = None

    atualiza_fert = getattr(ctx, 'atualizar_fertilizacao', None)
    if callable(atualiza_fert):
        atualiza_fert()

    for var in summary_vars.values():
        var.set('-')
    for var in resultado_metodo.values():
        var.set('-')
    if recomendacao_var is not None:
        recomendacao_var.set('')

    if status_var is not None:
        status_var.set('')

    if metodo_var is not None and correcao_var is not None:
        if normalize_key(metodo_var.get()) != 'correcao':
            correcao_var.set('Correção total')
    if mostrar_correcao is not None:
        mostrar_correcao()

    diag = getattr(ctx, '_diag_cache', None)
    if not diag:
        return

    macros = diag.get('macronutrientes', {})
    p_info = macros.get('P') or {}
    k_info = macros.get('K') or {}
    p_class = p_info.get('classe')
    k_class = k_info.get('classe')

    if not p_class or not k_class:
        if status_var is not None:
            status_var.set('Não foi possível identificar as classes de P e K a partir da análise informada.')
        return

    entradas = ctx.get_entradas()
    produtividade = parse_float(entradas.get('Produtividade esperada')) or 0.0
    if produtividade <= 0:
        if status_var is not None:
            status_var.set('Informe uma produtividade esperada maior que zero para calcular as necessidades.')
        return

    argila = parse_float(entradas.get('Argila (%)'))
    ctc = parse_float(entradas.get('CTC (cmolc/dm3)'))
    teor_s = parse_float(entradas.get('S (mg/dm3)'))
    ph = parse_float(entradas.get('pH (Agua)'))

    cultivo_txt = entradas.get('Cultivo') or ''
    cultivo = 2 if '2' in str(cultivo_txt) else 1

    entrada = EntradaSoja(
        p_class=p_class,
        k_class=k_class,
        produtividade=produtividade,
        cultivo=cultivo,
        argila_pct=argila,
        ctc=ctc,
        teor_s_mg_dm3=teor_s,
        ph_agua=ph,
    )

    try:
        resultado = recomendar_adubacao_soja(entrada)
    except Exception as exc:
        for var in summary_vars.values():
            var.set('Erro')
        for var in resultado_metodo.values():
            var.set('Erro')
        if status_var is not None:
            status_var.set(f'Erro ao calcular adubação: {exc}')
        if recomendacao_var is not None:
            recomendacao_var.set('')
        return

    totais = resultado.totais
    summary_vars['P2O5'].set(f"{totais['P2O5_total']:.1f} kg/ha")
    summary_vars['K2O'].set(f"{totais['K2O_total']:.1f} kg/ha")
    summary_vars['S'].set('Dispensado' if totais['S_SO4'] == 0 else f"{totais['S_SO4']:.1f} kg/ha")
    summary_vars['Mo'].set('Dispensado' if totais['Mo_g_ha'] == 0 else f"{totais['Mo_g_ha']:.0f} g/ha")

    controles['ultimo_resultado'] = resultado
    aplicar_metodo(ctx)


def aplicar_metodo(ctx: AppContext):
    controles = getattr(ctx, 'adubacao_controls', None)
    if not controles:
        return

    metodo_var = controles.get('metodo')
    resultado_metodo = controles.get('resultado_metodo', {})
    recomendacao_var = controles.get('recomendacao')
    resultado = controles.get('ultimo_resultado')
    correcao_var = controles.get('correcao_var')

    if not metodo_var or not resultado_metodo:
        return

    for var in resultado_metodo.values():
        var.set('-')

    if recomendacao_var is not None:
        recomendacao_var.set('')

    if resultado is None:
        if recomendacao_var is not None:
            recomendacao_var.set('Calcule as necessidades primeiro.')
        atualiza_fert = getattr(ctx, 'atualizar_fertilizacao', None)
        if callable(atualiza_fert):
            atualiza_fert()
        return

    metodo_key = normalize_key(metodo_var.get() or '')

    mensagens: list[str]
    texto_p = '-'
    texto_k = '-'

    if metodo_key == 'manutencao':
        p_dose = resultado.manutencao['P2O5']
        k_dose = resultado.manutencao['K2O']
        texto_p = f"{p_dose:.1f} kg/ha"
        texto_k = f"{k_dose:.1f} kg/ha"
        mensagens = [
            'Considerar perdas de 20 a 30% em plantio direto e até 50% no sistema convencional.',
            'Utilizar em todos os níveis de fertilidade, exceto no "Muito alto", onde a aplicação pode variar de zero até a dose de manutenção.',
            'Ajustar doses +/-10 kg/ha conforme a fórmula comercial disponível.'
        ]
    elif metodo_key == 'reposicao':
        p_dose = resultado.reposicao['P2O5']
        k_dose = resultado.reposicao['K2O']
        texto_p = f"{p_dose:.1f} kg/ha"
        texto_k = f"{k_dose:.1f} kg/ha"
        mensagens = [
            'Após dois cultivos, reamostrar o solo para confirmar se os teores atingiram o nível "Alto" e ajustar novas aplicações.'
        ]
    else:
        total_p = resultado.totais['P2O5_total']
        total_k = resultado.totais['K2O_total']
        base_mensagens = [
            'Não ultrapassar 80 kg/ha de K2O na linha; aplicar o excedente a lanço ou cobertura.'
        ]
        escolha_correcao = normalize_key(correcao_var.get()) if correcao_var is not None else ''
        if escolha_correcao == 'duas safras':
            man_p = resultado.manutencao['P2O5']
            man_k = resultado.manutencao['K2O']
            corr_p = max(total_p - man_p, 0.0)
            corr_k = max(total_k - man_k, 0.0)
            dose1_p = corr_p * 0.75 + man_p
            dose2_p = corr_p * (1.0 / 3.0) + man_p
            dose1_k = corr_k * 0.75 + man_k
            dose2_k = corr_k * (1.0 / 3.0) + man_k
            texto_p = f"Safra 1: {dose1_p:.1f} kg/ha\nSafra 2: {dose2_p:.1f} kg/ha"
            texto_k = f"Safra 1: {dose1_k:.1f} kg/ha\nSafra 2: {dose2_k:.1f} kg/ha"
            mensagens = base_mensagens
        else:
            texto_p = f"{total_p:.1f} kg/ha"
            texto_k = f"{total_k:.1f} kg/ha"
            mensagens = base_mensagens + [
                'Evitar correção total de uma vez em solos arenosos devido ao risco de lixiviação e salinidade.',
                'Só recomenda-se a correção total seguida de incorporação do adubo na camada 0-20 cm do solo.'
            ]

    resultado_metodo['P'].set(texto_p)
    resultado_metodo['K'].set(texto_k)

    if recomendacao_var is not None:
        texto = '\n'.join(f'{msg.capitalize()}' for msg in mensagens)
        recomendacao_var.set(texto)

    atualiza_fert = getattr(ctx, 'atualizar_fertilizacao', None)
    if callable(atualiza_fert):
        atualiza_fert()


