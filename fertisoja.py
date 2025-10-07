# -*- coding: utf-8 -*-
"""Interface principal do Fertisoja."""
from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext, TabHost
def main():
    ctk.set_appearance_mode('dark')
    janela = ctk.CTk()
    janela.title('Fertisoja')
    largura, altura = 1040, 650
    pos_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    pos_y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    janela.resizable(False, False)

    tab_container = ctk.CTkFrame(janela, fg_color='transparent')
    tab_container.pack(fill='both', expand=True, padx=16, pady=16)

    tabview = ctk.CTkTabview(tab_container)
    tabview.pack(fill='both', expand=True)

    tab_scroll = ctk.CTkScrollbar(tab_container, orientation='horizontal', command=tabview._segmented_button._canvas.xview)
    tab_scroll.pack(fill='x', pady=(6, 0))
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
