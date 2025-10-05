# -*- coding: utf-8 -*-
import unicodedata
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from core.fonts import aplicar_fonte_global
from core.context import AppContext, TabHost, carregar_abas_externas
from core import calculo, diagnostico


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


def _parse_float(value):
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
    if not text:
        return ''
    normalized = unicodedata.normalize('NFKD', text)
    return normalized.encode('ascii', 'ignore').decode().lower()


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


def montar_aba_condicoes(tabhost, heading_font, labels_classificacao):
    body_font = ctk.CTkFont(size=11)
    bold_font = ctk.CTkFont(size=11, weight='bold')

    aba = tabhost.add_tab('Condicoes do Solo')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=16, pady=16)
    outer.grid_columnconfigure(0, weight=1)

    sec_prop = make_section(outer, 'PROPRIEDADES GERAIS DO SOLO', heading_font)
    for nome in ['Classe do teor de Argila', 'CTC', 'M.O.']:
        add_value_row(sec_prop, nome, labels_classificacao)

    sec_macro = make_section(outer, 'MACRONUTRIENTES', heading_font)
    for nome in ['Fosforo (P)', 'Potassio (K)', 'Calcio (Ca)', 'Magnesio (Mg)', 'Enxofre (S)']:
        add_value_row(sec_macro, nome, labels_classificacao)

    sec_micro = make_section(outer, 'MICRONUTRIENTES', heading_font)
    for nome in ['Zinco (Zn)', 'Cobre (Cu)', 'Boro (B)', 'Manganes (Mn)']:
        add_value_row(sec_micro, nome, labels_classificacao)

    resumo_section = make_section(outer, 'RESUMO DO DIAGNOSTICO', heading_font)
    resumo_section.grid_columnconfigure(0, weight=0)
    resumo_section.grid_columnconfigure(1, weight=1)
    summary_vars = {
        'textura': ctk.StringVar(value='Classe de argila: - | CTC: -'),
        'mo': ctk.StringVar(value='-'),
        'p': ctk.StringVar(value='-'),
        'k': ctk.StringVar(value='-'),
        'tecnica': ctk.StringVar(value='Informe os dados na aba principal e calcule para obter o diagnostico.'),
    }
    resumo_rows = [
        ('Textura e CTC:', 'textura'),
        ('Materia organica:', 'mo'),
        ('Fosforo (P):', 'p'),
        ('Potassio (K):', 'k'),
        ('Recomendacao:', 'tecnica'),
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


def atualizar_condicoes(ctx):
    controles = getattr(ctx, 'condicoes_controls', None)
    if not controles:
        return

    entradas = ctx.get_entradas()
    dados_diag = _coletar_diagnostico_entradas(entradas)
    diag = diagnostico.diagnosticar_soja(dados_diag)

    summary = controles['summary']
    props = diag['propriedades']
    macros = diag['macronutrientes']
    alertas = diag['alertas']
    observacoes = diag['observacoes']

    classe_argila = props.get('classe_argila_num')
    classe_ctc = props.get('classe_ctc') or '-'
    classe_desc = {1: 'Muito argilosa', 2: 'Argilosa', 3: 'Media', 4: 'Arenosa'}
    if classe_argila:
        textura_txt = f"Classe de argila: {classe_argila} ({classe_desc.get(classe_argila, '-')}) | CTC: {classe_ctc}"
    else:
        textura_txt = f"Classe de argila: - | CTC: {classe_ctc}"
    summary['textura'].set(textura_txt)

    mo_classe = props.get('classe_mo')
    mo_valor = dados_diag.get('MO_percent')
    if mo_classe and mo_valor is not None:
        summary['mo'].set(f"{mo_classe} ({mo_valor:.1f}%)")
    elif mo_classe:
        summary['mo'].set(mo_classe)
    else:
        summary['mo'].set('-')

    p_info = macros['P']
    k_info = macros['K']
    prob_p = p_info.get('prob_resposta')
    prob_k = k_info.get('prob_resposta')
    summary['p'].set(f"Resposta {prob_p}" if prob_p else '-')
    summary['k'].set(f"Resposta {prob_k}" if prob_k else '-')

    if p_info.get('classe') in ('Muito Baixo', 'Baixo') or k_info.get('classe') in ('Muito Baixo', 'Baixo'):
        summary['tecnica'].set('Repetir analise na proxima safra.\nAlta chance de resposta a P/K.')
    else:
        summary['tecnica'].set('Repetir analise na proxima safra.')

    if alertas:
        controles['alertas_label'].configure(text='\n'.join(f'- {msg}' for msg in alertas))
    else:
        controles['alertas_label'].configure(text='Nenhum alerta especifico identificado.')

    observacoes_texto = '\n'.join(f'- {valor}' for valor in observacoes.values())
    controles['observacoes_label'].configure(text=observacoes_texto)


def main():
    ctk.set_appearance_mode('dark')
    janela = ctk.CTk()
    janela.title('Fertisoja')
    largura = 840
    altura = 650
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    janela.resizable(False, False)

    _, heading_font = aplicar_fonte_global(janela)

    cultivo_var = ctk.StringVar(value='1o Cultivo')
    calculo.ligar_cultivo_var(cultivo_var)

    campos = calculo.campos
    labels_classificacao = calculo.labels_classificacao
    labels_resultado = calculo.labels_resultado

    tabview = ctk.CTkTabview(janela)
    tabview.pack(fill='both', expand=True, padx=16, pady=16)
    tabhost = TabHost(tabview)

    aba_entrada = tabhost.add_tab('Dados da analise de Solo')
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

    sec1 = make_section(col_esq, 'INFORMACOES DA PRODUCAO', heading_font)
    sec1.grid_columnconfigure(1, weight=1)
    sec1.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(sec1, text='Produtividade esperada (T/Ha)').grid(row=0, column=0, sticky='w', pady=4)
    entrada_prod = ctk.CTkEntry(sec1, width=120)
    entrada_prod.grid(row=0, column=1, sticky='w', padx=6)
    campos['Produtividade esperada'] = entrada_prod
    entrada_prod.insert(0, TEST_DEFAULTS.get('Produtividade esperada', ''))

    ctk.CTkLabel(sec1, text='Area (Ha)').grid(row=0, column=2, sticky='w', pady=4)
    entrada_area = ctk.CTkEntry(sec1, width=100)
    entrada_area.grid(row=0, column=3, sticky='w', padx=6)
    campos['Area (Ha)'] = entrada_area
    entrada_area.insert(0, TEST_DEFAULTS.get('Area (Ha)', ''))

    ctk.CTkLabel(sec1, text='Cultivo').grid(row=1, column=0, sticky='w', pady=(6, 0))
    radio_frame = ctk.CTkFrame(sec1, fg_color='transparent')
    radio_frame.grid(row=1, column=1, columnspan=3, sticky='w', pady=(6, 0))
    ctk.CTkRadioButton(radio_frame, text='1o Cultivo', variable=cultivo_var, value='1o Cultivo').pack(side='left', padx=(0, 16))
    ctk.CTkRadioButton(radio_frame, text='2o Cultivo', variable=cultivo_var, value='2o Cultivo').pack(side='left')

    sec2 = make_section(col_esq, 'CONDICOES DO SOLO', heading_font)
    sec2.grid_columnconfigure(1, weight=1)
    dados_sec2 = [
        ('Indice SMP', 'Indice SMP'),
        ('Argila (%)', 'Argila (%)'),
        ('CTC (cmolc/dm3)', 'CTC (cmolc/dm3)'),
        ('M.O. (%)', 'M.O. (%)'),
        ('pH (agua)', 'pH (Agua)'),
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
        ('P (mg/dm3)', 'P (mg/dm3)'),
        ('K (mg/dm3)', 'K (mg/dm3)'),
        ('S (mg/dm3)', 'S (mg/dm3)'),
        ('Ca (cmolc/dm3)', 'Ca (cmolc/dm3)'),
        ('Mg (cmolc/dm3)', 'Mg (cmolc/dm3)'),
        ('Zn (mg/dm3)', 'Zn (mg/dm3)'),
        ('Cu (mg/dm3)', 'Cu (mg/dm3)'),
        ('B (mg/dm3)', 'B (mg/dm3)'),
        ('Mn (mg/dm3)', 'Mn (mg/dm3)'),
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
        resultado = calculo.calcular()
        if resultado:
            status_var.set('Calculo atualizado com sucesso.')
            atualizar_condicoes(ctx)
            janela.after(4000, lambda: status_var.set(''))

    rodape = ctk.CTkFrame(aba_entrada, fg_color='transparent')
    rodape.grid(row=1, column=0, sticky='ew', padx=16, pady=(8, 16))
    rodape.grid_columnconfigure(0, weight=0)
    rodape.grid_columnconfigure(1, weight=1)
    ctk.CTkButton(rodape, text='CALCULAR', command=executar_calculo_principal).grid(row=0, column=0, pady=0)
    ctk.CTkLabel(rodape, textvariable=status_var, text_color='#57C17A').grid(row=0, column=1, sticky='w', padx=(12, 0))

    logo_path = Path(__file__).resolve().parent / 'assets' / 'logo.png'
    try:
        imagem = Image.open(logo_path)
        max_w = 220
        if imagem.width > max_w:
            ratio = max_w / imagem.width
            new_size = (int(imagem.width * ratio), int(imagem.height * ratio))
            imagem = imagem.resize(new_size, Image.LANCZOS)
        logo = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(imagem.width, imagem.height))
        ctk.CTkLabel(col_dir, image=logo, text='').pack(anchor='ne')
    except Exception:
        ctk.CTkLabel(col_dir, text='(imagem nao carregada)').pack(anchor='ne')

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

    atualizar_condicoes(ctx)

    janela.mainloop()


if __name__ == '__main__':
    main()
