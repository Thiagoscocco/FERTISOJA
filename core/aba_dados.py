from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .fonts import aplicar_fonte_global
from .context import AppContext, TabHost
from . import calculo
from .ui import make_section
from . import aba_condicoes, aba_adubacao


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


def add_tab(tabhost: TabHost, ctx: AppContext):
    janela = ctx.janela
    _, heading_font = aplicar_fonte_global(janela)
    ctx.heading_font = heading_font

    cultivo_var = ctk.StringVar(value='1º Cultivo')
    calculo.ligar_cultivo_var(cultivo_var)
    ctx.cultivo_var = cultivo_var

    campos = calculo.campos
    labels_classificacao = calculo.labels_classificacao
    labels_resultado = calculo.labels_resultado
    ctx.labels_classificacao = labels_classificacao
    ctx.labels_resultado = labels_resultado
    ctx.campos = campos
    ctx.calcular = calculo.calcular

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
    sec2.grid_columnconfigure(0, weight=0)
    sec2.grid_columnconfigure(1, weight=0)
    sec2.grid_columnconfigure(2, weight=1)
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
        entrada.grid(row=idx, column=1, sticky='w', padx=2)
        campos[chave] = entrada
        entrada.insert(0, TEST_DEFAULTS.get(chave, ''))

    sec3 = make_section(col_esq, 'TEOR DE NUTRIENTES', heading_font)
    sec3.grid_columnconfigure(0, weight=0)
    sec3.grid_columnconfigure(1, weight=0)
    sec3.grid_columnconfigure(2, weight=1)
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
        entrada.grid(row=idx, column=1, sticky='w', padx=2)
        campos[chave] = entrada
        entrada.insert(0, TEST_DEFAULTS.get(chave, ''))

    status_var = ctk.StringVar(value='')

    def executar_calculo_principal():
        status_var.set('')
        if calculo.calcular():
            status_var.set('Cálculo atualizado com sucesso.')
            aba_condicoes.atualizar(ctx)
            aba_adubacao.atualizar(ctx)
            atualiza_fert = getattr(ctx, 'atualizar_fertilizacao', None)
            if callable(atualiza_fert):
                atualiza_fert()
            janela.after(4000, lambda: status_var.set(''))

    rodape = ctk.CTkFrame(aba_entrada, fg_color='transparent')
    rodape.grid(row=1, column=0, sticky='ew', padx=16, pady=(8, 16))
    rodape.grid_columnconfigure(0, weight=1)
    ctk.CTkButton(rodape, text='CALCULAR', command=executar_calculo_principal).grid(row=0, column=0, pady=(0, 4), padx=0)
    ctk.CTkLabel(rodape, textvariable=status_var, text_color='#57C17A', anchor='center').grid(row=1, column=0, sticky='n', padx=0)

    logo_image = None
    logo_path = Path(__file__).resolve().parent.parent / 'assets' / 'logo.png'
    try:
        imagem = Image.open(logo_path)
        max_w = 120
        if imagem.width > max_w:
            ratio = max_w / imagem.width
            imagem = imagem.resize((int(imagem.width * ratio), int(imagem.height * ratio)), Image.LANCZOS)
        logo_image = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(imagem.width, imagem.height))
        logo_label = ctk.CTkLabel(col_dir, image=logo_image, text='')
        logo_label.pack(anchor='ne')
        logo_label.image = logo_image
    except Exception:
        ctk.CTkLabel(col_dir, text='(imagem não carregada)').pack(anchor='ne')

    ctx.logo_image = logo_image

    return {
        'status': status_var,
        'logo_image': logo_image,
    }


