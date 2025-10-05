# -*- coding: utf-8 -*-
"""Interface principal do Fertisoja."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from core.fonts import aplicar_fonte_global
from core.context import AppContext, TabHost, carregar_abas_externas
from core import calculo, diagnostico
from core.adubacao_dados import EntradaSoja, recomendar_adubacao_soja


TEST_DEFAULTS = {
    'Produtividade esperada': '3.6',
    'Area (Ha)': '15',
    'Indice SMP': '6.7',
    'Argila (%)': '13',
    'CTC (cmolc/dm3)': '2.5',
    'M.O. (%)': '0.6',
    'pH (Agua)': '4.7',
    'P (mg/dm3)': '2.6',
    'K (mg/dm3)': '21',
    'S (mg/dm3)': '2.8',
    'Ca (cmolc/dm3)': '0.3',
    'Mg (cmolc/dm3)': '0.2',
    'Zn (mg/dm3)': '0.3',
    'Cu (mg/dm3)': '0.5',
    'B (mg/dm3)': '0.1',
    'Mn (mg/dm3)': '4',
}
# TODO: remover TEST_DEFAULTS quando os testes terminarem.


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


def _parse_float(value) -> float | None:
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


def _normalize_key(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text or '')
    return normalized.encode('ascii', 'ignore').decode('ascii').lower()


def _lookup_value(entradas: dict, keyword: str):
    alvo = keyword.lower()
    for chave, valor in entradas.items():
        if _normalize_key(chave).startswith(alvo):
            return valor
    return None


def _coletar_diagnostico_entradas(entradas: dict) -> dict:
    return {
        'pH_H2O': _parse_float(_lookup_value(entradas, 'ph (')),
        'argila_percent': _parse_float(_lookup_value(entradas, 'argila')),
        'CTC_pH7': _parse_float(_lookup_value(entradas, 'ctc')),
        'MO_percent': _parse_float(_lookup_value(entradas, 'm.o')),
        'P_mg_dm3': _parse_float(_lookup_value(entradas, 'p (mg')),
        'K_mg_dm3': _parse_float(_lookup_value(entradas, 'k (mg')),
        'Ca_cmolc_dm3': _parse_float(_lookup_value(entradas, 'ca (cmol')),
        'Mg_cmolc_dm3': _parse_float(_lookup_value(entradas, 'mg (cmol')),
        'S_mg_dm3': _parse_float(_lookup_value(entradas, 's (mg')),
        'Cu_mg_dm3': _parse_float(_lookup_value(entradas, 'cu (mg')),
        'Zn_mg_dm3': _parse_float(_lookup_value(entradas, 'zn (mg')),
        'B_mg_dm3': _parse_float(_lookup_value(entradas, 'b (mg')),
        'Mn_mg_dm3': _parse_float(_lookup_value(entradas, 'mn (mg')),
    }


def montar_aba_condicoes(tabhost: TabHost, heading_font, labels_classificacao):
    body_font = ctk.CTkFont(size=11)
    bold_font = ctk.CTkFont(size=11, weight='bold')

    aba = tabhost.add_tab('Condições do Solo')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=16, pady=16)
    outer.grid_columnconfigure(0, weight=1)

    sec_prop = make_section(outer, 'PROPRIEDADES GERAIS DO SOLO', heading_font)
    for nome in ['Classe do teor de Argila', 'CTC', 'M.O.']:
        add_value_row(sec_prop, nome, labels_classificacao)

    sec_macro = make_section(outer, 'MACRONUTRIENTES', heading_font)
    for nome in ['Fósforo (P)', 'Potássio (K)', 'Cálcio (Ca)', 'Magnésio (Mg)', 'Enxofre (S)']:
        add_value_row(sec_macro, nome, labels_classificacao)

    sec_micro = make_section(outer, 'MICRONUTRIENTES', heading_font)
    for nome in ['Zinco (Zn)', 'Cobre (Cu)', 'Boro (B)', 'Manganês (Mn)']:
        add_value_row(sec_micro, nome, labels_classificacao)

    resumo_section = make_section(outer, 'RESUMO DO DIAGNÓSTICO', heading_font)
    resumo_section.grid_columnconfigure(0, weight=0)
    resumo_section.grid_columnconfigure(1, weight=1)
    summary_vars = {
        'textura': ctk.StringVar(value='Classe de argila: - | CTC: -'),
        'mo': ctk.StringVar(value='Matéria orgânica: -'),
        'p': ctk.StringVar(value='Resposta ao P: aguardando dados'),
        'k': ctk.StringVar(value='Resposta ao K: aguardando dados'),
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
    alertas_label = ctk.CTkLabel(alertas_section, text='Preencha os dados para gerar alertas.', font=body_font, anchor='w', justify='left', wraplength=520)
    alertas_label.pack(fill='x')

    notas_section = make_section(outer, 'NOTAS', heading_font)
    observacoes_label = ctk.CTkLabel(notas_section, text='', font=body_font, anchor='w', justify='left', wraplength=520)
    observacoes_label.pack(fill='x')

    return {
        'summary': summary_vars,
        'alertas_label': alertas_label,
        'observacoes_label': observacoes_label,
    }


def atualizar_condicoes(ctx: AppContext):
    controles = getattr(ctx, 'condicoes_controls', None)
    if not controles:
        return

    entradas = ctx.get_entradas()
    dados_diag = _coletar_diagnostico_entradas(entradas)
    diag = diagnostico.diagnosticar_soja(dados_diag)
    ctx._diag_cache = diag  # reutilizado pela aba de adubação

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
    summary['p'].set(f"Resposta ao P: {p_prob}" if p_prob else 'Resposta ao P: -')

    k_prob = macros['K'].get('prob_resposta')
    summary['k'].set(f"Resposta ao K: {k_prob}" if k_prob else 'Resposta ao K: -')

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


def montar_aba_adubacao(tabhost: TabHost, heading_font, ctx: AppContext):
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

    status_var = ctk.StringVar(value='Informe os dados da análise de solo e calcule para gerar as necessidades.')
    ctk.CTkLabel(outer, textvariable=status_var, font=body_font, anchor='w', justify='left', wraplength=520).pack(fill='x', pady=(12, 0))

    metodo_section = make_section(outer, 'DEFINIR ADUBAÇÃO', heading_font)
    metodo_section.grid_columnconfigure(1, weight=1)
    metodo_section.grid_columnconfigure(2, weight=0)

    metodo_var = ctk.StringVar(value='Correção')
    ctk.CTkLabel(metodo_section, text='Método de adubação:', font=bold_font).grid(row=0, column=0, sticky='w', pady=3)
    metodo_box = ctk.CTkComboBox(metodo_section, values=['Correção', 'Manutenção', 'Reposição'], variable=metodo_var, state='readonly', width=160)
    metodo_box.grid(row=0, column=1, sticky='w', padx=(0, 8))

    definir_btn = ctk.CTkButton(metodo_section, text='Definir adubação', width=140, command=lambda: aplicar_metodo_adubacao(ctx))
    definir_btn.grid(row=0, column=2, sticky='w')

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

    recomendacao_var = ctk.StringVar(value='Recomendações técnicas: -')
    ctk.CTkLabel(metodo_section, textvariable=recomendacao_var, font=body_font, anchor='w', justify='left', wraplength=520).grid(row=4, column=0, columnspan=3, sticky='w', pady=(8, 0))

    def atualizar_opcoes_correcao(*_):
        if _normalize_key(metodo_var.get()) == 'correcao':
            correcao_label.grid(row=1, column=0, sticky='w', pady=3)
            correcao_box.grid(row=1, column=1, sticky='w', padx=(0, 8))
        else:
            correcao_label.grid_remove()
            correcao_box.grid_remove()

    metodo_box.configure(command=lambda _: (atualizar_opcoes_correcao(), aplicar_metodo_adubacao(ctx)))
    correcao_box.configure(command=lambda _: aplicar_metodo_adubacao(ctx))
    atualizar_opcoes_correcao()

    return {
        'summary': summary_vars,
        'status': status_var,
        'metodo': metodo_var,
        'resultado_metodo': resultado_metodo,
        'recomendacao': recomendacao_var,
        'definir_button': definir_btn,
        'ultimo_resultado': None,
        'correcao_var': correcao_var,
        'correcao_label': correcao_label,
        'correcao_box': correcao_box,
        'mostrar_correcao': atualizar_opcoes_correcao,
    }


def atualizar_adubacao(ctx: AppContext):
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

    for var in summary_vars.values():
        var.set('-')
    for var in resultado_metodo.values():
        var.set('-')
    if recomendacao_var is not None:
        recomendacao_var.set('Recomendações técnicas: -')

    if status_var is not None:
        status_var.set('Informe os dados da análise de solo e calcule para gerar as necessidades.')

    if metodo_var is not None and correcao_var is not None:
        if _normalize_key(metodo_var.get()) != 'correcao':
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
    produtividade = _parse_float(entradas.get('Produtividade esperada')) or 0.0
    if produtividade <= 0:
        if status_var is not None:
            status_var.set('Informe uma produtividade esperada maior que zero para calcular as necessidades.')
        return

    argila = _parse_float(entradas.get('Argila (%)'))
    ctc = _parse_float(entradas.get('CTC (cmolc/dm3)'))
    teor_s = _parse_float(entradas.get('S (mg/dm3)'))
    ph = _parse_float(entradas.get('pH (Agua)'))

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
            recomendacao_var.set('Recomendações técnicas: -')
        return

    totais = resultado.totais
    summary_vars['P2O5'].set(f"{totais['P2O5_total']:.1f} kg/ha")
    summary_vars['K2O'].set(f"{totais['K2O_total']:.1f} kg/ha")
    summary_vars['S'].set('Dispensado' if totais['S_SO4'] == 0 else f"{totais['S_SO4']:.1f} kg/ha")
    summary_vars['Mo'].set('Dispensado' if totais['Mo_g_ha'] == 0 else f"{totais['Mo_g_ha']:.0f} g/ha")

    controles['ultimo_resultado'] = resultado

    if status_var is not None:
        status_var.set('Resultados atualizados. Defina a adubação conforme o método selecionado.')

    aplicar_metodo_adubacao(ctx)

def aplicar_metodo_adubacao(ctx: AppContext):
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
        recomendacao_var.set('Recomendações técnicas: -')

    if resultado is None:
        if recomendacao_var is not None:
            recomendacao_var.set('Recomendações técnicas: calcule as necessidades primeiro.')
        return

    metodo_key = _normalize_key(metodo_var.get() or '')

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
        escolha_correcao = _normalize_key(correcao_var.get()) if correcao_var is not None else ''
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
        texto = 'Recomendações técnicas:\n' + '\n'.join(f'- {msg}' for msg in mensagens)
        recomendacao_var.set(texto)


def main():
    ctk.set_appearance_mode('dark')
    janela = ctk.CTk()
    janela.title('Fertisoja')
    largura, altura = 840, 650
    pos_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    pos_y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    janela.resizable(False, False)

    _, heading_font = aplicar_fonte_global(janela)

    cultivo_var = ctk.StringVar(value='1º Cultivo')
    calculo.ligar_cultivo_var(cultivo_var)

    campos = calculo.campos
    labels_classificacao = calculo.labels_classificacao
    labels_resultado = calculo.labels_resultado

    tabview = ctk.CTkTabview(janela)
    tabview.pack(fill='both', expand=True, padx=16, pady=16)
    tabhost = TabHost(tabview)

    aba_entrada = tabhost.add_tab('Dados da análise de Solo')
    aba_entrada.grid_columnconfigure(0, weight=1)
    aba_entrada.grid_rowconfigure(0, weight=1)
    aba_entrada.grid_rowconfigure(1, weight=0)

    conteudo = ctk.CTkScrollableFrame(aba_entrada, fg_color='transparent')
    conteudo.grid(row=0, column=0, sticky='nsew')
    conteudo.grid_columnconfigure(0, weight=1)
    conteudo.grid_columnconfigure(1, weight=0)

    col_esq = ctk.CTkFrame(conteudo, fg_color='transparent')
    col_esq.grid(row=0, column=0, sticky='nwe')

    col_dir = ctk.CTkFrame(conteudo, fg_color='transparent')
    col_dir.grid(row=0, column=1, sticky='ne', padx=(20, 0))

    sec1 = make_section(col_esq, 'INFORMAÇÕES DA PRODUÇÃO', heading_font)
    sec1.grid_columnconfigure(1, weight=1)
    sec1.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(sec1, text='Produtividade esperada (t/ha)').grid(row=0, column=0, sticky='w', pady=4)
    entrada_prod = ctk.CTkEntry(sec1, width=120)
    entrada_prod.grid(row=0, column=1, sticky='w', padx=6)
    campos['Produtividade esperada'] = entrada_prod
    entrada_prod.insert(0, TEST_DEFAULTS.get('Produtividade esperada', ''))

    ctk.CTkLabel(sec1, text='Área (ha)').grid(row=0, column=2, sticky='w', pady=4)
    entrada_area = ctk.CTkEntry(sec1, width=100)
    entrada_area.grid(row=0, column=3, sticky='w', padx=6)
    campos['Area (Ha)'] = entrada_area
    entrada_area.insert(0, TEST_DEFAULTS.get('Area (Ha)', ''))

    ctk.CTkLabel(sec1, text='Cultivo').grid(row=1, column=0, sticky='w', pady=(6, 0))
    radio_frame = ctk.CTkFrame(sec1, fg_color='transparent')
    radio_frame.grid(row=1, column=1, columnspan=3, sticky='w', pady=(6, 0))
    ctk.CTkRadioButton(radio_frame, text='1º Cultivo', variable=cultivo_var, value='1º Cultivo').pack(side='left', padx=(0, 16))
    ctk.CTkRadioButton(radio_frame, text='2º Cultivo', variable=cultivo_var, value='2º Cultivo').pack(side='left')

    sec2 = make_section(col_esq, 'CONDIÇÕES DO SOLO', heading_font)
    sec2.grid_columnconfigure(1, weight=1)
    dados_sec2 = [
        ('Índice SMP', 'Indice SMP'),
        ('Argila (%)', 'Argila (%)'),
        ('CTC (cmolc/dm3)', 'CTC (cmolc/dm3)'),
        ('M.O. (%)', 'M.O. (%)'),
        ('pH (água)', 'pH (Agua)'),
    ]
    for idx, (rotulo, chave) in enumerate(dados_sec2):
        ctk.CTkLabel(sec2, text=rotulo).grid(row=idx, column=0, sticky='w', pady=4)
        entrada = ctk.CTkEntry(sec2, width=120)
        entrada.grid(row=idx, column=1, sticky='w', padx=6)
        campos[chave] = entrada
        entrada.insert(0, TEST_DEFAULTS.get(chave, ''))

    sec3 = make_section(col_esq, 'TEOR DE NUTRIENTES', heading_font)
    sec3.grid_columnconfigure(0, weight=1)
    sec3.grid_columnconfigure(1, weight=1)
    dados_sec3 = [
        ('P (mg/dm³)', 'P (mg/dm3)'),
        ('K (mg/dm³)', 'K (mg/dm3)'),
        ('S (mg/dm³)', 'S (mg/dm3)'),
        ('Ca (cmolc/dm³)', 'Ca (cmolc/dm3)'),
        ('Mg (cmolc/dm³)', 'Mg (cmolc/dm3)'),
        ('Zn (mg/dm³)', 'Zn (mg/dm3)'),
        ('Cu (mg/dm³)', 'Cu (mg/dm3)'),
        ('B (mg/dm³)', 'B (mg/dm3)'),
        ('Mn (mg/dm³)', 'Mn (mg/dm3)'),
    ]
    for idx, (rotulo, chave) in enumerate(dados_sec3):
        ctk.CTkLabel(sec3, text=rotulo).grid(row=idx, column=0, sticky='w', pady=3)
        entrada = ctk.CTkEntry(sec3, width=120)
        entrada.grid(row=idx, column=1, sticky='w', padx=6)
        campos[chave] = entrada
        entrada.insert(0, TEST_DEFAULTS.get(chave, ''))

    status_var = ctk.StringVar(value='')

    def executar_calculo_principal():
        status_var.set('')
        if calculo.calcular():
            status_var.set('Cálculo atualizado com sucesso.')
            atualizar_condicoes(ctx)
            atualizar_adubacao(ctx)
            janela.after(4000, lambda: status_var.set(''))

    rodape = ctk.CTkFrame(aba_entrada, fg_color='transparent')
    rodape.grid(row=1, column=0, sticky='ew', padx=16, pady=(8, 16))
    rodape.grid_columnconfigure(0, weight=0)
    rodape.grid_columnconfigure(1, weight=1)
    ctk.CTkButton(rodape, text='Calcular', command=executar_calculo_principal).grid(row=0, column=0, pady=0)
    ctk.CTkLabel(rodape, textvariable=status_var, text_color='#57C17A').grid(row=0, column=1, sticky='w', padx=(12, 0))

    logo_path = Path(__file__).resolve().parent / 'assets' / 'logo.png'
    try:
        imagem = Image.open(logo_path)
        max_w = 220
        if imagem.width > max_w:
            ratio = max_w / imagem.width
            imagem = imagem.resize((int(imagem.width * ratio), int(imagem.height * ratio)), Image.LANCZOS)
        logo = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(imagem.width, imagem.height))
        ctk.CTkLabel(col_dir, image=logo, text='').pack(anchor='ne')
    except Exception:
        ctk.CTkLabel(col_dir, text='(imagem não carregada)').pack(anchor='ne')

    ctx = AppContext(
        janela=janela,
        abas=tabhost,
        campos=campos,
        labels_classificacao=labels_classificacao,
        labels_resultado=labels_resultado,
        cultivo_var=cultivo_var,
        calcular=calculo.calcular,
    )

    ctx.condicoes_controls = montar_aba_condicoes(tabhost, heading_font, labels_classificacao)

    carregar_abas_externas(tabhost, ctx)

    ctx.adubacao_controls = montar_aba_adubacao(tabhost, heading_font, ctx)
    atualizar_condicoes(ctx)
    atualizar_adubacao(ctx)

    janela.mainloop()


if __name__ == '__main__':
    main()
