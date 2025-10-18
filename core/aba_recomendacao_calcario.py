# -*- coding: utf-8 -*-
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

from core.calagem_dados import (
    V_TARGETS,
    adjust_for_prnt,
    cap_surface_application,
    lime_dose_from_SMP,
    lime_dose_from_V,
    lime_dose_from_polynomial,
)
from .design_constants import *
from .ui import make_section as build_section, place_logo_footer

PH_THRESHOLD_NEED = 5.5
PH_SEVERE_PD = 5.2
ALPCT_LIMIT_NO_LIME = 10.0
ALPCT_RESTR_THRESHOLD = 30.0
MG_LOW_THRESHOLD = 1.0


def _f(value, default=None):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '.')
    if text == '':
        return default
    try:
        return float(text)
    except Exception:
        return default


def make_section(parent, title, font):
    return build_section(parent, title, font, wrap=520)


def _registrar_calagem(ctx, dose_t_ha=0.0, area=0.0, modo='', epoca='', tipo='', tecnica='', prnt=None):
    area = area or 0.0
    dose_t_ha = max(dose_t_ha or 0.0, 0.0)
    kg_ha = dose_t_ha * 1000.0
    kg_total = kg_ha * max(area, 0.0)
    ctx.calagem_resultado = {
        'dose_t_ha': dose_t_ha,
        'kg_ha': kg_ha,
        'kg_total': kg_total,
        'modo': modo or '',
        'epoca': epoca or '',
        'tipo': tipo or '',
        'tecnica': tecnica or '',
        'prnt': prnt if prnt is None else float(prnt),
    }


def add_tab(tabhost, ctx):
    heading_font = ctk.CTkFont(size=13, weight='bold')
    body_font = ctk.CTkFont(size=11)

    logo_image = getattr(ctx, 'logo_image', None)

    aba = tabhost.add_tab('🪨 Recomendação de Calcário')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    outer.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)
    outer.grid_columnconfigure(0, weight=1)

    sec_inputs = make_section(outer, 'Parâmetros complementares', heading_font)
    for col in range(4):
        sec_inputs.grid_columnconfigure(col, weight=1 if col % 2 == 1 else 0)

    ctk.CTkLabel(sec_inputs, text='Sistema de manejo:', font=body_font).grid(row=0, column=0, sticky='w', pady=4)
    sistema_var = ctk.StringVar(value='PD consolidado')
    ctk.CTkComboBox(
        sec_inputs,
        values=['Convencional', 'Implantação do PD', 'PD consolidado'],
        state='readonly',
        variable=sistema_var,
        width=180,
    ).grid(row=0, column=1, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='Profundidade da análise:', font=body_font).grid(row=0, column=2, sticky='w', pady=4)
    profundidade_var = ctk.StringVar(value='0-20 cm')
    ctk.CTkComboBox(
        sec_inputs,
        values=['0-20 cm', '0-10 cm', '10-20 cm'],
        state='readonly',
        variable=profundidade_var,
        width=150,
    ).grid(row=0, column=3, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='pH alvo:', font=body_font).grid(row=1, column=0, sticky='w', pady=4)
    ph_alvo_var = ctk.StringVar(value='6.0')
    ctk.CTkComboBox(
        sec_inputs,
        values=['5.5', '6.0', '6.5'],
        state='readonly',
        variable=ph_alvo_var,
        width=120,
    ).grid(row=1, column=1, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='V% atual:', font=body_font).grid(row=1, column=2, sticky='w', pady=4)
    v_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=v_var, width=120).grid(row=1, column=3, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='Al% (saturação):', font=body_font).grid(row=2, column=0, sticky='w', pady=4)
    alpct_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=alpct_var, width=120).grid(row=2, column=1, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='PRNT (%):', font=body_font).grid(row=2, column=2, sticky='w', pady=4)
    prnt_var = ctk.StringVar(value='100')
    ctk.CTkEntry(sec_inputs, textvariable=prnt_var, width=120).grid(row=2, column=3, sticky='w', padx=6)

    ctk.CTkLabel(sec_inputs, text='Al trocável (cmolc/dm³):', font=body_font).grid(row=3, column=0, sticky='w', pady=4)
    altroc_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=altroc_var, width=120).grid(row=3, column=1, sticky='w', padx=6)

    sec_summary = make_section(outer, 'Resumo da recomendação', heading_font)
    sec_summary.grid_columnconfigure(1, weight=1)
    summary_vars = {
        'dose': ctk.StringVar(value='-'),
        'total': ctk.StringVar(value='-'),
        'mode': ctk.StringVar(value='-'),
        'epoca': ctk.StringVar(value='-'),
        'tipo': ctk.StringVar(value='-'),
        'tecnica': ctk.StringVar(value='Informe os dados para calcular.'),
    }
    summary_rows = [
        ('Dose recomendada:', 'dose'),
        ('Quantidade total:', 'total'),
        ('Modo de aplicação:', 'mode'),
        ('Época sugerida:', 'epoca'),
        ('Tipo de corretivo:', 'tipo'),
        ('RECOMENDAÇÕES TÉCNICAS:', 'tecnica'),
    ]
    for idx, (rotulo, chave) in enumerate(summary_rows):
        ctk.CTkLabel(sec_summary, text=rotulo, font=body_font).grid(row=idx, column=0, sticky='w', pady=2)
        ctk.CTkLabel(sec_summary, textvariable=summary_vars[chave], font=body_font, anchor='w', justify='left').grid(row=idx, column=1, sticky='w', pady=2)

    _registrar_calagem(ctx, prnt=_f(prnt_var.get(), 100.0))

    btn_calc = ctk.CTkButton(outer, text='CALCULAR')
    btn_calc.pack(pady=(12, 6))

    toggle_state = {'visible': False}
    toggle_button = ctk.CTkButton(outer, text='Exibir outras informações', fg_color='#333333', hover_color='#454545')
    toggle_button.pack(pady=(4, 4))

    sec_methods = make_section(outer, 'Outras informações (PRNT 100%)', heading_font)
    method_display_var = ctk.StringVar(value='Método predominante: -')
    ctk.CTkLabel(sec_methods, textvariable=method_display_var, font=body_font, anchor='w').pack(fill='x', pady=(0, 4))

    mg_info_var = ctk.StringVar(value='Mg trocável: sem dados')
    ctk.CTkLabel(sec_methods, textvariable=mg_info_var, font=body_font, anchor='w').pack(fill='x', pady=(0, 4))

    method_labels = {
        'SMP': ctk.CTkLabel(sec_methods, text='Tabela SMP: aguardando dados', font=body_font, anchor='w', justify='left'),
        'V%': ctk.CTkLabel(sec_methods, text='Método da saturação (V%): aguardando dados', font=body_font, anchor='w', justify='left'),
        'Polinomial': ctk.CTkLabel(sec_methods, text='Equação polinomial (MO/Al): aguardando dados', font=body_font, anchor='w', justify='left'),
    }
    for lbl in method_labels.values():
        lbl.pack(fill='x', pady=2)

    extras_wrapper = sec_methods.master
    extras_wrapper.pack_forget()

    def toggle_extras():
        if toggle_state['visible']:
            extras_wrapper.pack_forget()
            toggle_state['visible'] = False
            toggle_button.configure(text='Exibir outras informações')
        else:
            extras_wrapper.pack(fill='x', pady=(8, 0), after=toggle_button)
            toggle_state['visible'] = True
            toggle_button.configure(text='Ocultar outras informações')

    toggle_button.configure(command=toggle_extras)

    def atualizar_metodos(resultados):
        mapping = {
            'SMP': 'Tabela SMP',
            'V%': 'Método da saturação (V%)',
            'Polinomial': 'Equação polinomial (MO/Al)',
        }
        for chave, label in method_labels.items():
            if chave in resultados:
                label.configure(text=f"{mapping[chave]}: {resultados[chave]:.2f} t/ha")
            else:
                label.configure(text=f"{mapping[chave]}: dados insuficientes")

    def calcular():
        try:
            entradas = ctx.get_entradas() if hasattr(ctx, 'get_entradas') else {}
            smp = _f(entradas.get('Indice SMP'))
            ph_agua = _f(entradas.get('pH (Agua)'))
            argila = _f(entradas.get('Argila (%)'))
            mo = _f(entradas.get('M.O. (%)'))
            area = _f(entradas.get('Area (Ha)'), 0.0)
            mg = _f(entradas.get('Mg (cmolc/dm3)'))
            ctc = _f(entradas.get('CTC (cmolc/dm3)'))

            v_pct = _f(v_var.get())
            alpct = _f(alpct_var.get())
            prnt = _f(prnt_var.get(), 100.0)
            al_troc = _f(altroc_var.get())
            desired_pH = _f(ph_alvo_var.get(), 6.0)
            if desired_pH not in V_TARGETS:
                desired_pH = 6.0

            sistema = sistema_var.get()
            profundidade = profundidade_var.get()

            resultados_metodo = {}

            if smp is not None:
                dose_smp = lime_dose_from_SMP(smp, desired_pH)
                if dose_smp is not None:
                    resultados_metodo['SMP'] = max(0.0, dose_smp)
            if ctc is not None and v_pct is not None:
                dose_v = lime_dose_from_V(ctc, v_pct, desired_pH)
                if dose_v is not None:
                    resultados_metodo['V%'] = max(0.0, dose_v)
            if mo is not None and al_troc is not None:
                dose_poly = lime_dose_from_polynomial(mo, al_troc, desired_pH)
                if dose_poly is not None:
                    resultados_metodo['Polinomial'] = max(0.0, dose_poly)

            atualizar_metodos(resultados_metodo)

            target_v = V_TARGETS.get(desired_pH, 75.0)
            dispensa = False
            if v_pct is not None and v_pct >= target_v and (alpct is None or alpct < ALPCT_LIMIT_NO_LIME):
                dispensa = True
            elif ph_agua is not None and ph_agua >= PH_THRESHOLD_NEED and (alpct is None or alpct < ALPCT_LIMIT_NO_LIME):
                if v_pct is None or v_pct >= target_v - 5:
                    dispensa = True

            if dispensa:
                summary_vars['dose'].set('0.00 t/ha')
                summary_vars['total'].set('0.00 t')
                summary_vars['mode'].set('-')
                summary_vars['epoca'].set('-')
                summary_vars['tipo'].set('-')
                if v_pct is not None:
                    summary_vars['tecnica'].set(f'Repetir análise na próxima safra para monitorar V% (atual {v_pct:.1f}%).')
                else:
                    summary_vars['tecnica'].set('Repetir análise na próxima safra para monitoramento.')
                method_display_var.set('Método predominante: sem necessidade')
                atualizar_metodos({})
                label_ctx = ctx.labels_resultado.get('Calcario (PRNT 100%)')
                if label_ctx is not None:
                    label_ctx.configure(text='0.00 t/ha')
                mg_info_var.set('Mg trocável: sem dados')
                tecnica_msg = summary_vars['tecnica'].get()
                _registrar_calagem(ctx, 0.0, area, 'Sem necessidade', '', '', tecnica_msg, prnt)
                atualiza_res = getattr(ctx, 'atualizar_resultados', None)
                if callable(atualiza_res):
                    atualiza_res()
                return

            if not resultados_metodo:
                raise ValueError('Forneça SMP, V% com CTC ou MO e Al para permitir o cálculo.')

            usar_polynomial = False
            if argila is not None and argila < 20.0:
                usar_polynomial = True
            elif smp is not None and smp >= 6.3:
                usar_polynomial = True
            elif ctc is not None and ctc < 7.5:
                usar_polynomial = True

            metodo_usado = None
            dose_prnt100 = 0.0
            if usar_polynomial and 'Polinomial' in resultados_metodo:
                metodo_usado = 'Equação polinomial (solos leves)'
                dose_prnt100 = resultados_metodo['Polinomial']
            elif 'SMP' in resultados_metodo:
                metodo_usado = 'Tabela SMP'
                dose_prnt100 = resultados_metodo['SMP']
            elif 'V%' in resultados_metodo:
                metodo_usado = 'Saturação por bases (V%)'
                dose_prnt100 = resultados_metodo['V%']
            else:
                chave, valor = next(iter(resultados_metodo.items()))
                metodo_usado = chave
                dose_prnt100 = valor

            dose_prnt100 = max(0.0, dose_prnt100)

            modo = 'Incorporar'
            epoca = 'Aplicar e incorporar até 3 meses antes da semeadura.'
            if sistema == 'PD consolidado':
                if (alpct is not None and alpct >= ALPCT_RESTR_THRESHOLD) or (ph_agua is not None and ph_agua <= PH_SEVERE_PD):
                    pass
                else:
                    modo = 'Superficial'
                    dose_prnt100 *= 0.25
            if prnt is None:
                raise ValueError('Informe o PRNT do corretivo.')
            dose_ajustada = adjust_for_prnt(dose_prnt100, prnt)
            if modo == 'Superficial':
                dose_ajustada = cap_surface_application(dose_ajustada, 5.0)

            total_t = dose_ajustada * max(0.0, area or 0.0)
            tipo_calcario = 'Calcítico ou dolomítico'
            if mg is not None and mg < MG_LOW_THRESHOLD:
                tipo_calcario = 'Preferir calcário dolomítico'

            summary_vars['dose'].set(f"{dose_ajustada:.2f} t/ha (PRNT {prnt:.0f}%)")
            summary_vars['total'].set(f"{total_t:.2f} t")
            summary_vars['mode'].set(modo)
            summary_vars['epoca'].set(epoca)
            summary_vars['tipo'].set(tipo_calcario)
            if v_pct is not None and v_pct < target_v:
                summary_vars['tecnica'].set(f'Repetir análise na próxima safra para verificar elevação do V% (alvo {target_v:.0f}%).')
            else:
                summary_vars['tecnica'].set('Repetir análise na próxima safra para monitoramento.')

            method_display_var.set(f"Método predominante: {metodo_usado}")

            label_ctx = ctx.labels_resultado.get('Calcario (PRNT 100%)')
            if label_ctx is not None:
                label_ctx.configure(text=f"{dose_prnt100:.2f} t/ha (pH alvo {desired_pH:.1f})")

            if mg is not None:
                mg_info_var.set(f"Mg trocável: {mg:.2f} cmolc/dm³ (limite 1.0)")
            else:
                mg_info_var.set('Mg trocável: sem dados')
            tecnica_msg = summary_vars['tecnica'].get()
            _registrar_calagem(ctx, dose_ajustada, area, modo, epoca, tipo_calcario, tecnica_msg, prnt)
            atualiza_res = getattr(ctx, 'atualizar_resultados', None)
            if callable(atualiza_res):
                atualiza_res()
        except ValueError as exc:
            messagebox.showerror('Calagem', str(exc))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror('Calagem', f'Erro inesperado: {exc}')

    btn_calc.configure(command=calcular)

    if logo_image is not None:
        place_logo_footer(outer, logo_image, padx=10, pady=10)
    else:
        try:
            from PIL import Image

            base_dir = Path(__file__).resolve().parent
            logo_path = base_dir.parent / "imagem.png"
            img = Image.open(logo_path)
            img.thumbnail((120, 60))
            logo = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            place_logo_footer(outer, logo, padx=10, pady=10)
        except Exception:
            pass
