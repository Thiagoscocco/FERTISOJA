from __future__ import annotations

import unicodedata
from typing import Dict, Optional

import customtkinter as ctk

from fertilizacao import (
    FOSFATADOS_CHOICES,
    POTASSICOS_CHOICES,
    FertilizacaoResultado,
    MOLIBDATO_PADRAO,
    calcular_formulado,
    calcular_individual_usuario,
    calcular_individual_software,
    obter_fosfatado_por_nome,
    obter_potassico_por_nome,
)
from .design_constants import *


def make_section(parent, title: str, font: ctk.CTkFont):
    wrapper = ctk.CTkFrame(parent, fg_color=(PANEL_LIGHT, PANEL_DARK))
    wrapper.pack(fill='x', pady=(PADY_SMALL, 0))
    header = ctk.CTkLabel(wrapper, text=title, font=font, anchor='w', 
                         text_color=(TEXT_PRIMARY, "#4a9eff"))
    header.pack(anchor='w', padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))
    body = ctk.CTkFrame(wrapper, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=(0, PADY_STANDARD))
    return wrapper, body


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ''
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower().strip()


def _parse_float(value: Optional[str]) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(',', '.')
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _format_valor(valor: float) -> str:
    if valor >= 100:
        return f"{valor:.0f}"
    if valor >= 10:
        return f"{valor:.1f}"
    if valor >= 1:
        return f"{valor:.2f}"
    return f"{valor:.3f}"


def _formatar_produtos(produtos):
    if not produtos:
        return 'Nenhum fertilizante necessário nas condições atuais.'
    linhas = []
    for nome, qtd in produtos:
        if nome == MOLIBDATO_PADRAO.nome:
            linhas.append(f"- {nome}: {_format_valor(qtd * 1000)} g/ha")
        else:
            linhas.append(f"- {nome}: {_format_valor(qtd)} kg/ha")
    return 'Produtos aplicados:\n' + '\n'.join(linhas)


def _formatar_alertas(alertas, faltantes):
    mensagens = list(alertas or [])
    for nutriente, valor in (faltantes or {}).items():
        mensagens.append(f"Faltante: {nutriente} ({_format_valor(valor)} kg/ha)")
    if not mensagens:
        return ''
    return 'Avisos:\n' + '\n'.join(f"- {mensagem}" for mensagem in mensagens)


def _obter_demanda(ctx) -> tuple[Optional[Dict[str, float]], Optional[str]]:
    controles_adub = getattr(ctx, 'adubacao_controls', None)
    if not controles_adub:
        return None, 'Calcule a recomendação de adubação antes de usar esta aba.'
    resultado = controles_adub.get('ultimo_resultado') if isinstance(controles_adub, dict) else None
    if resultado is None:
        return None, 'Calcule a recomendação de adubação antes de usar esta aba.'

    metodo_var = controles_adub.get('metodo') if isinstance(controles_adub, dict) else None
    correcao_var = controles_adub.get('correcao_var') if isinstance(controles_adub, dict) else None

    metodo_key = _normalize(metodo_var.get()) if metodo_var is not None else ''
    correcao_key = _normalize(correcao_var.get()) if correcao_var is not None else ''

    totais = resultado.totais
    manutencao = resultado.manutencao
    reposicao = resultado.reposicao

    total_p = float(totais.get('P2O5_total', 0.0))
    total_k = float(totais.get('K2O_total', 0.0))
    man_p = float(manutencao.get('P2O5', 0.0))
    man_k = float(manutencao.get('K2O', 0.0))
    rep_p = float(reposicao.get('P2O5', 0.0))
    rep_k = float(reposicao.get('K2O', 0.0))

    p_destino = total_p
    k_destino = total_k

    if metodo_key == 'manutencao':
        p_destino = man_p
        k_destino = man_k
    elif metodo_key == 'reposicao':
        p_destino = rep_p
        k_destino = rep_k
    else:
        desc_p = _normalize(getattr(resultado, 'descricao_p', ''))
        desc_k = _normalize(getattr(resultado, 'descricao_k', ''))
        if correcao_key == 'duas safras' or desc_p == 'correcao parcial':
            correcao_p = max(total_p - man_p, 0.0)
            p_destino = man_p + 0.75 * correcao_p
        if correcao_key == 'duas safras' or desc_k == 'correcao parcial':
            correcao_k = max(total_k - man_k, 0.0)
            k_destino = man_k + 0.75 * correcao_k

    s_destino = max(float(totais.get('S_SO4', 0.0)), 0.0)
    mo_g = max(float(totais.get('Mo_g_ha', 0.0)), 0.0)
    mo_destino = mo_g / 1000.0

    demanda = {
        'P2O5': max(p_destino, 0.0),
        'K2O': max(k_destino, 0.0),
        'S': s_destino,
        'Mo': mo_destino,
    }
    return demanda, None


def _gerar_resultado(ctx, demanda: Dict[str, float], controles: Dict) -> Optional[FertilizacaoResultado]:
    modo = _normalize(controles['modo_var'].get())
    if modo.startswith('fertilizantes form'):
        entradas = controles['formulado_inputs']
        n_txt = entradas['N'].get().strip()
        p_txt = entradas['P2O5'].get().strip()
        k_txt = entradas['K2O'].get().strip()
        grade = {
            'P2O5': _parse_float(p_txt),
            'K2O': _parse_float(k_txt),
        }
        nome_formulado = f"Formulado N {n_txt or '0'} - P {p_txt or '0'} - K {k_txt or '0'}"
        return calcular_formulado(demanda, grade, nome_formulado)

    submodo = _normalize(controles['submodo_var'].get())
    if submodo.startswith('escolha do usuário'):
        fosfatado_sel = controles['fosfatado_var'].get()
        potassico_sel = controles['potassico_var'].get()
        fosfatado = obter_fosfatado_por_nome(fosfatado_sel)
        potassico = obter_potassico_por_nome(potassico_sel)
        codigo_p = fosfatado.codigo if fosfatado else None
        codigo_k = potassico.codigo if potassico else None
        return calcular_individual_usuario(demanda, codigo_p, codigo_k)

    return calcular_individual_software(demanda)


def _executar_calculo(ctx, atualizar_status: bool = True) -> Optional[FertilizacaoResultado]:
    controles = getattr(ctx, 'fertilizacao_controls', None)
    if not isinstance(controles, dict):
        return None

    status_var = controles['status_var']
    resultado_var = controles['resultado_var']
    alerta_var = controles['alerta_var']
    atualiza_res = getattr(ctx, 'atualizar_resultados', None)

    demanda, mensagem = _obter_demanda(ctx)
    if mensagem:
        if atualizar_status:
            status_var.set(mensagem)
        resultado_var.set('')
        alerta_var.set('')
        controles['ultimo_resultado'] = None
        if callable(atualiza_res):
            atualiza_res()
        return None

    resultado = _gerar_resultado(ctx, demanda, controles)
    if resultado is None:
        if atualizar_status:
            status_var.set('Revise as opções e tente novamente.')
        resultado_var.set('')
        alerta_var.set('')
        controles['ultimo_resultado'] = None
        if callable(atualiza_res):
            atualiza_res()
        return None

    resultado_var.set(_formatar_produtos(resultado.produtos))
    alerta_var.set(_formatar_alertas(resultado.alertas, resultado.faltantes))
    controles['ultimo_resultado'] = resultado

    if atualizar_status:
        if resultado.faltantes:
            status_var.set('Existem nutrientes não atendidos; verifique os avisos.')
        else:
            status_var.set('')

    if callable(atualiza_res):
        atualiza_res()
    return resultado


def atualizar_fertilizacao(ctx):
    _executar_calculo(ctx, atualizar_status=False)


def add_tab(tabhost, ctx):
    heading_font = ctk.CTkFont(size=13, weight='bold')
    body_font = ctk.CTkFont(size=11)
    subheading_font = ctk.CTkFont(size=FONT_SIZE_BODY, weight='bold')
    card_style = {
        'fg_color': (PANEL_LIGHT, PANEL_DARK),
        'border_width': 1,
        'border_color': TEXT_PRIMARY,
        'corner_radius': 12,
    }

    logo_image = getattr(ctx, 'logo_image', None)

    aba = tabhost.add_tab('🌿 Escolha dos Fertilizantes')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)

    modo_wrapper, modo_body = make_section(outer, 'CONFIGURAÇÃO', heading_font)
    modo_body.grid_columnconfigure(1, weight=1)

    modo_var = ctk.StringVar(value='Fertilizantes formulados')
    ctk.CTkLabel(modo_body, text='Modo de cálculo:', font=body_font).grid(row=0, column=0, sticky='w', pady=4)
    modo_box = ctk.CTkComboBox(
        modo_body,
        values=['Fertilizantes formulados', 'Fertilizantes individuais'],
        variable=modo_var,
        state='readonly',
        width=220,
    )
    modo_box.grid(row=0, column=1, sticky='w', padx=(0, 12), pady=4)

    fertilizantes_wrapper, fertilizantes_body = make_section(outer, 'FERTILIZANTES', heading_font)

    formulado_frame = ctk.CTkFrame(fertilizantes_body, **card_style)
    formulado_frame.grid_columnconfigure(0, weight=0)
    formulado_frame.grid_columnconfigure(1, weight=1)
    formulado_frame.grid_columnconfigure(2, weight=0)
    formulado_frame.grid_columnconfigure(3, weight=1)
    formulado_frame.grid_columnconfigure(4, weight=0)
    formulado_frame.grid_columnconfigure(5, weight=1)
    ctk.CTkLabel(formulado_frame, text='Formulados N-P-K', font=subheading_font).grid(row=0, column=0, columnspan=6, sticky='w', pady=(PADY_SMALL, 6))

    ctk.CTkLabel(formulado_frame, text='N (%)', font=body_font).grid(row=1, column=0, sticky='w', pady=4, padx=(PADX_STANDARD, PADX_SMALL))
    entrada_n = ctk.CTkEntry(formulado_frame, width=80)
    entrada_n.grid(row=1, column=1, sticky='ew', pady=4, padx=(0, PADX_SMALL))

    ctk.CTkLabel(formulado_frame, text='P2O5 (%)', font=body_font).grid(row=1, column=2, sticky='w', pady=4, padx=(PADX_SMALL, PADX_SMALL))
    entrada_p = ctk.CTkEntry(formulado_frame, width=80)
    entrada_p.grid(row=1, column=3, sticky='ew', pady=4, padx=(0, PADX_SMALL))

    ctk.CTkLabel(formulado_frame, text='K2O (%)', font=body_font).grid(row=1, column=4, sticky='w', pady=4, padx=(PADX_SMALL, PADX_SMALL))
    entrada_k = ctk.CTkEntry(formulado_frame, width=80)
    entrada_k.grid(row=1, column=5, sticky='ew', pady=4, padx=(0, PADX_STANDARD))

    individual_frame = ctk.CTkFrame(fertilizantes_body, **card_style)
    individual_frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(individual_frame, text='Fertilizantes individuais', font=subheading_font).grid(row=0, column=0, columnspan=2, sticky='w', pady=(PADY_SMALL, 6), padx=PADX_STANDARD)

    submodo_var = ctk.StringVar(value='Escolha do usuário')
    ctk.CTkLabel(individual_frame, text='Como deseja compor?', font=body_font).grid(row=1, column=0, sticky='w', pady=4, padx=PADX_STANDARD)
    submodo_box = ctk.CTkComboBox(
        individual_frame,
        values=['Escolha do usuário', 'Escolha do software'],
        variable=submodo_var,
        state='readonly',
        width=220,
    )
    submodo_box.grid(row=1, column=1, sticky='w', pady=4, padx=(0, PADX_STANDARD))

    selecoes_frame = ctk.CTkFrame(individual_frame, fg_color='transparent')
    selecoes_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(8, PADY_SMALL), padx=PADX_STANDARD)
    selecoes_frame.grid_columnconfigure(0, weight=0)
    selecoes_frame.grid_columnconfigure(1, weight=1)
    selecoes_frame.grid_columnconfigure(2, weight=0)
    selecoes_frame.grid_columnconfigure(3, weight=1)

    fosfatado_var = ctk.StringVar(value='')
    ctk.CTkLabel(selecoes_frame, text='Fosfatado:', font=body_font).grid(row=0, column=0, sticky='w', pady=4, padx=(0, PADX_SMALL))
    fosfatado_box = ctk.CTkComboBox(
        selecoes_frame,
        values=FOSFATADOS_CHOICES,
        variable=fosfatado_var,
        state='readonly',
        width=210,
    )
    fosfatado_box.grid(row=0, column=1, sticky='ew', pady=4, padx=(0, PADX_STANDARD))
    fosfatado_box.set('')

    potassico_var = ctk.StringVar(value='')
    ctk.CTkLabel(selecoes_frame, text='Potássico:', font=body_font).grid(row=0, column=2, sticky='w', pady=4, padx=(0, PADX_SMALL))
    potassico_box = ctk.CTkComboBox(
        selecoes_frame,
        values=POTASSICOS_CHOICES,
        variable=potassico_var,
        state='readonly',
        width=210,
    )
    potassico_box.grid(row=0, column=3, sticky='ew', pady=4, padx=(0, 0))
    potassico_box.set('')

    resultado_wrapper, resultado_body = make_section(outer, 'RESULTADO', heading_font)
    resultado_body.grid_columnconfigure(0, weight=1)

    status_var = ctk.StringVar(value='Ajuste as opções para definir os fertilizantes.')
    resultado_var = ctk.StringVar(value='')
    alerta_var = ctk.StringVar(value='')

    ctk.CTkLabel(resultado_body, textvariable=status_var, font=body_font, anchor='w', justify='left').pack(fill='x', pady=(0, 6))
    ctk.CTkLabel(resultado_body, textvariable=resultado_var, font=body_font, anchor='w', justify='left').pack(fill='x', pady=(0, 6))
    ctk.CTkLabel(resultado_body, textvariable=alerta_var, font=ctk.CTkFont(size=10), text_color='#F4B942', anchor='w', justify='left', wraplength=520).pack(fill='x')

    calcular_btn = ctk.CTkButton(outer, text='Calcular fertilização', command=lambda: _executar_calculo(ctx))
    calcular_btn.pack(pady=(16, 0))

    controles = {
        'modo_var': modo_var,
        'submodo_var': submodo_var,
        'resultado_var': resultado_var,
        'alerta_var': alerta_var,
        'status_var': status_var,
        'formulado_inputs': {'N': entrada_n, 'P2O5': entrada_p, 'K2O': entrada_k},
        'fosfatado_var': fosfatado_var,
        'potassico_var': potassico_var,
        'formulado_frame': formulado_frame,
        'individual_frame': individual_frame,
        'selecoes_frame': selecoes_frame,
        'ultimo_resultado': None,
    }

    ctx.fertilizacao_controls = controles
    ctx.atualizar_fertilizacao = lambda: atualizar_fertilizacao(ctx)

    def recalcular_silencioso(*_):
        _executar_calculo(ctx, atualizar_status=False)

    for entrada in (entrada_n, entrada_p, entrada_k):
        entrada.bind('<FocusOut>', lambda *_: recalcular_silencioso())
        entrada.bind('<Return>', lambda *_: recalcular_silencioso())

    fosfatado_box.configure(command=lambda _: recalcular_silencioso())
    potassico_box.configure(command=lambda _: recalcular_silencioso())

    def atualizar_submodo(*_):
        sub_norm = _normalize(submodo_var.get())
        if sub_norm.startswith('escolha do usuario'):
            selecoes_frame.grid()
        else:
            selecoes_frame.grid_remove()
        recalcular_silencioso()

    def atualizar_formulario(*_):
        modo_norm = _normalize(modo_var.get())
        if modo_norm.startswith('fertilizantes form'):
            individual_frame.pack_forget()
            if formulado_frame.winfo_manager() == '':
                formulado_frame.pack(fill='x', padx=PADX_SMALL, pady=(0, PADY_SMALL))
        else:
            formulado_frame.pack_forget()
            if individual_frame.winfo_manager() == '':
                individual_frame.pack(fill='x', padx=PADX_SMALL, pady=(0, PADY_SMALL))
        atualizar_submodo()
        recalcular_silencioso()

    modo_box.configure(command=atualizar_formulario)
    submodo_box.configure(command=atualizar_submodo)

    formulado_frame.pack(fill='x', padx=PADX_SMALL, pady=(0, PADY_SMALL))
    atualizar_submodo()
    atualizar_fertilizacao(ctx)

    if logo_image is not None:
        logo_label = ctk.CTkLabel(aba, image=logo_image, text='')
        logo_label.pack(anchor='se', padx=12, pady=12)
        logo_label.image = logo_image


__all__ = ['add_tab', 'atualizar_fertilizacao']
