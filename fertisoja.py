# -*- coding: utf-8 -*-
"""Interface principal do Fertisoja."""
from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext, TabHost
from core.design_constants import *

def main():
    ctk.set_appearance_mode('dark')
    janela = ctk.CTk()
    janela.title('🌱 Fertisoja - Sistema de Recomendação de Adubação')
    janela.configure(fg_color=(BACKGROUND_LIGHT, BACKGROUND_DARK))
    
    # Configuração responsiva da janela
    largura, altura = 1200, 750
    pos_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    pos_y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    janela.resizable(True, True)
    janela.minsize(1000, 600)

    # Configuração do grid principal
    janela.grid_rowconfigure(0, weight=1)
    janela.grid_columnconfigure(0, weight=1)
    
    # Container principal com novo estilo
    tab_container = ctk.CTkFrame(janela, fg_color=(PANEL_LIGHT, PANEL_DARK))
    tab_container.grid(row=0, column=0, sticky="nsew", padx=PADX_STANDARD, pady=PADY_STANDARD)
    tab_container.grid_rowconfigure(0, weight=1)
    tab_container.grid_columnconfigure(0, weight=1)

    # TabView com novo estilo
    tabview = ctk.CTkTabview(tab_container, 
                            fg_color=(PANEL_LIGHT, PANEL_DARK),
                            segmented_button_fg_color=(BACKGROUND_LIGHT, BACKGROUND_DARK),
                            segmented_button_selected_color=PRIMARY_BLUE,
                            segmented_button_selected_hover_color=PRIMARY_HOVER)
    tabview.grid(row=0, column=0, sticky="nsew", padx=PADX_SMALL, pady=PADY_SMALL)

    # Scrollbar para tabs (se necessário)
    tab_scroll = ctk.CTkScrollbar(tab_container, orientation='horizontal', command=tabview._segmented_button._canvas.xview)
    tab_scroll.grid(row=1, column=0, sticky="ew", pady=(PADY_SMALL, 0))
    tabview._segmented_button._canvas.configure(xscrollcommand=tab_scroll.set)

    def _scroll_tabs(event):
        passo = -1 if event.delta > 0 else 1
        tabview._segmented_button._canvas.xview_scroll(passo, 'units')
        return 'break'

    tabview._segmented_button._canvas.bind('<Shift-MouseWheel>', _scroll_tabs)

    tabhost = TabHost(tabview)

    from core import aba_dados, aba_condicoes, aba_adubacao, aba_fertilizacao, aba_mapa_area, aba_recomendacao_calcario

    ctx = AppContext(
        janela=janela,
        abas=tabhost,
        campos={},
        labels_classificacao={},
        labels_resultado={},
        cultivo_var=ctk.StringVar(value='1º Cultivo'),
        calcular=lambda: False,
    )

    aba_dados.add_tab(tabhost, ctx)
    aba_condicoes.add_tab(tabhost, ctx)
    aba_recomendacao_calcario.add_tab(tabhost, ctx)
    aba_adubacao.add_tab(tabhost, ctx)
    aba_fertilizacao.add_tab(tabhost, ctx)
    #aba_mapa_area.add_tab(tabhost, ctx)

    aba_condicoes.atualizar(ctx)
    aba_adubacao.atualizar(ctx)

    janela.mainloop()


if __name__ == '__main__':
    main()
