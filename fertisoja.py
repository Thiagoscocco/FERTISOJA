# -*- coding: utf-8 -*-
"""Interface principal do Fertisoja."""
from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext, TabHost
from core.design_constants import (
    BACKGROUND_DARK,
    BACKGROUND_LIGHT,
    CARD_BORDER_COLOR,
    CARD_BORDER_WIDTH,
    CARD_CORNER_RADIUS,
    PADX_MICRO,
    PADX_SMALL,
    PADX_STANDARD,
    PADY_SMALL,
    PADY_STANDARD,
    PANEL_DARK,
    PANEL_LIGHT,
    PLANT_COLOR,
    PLANT_HOVER,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
)


def main() -> None:
    ctk.set_appearance_mode("dark")
    janela = ctk.CTk()
    janela.title("🌱 Fertisoja - Sistema de Recomendação de Adubação")
    janela.configure(fg_color=(BACKGROUND_LIGHT, BACKGROUND_DARK))

    # Configuração responsiva da janela
    largura, altura = 960, 680
    pos_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    pos_y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    janela.resizable(True, True)
    janela.minsize(860, 560)

    # Configuração do grid principal
    janela.grid_rowconfigure(0, weight=1)
    janela.grid_columnconfigure(0, weight=1)

    # Container principal com novo estilo
    tab_container = ctk.CTkFrame(
        janela,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        corner_radius=CARD_CORNER_RADIUS,
        border_width=CARD_BORDER_WIDTH,
        border_color=CARD_BORDER_COLOR,
    )
    tab_container.grid(row=0, column=0, sticky="nsew", padx=PADX_STANDARD, pady=PADY_STANDARD)
    tab_container.grid_rowconfigure(0, weight=0)
    tab_container.grid_rowconfigure(1, weight=1)
    tab_container.grid_rowconfigure(2, weight=0)
    tab_container.grid_columnconfigure(0, weight=1)

    tabs_wrapper = ctk.CTkFrame(
        tab_container,
        fg_color=(PANEL_DARK, PANEL_DARK),
        corner_radius=CARD_CORNER_RADIUS,
        border_width=0,
    )
    tabs_wrapper.grid(row=0, column=0, sticky="ew", padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))
    tabs_wrapper.grid_columnconfigure(0, weight=1)

    # TabView com estilo padronizado
    tabview = ctk.CTkTabview(
        tab_container,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        segmented_button_fg_color=(PLANT_COLOR, PLANT_HOVER),
        segmented_button_selected_color=PRIMARY_BLUE,
        segmented_button_selected_hover_color=PRIMARY_HOVER,
        segmented_button_unselected_color=(CARD_BORDER_COLOR, CARD_BORDER_COLOR),
        segmented_button_unselected_hover_color=(PRIMARY_BLUE, PRIMARY_BLUE),
        border_width=0,
    )
    tabview.grid(row=1, column=0, sticky="nsew", padx=PADX_MICRO, pady=(0, PADY_SMALL))

    tabhost = TabHost(tabview)

    from core import (
        aba_dados,
        aba_condicoes,
        aba_adubacao,
        aba_fertilizacao,
        aba_recomendacao_calcario,
        aba_exportacao,
        aba_resultados,
        aba_mapa_area,
    )

    ctx = AppContext(
        janela=janela,
        abas=tabhost,
        campos={},
        labels_classificacao={},
        labels_resultado={},
        cultivo_var=ctk.StringVar(value="1º Cultivo"),
        calcular=lambda: False,
    )

    aba_dados.add_tab(tabhost, ctx)
    aba_condicoes.add_tab(tabhost, ctx)
    aba_recomendacao_calcario.add_tab(tabhost, ctx)
    aba_adubacao.add_tab(tabhost, ctx)
    aba_fertilizacao.add_tab(tabhost, ctx)
    aba_resultados.add_tab(tabhost, ctx)
    aba_exportacao.add_tab(tabhost, ctx)
    # aba_mapa_area.add_tab(tabhost, ctx)

    tab_segment = tabview._segmented_button  # noqa: SLF001
    tab_segment.grid_remove()

    tab_names = list(tabview._tab_dict.keys())  # noqa: SLF001
    if len(tab_names) > 4:
        top_row = tab_names[:4]
        bottom_row = tab_names[4:]
    else:
        top_row = tab_names
        bottom_row = []

    button_font = ctk.CTkFont(size=14, weight="bold")
    inactive_color = (PLANT_HOVER, PLANT_HOVER)

    buttons: dict[str, ctk.CTkButton] = {}

    def _sync_buttons(active_name: str) -> None:
        for name, btn in buttons.items():
            if name == active_name:
                btn.configure(fg_color=(PLANT_COLOR, PLANT_COLOR), hover_color=PLANT_HOVER)
            else:
                btn.configure(fg_color=inactive_color, hover_color=PLANT_COLOR)

    def _on_tab_click(name: str) -> None:
        tabview.set(name)
        _sync_buttons(name)

    def _build_row(names: list[str], row_index: int, center: bool = False) -> None:
        if not names:
            return
        row_frame = ctk.CTkFrame(
            tabs_wrapper,
            fg_color=(PANEL_DARK, PANEL_DARK),
            border_width=0,
        )
        row_frame.grid(row=row_index, column=0, sticky="ew")
        if center:
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            container = ctk.CTkFrame(row_frame, fg_color=(PANEL_DARK, PANEL_DARK), border_width=0)
            container.grid(row=0, column=1)
        else:
            container = row_frame
        for idx, name in enumerate(names):
            btn = ctk.CTkButton(
                container,
                text=name,
                width=170,
                height=34,
                corner_radius=12,
                fg_color=inactive_color,
                text_color="white",
                font=button_font,
                command=lambda n=name: _on_tab_click(n),
            )
            btn.grid(row=0, column=idx, padx=(0 if idx == 0 else PADX_SMALL, PADX_SMALL), pady=(0, PADY_SMALL))
            buttons[name] = btn

    _build_row(top_row, 0)
    _build_row(bottom_row, 1, center=True)

    def _on_tab_change(name: str) -> None:
        _sync_buttons(name)

    tabview.configure(command=_on_tab_change)
    if tab_names:
        _sync_buttons(tab_names[0])

    aba_condicoes.atualizar(ctx)
    aba_adubacao.atualizar(ctx)

    janela.mainloop()


if __name__ == "__main__":
    main()
