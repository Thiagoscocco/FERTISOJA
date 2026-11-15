from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .fonts import aplicar_fonte_global
from .context import AppContext, TabHost
from . import calculo
from .ui import (
    create_calc_button,
    create_compact_form,
    create_label,
    enable_mousewheel_scroll,
    make_section,
    place_logo_footer,
)
from .design_constants import (
    ENTRY_WIDTH_SMALL,
    ENTRY_WIDTH_STANDARD,
    PADX_STANDARD,
    PADY_SMALL,
    PADY_STANDARD,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
)
from . import aba_condicoes, aba_adubacao


DEFAULTS = {
    "Produtividade esperada": "6",
    "Area (Ha)": "0.63",
    "Indice SMP": "6.6",
    "Argila (%)": "30",
    "CTC (cmolc/dm3)": "7.23",
    "M.O. (%)": "2.1",
    "pH (Agua)": "5.9",
    "P (mg/dm3)": "7.9",
    "K (mg/dm3)": "126",
    "S (mg/dm3)": "3.4",
    "Ca (cmolc/dm3)": "1.6",
    "Mg (cmolc/dm3)": "6",
    "Zn (mg/dm3)": "2.4",
    "Cu (mg/dm3)": "1.3",
    "B (mg/dm3)": "0.4",
    "Mn (mg/dm3)": "8",
}


def _carregar_logo(parent: ctk.CTkScrollableFrame) -> ctk.CTkImage | None:
    logo_path = Path(__file__).resolve().parent.parent / "imagem.png"
    try:
        imagem = Image.open(logo_path)
        max_w = 120
        if imagem.width > max_w:
            proporcao = max_w / imagem.width
            imagem = imagem.resize(
                (int(imagem.width * proporcao), int(imagem.height * proporcao)),
                Image.LANCZOS,
            )
        logo_image = ctk.CTkImage(
            light_image=imagem,
            dark_image=imagem,
            size=(imagem.width, imagem.height),
        )
        place_logo_footer(parent, logo_image, text="")
        return logo_image
    except Exception:
        return None


def add_tab(tabhost: TabHost, ctx: AppContext):
    janela = ctx.janela
    _, heading_font = aplicar_fonte_global(janela)
    ctx.heading_font = heading_font

    cultivo_var = ctk.StringVar(value="2º Cultivo")
    calculo.ligar_cultivo_var(cultivo_var)
    ctx.cultivo_var = cultivo_var

    campos = calculo.campos
    labels_classificacao = calculo.labels_classificacao
    labels_resultado = calculo.labels_resultado
    ctx.labels_classificacao = labels_classificacao
    ctx.labels_resultado = labels_resultado
    ctx.campos = campos
    ctx.calcular = calculo.calcular

    aba_entrada = tabhost.add_tab("🌾 Dados da Análise de Solo")

    aba_entrada.grid_columnconfigure(0, weight=1)
    aba_entrada.grid_rowconfigure(0, weight=1)
    aba_entrada.grid_rowconfigure(1, weight=0)

    conteudo = ctk.CTkScrollableFrame(aba_entrada, fg_color="transparent")
    enable_mousewheel_scroll(janela, conteudo)
    conteudo.grid(row=0, column=0, sticky="nsew", padx=PADX_STANDARD, pady=PADY_STANDARD)
    conteudo.grid_columnconfigure(0, weight=1)

    logo_image = _carregar_logo(conteudo)

    sec_producao = make_section(conteudo, "📊 Informações da Produção", heading_font)
    create_compact_form(
        sec_producao,
        [
            ("Produtividade esperada (t/ha)", "Produtividade esperada", ENTRY_WIDTH_STANDARD),
            ("Área (ha)", "Area (Ha)", ENTRY_WIDTH_SMALL),
        ],
        campos,
        DEFAULTS,
        columns=2,
        entry_width=ENTRY_WIDTH_STANDARD,
    )

    cultivo_card = ctk.CTkFrame(sec_producao, fg_color="transparent")
    cultivo_card.pack(fill="x", pady=(PADY_SMALL, 0))
    create_label(cultivo_card, "Cultivo", weight="bold").pack(anchor="w")
    radio_frame = ctk.CTkFrame(cultivo_card, fg_color="transparent")
    radio_frame.pack(anchor="w", pady=(PADY_SMALL // 2, 0))
    ctk.CTkRadioButton(
        radio_frame,
        text="1º Cultivo",
        variable=cultivo_var,
        value="1º Cultivo",
        fg_color=PRIMARY_BLUE,
        hover_color=PRIMARY_HOVER,
    ).pack(side="left", padx=(0, PADX_STANDARD))
    ctk.CTkRadioButton(
        radio_frame,
        text="2º Cultivo",
        variable=cultivo_var,
        value="2º Cultivo",
        fg_color=PRIMARY_BLUE,
        hover_color=PRIMARY_HOVER,
    ).pack(side="left")

    sec_condicoes = make_section(conteudo, "🧪 Condições do Solo", heading_font)
    create_compact_form(
        sec_condicoes,
        [
            ("Índice SMP", "Indice SMP", ENTRY_WIDTH_SMALL),
            ("Argila (%)", "Argila (%)", ENTRY_WIDTH_SMALL),
            ("CTC (cmolc/dm³)", "CTC (cmolc/dm3)", ENTRY_WIDTH_STANDARD),
            ("M.O. (%)", "M.O. (%)", ENTRY_WIDTH_SMALL),
            ("pH (água)", "pH (Agua)", ENTRY_WIDTH_SMALL),
        ],
        campos,
        DEFAULTS,
        columns=2,
        entry_width=ENTRY_WIDTH_SMALL,
    )

    sec_nutrientes = make_section(conteudo, "🌿 Teor de Nutrientes", heading_font)
    create_compact_form(
        sec_nutrientes,
        [
            ("P (mg/dm³)", "P (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("K (mg/dm³)", "K (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("S (mg/dm³)", "S (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("Ca (cmolc/dm³)", "Ca (cmolc/dm3)", ENTRY_WIDTH_SMALL),
            ("Mg (cmolc/dm³)", "Mg (cmolc/dm3)", ENTRY_WIDTH_SMALL),
            ("Zn (mg/dm³)", "Zn (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("Cu (mg/dm³)", "Cu (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("B (mg/dm³)", "B (mg/dm3)", ENTRY_WIDTH_SMALL),
            ("Mn (mg/dm³)", "Mn (mg/dm3)", ENTRY_WIDTH_SMALL),
        ],
        campos,
        DEFAULTS,
        columns=3,
        entry_width=ENTRY_WIDTH_SMALL,
    )

    status_var = ctk.StringVar(value="")

    def executar_calculo_principal() -> None:
        status_var.set("")
        status_label.grid_remove()
        if calculo.calcular():
            status_var.set("Cálculo atualizado com sucesso.")
            status_label.grid()
            aba_condicoes.atualizar(ctx)
            aba_adubacao.atualizar(ctx)
            atualiza_fert = getattr(ctx, "atualizar_fertilizacao", None)
            if callable(atualiza_fert):
                atualiza_fert()
            atualiza_res = getattr(ctx, "atualizar_resultados", None)
            if callable(atualiza_res):
                atualiza_res()
            def limpar_status() -> None:
                status_var.set("")
                status_label.grid_remove()

            janela.after(4000, limpar_status)

    rodape = ctk.CTkFrame(aba_entrada, fg_color="transparent")
    rodape.grid(row=1, column=0, sticky="ew", padx=PADX_STANDARD, pady=(2, 6))
    rodape.grid_columnconfigure(0, weight=1)

    btn_calcular = create_calc_button(
        rodape,
        "🧮 Calcular",
        executar_calculo_principal,
        width=132,
        height=36,
    )
    btn_calcular.grid(row=0, column=0)

    status_label = create_label(rodape, "", weight="bold")
    status_label.configure(textvariable=status_var, text_color=PRIMARY_BLUE, anchor="center")
    status_label.grid(row=1, column=0, sticky="n", padx=0)
    status_label.grid_remove()

    ctx.logo_image = logo_image

    return {
        "status": status_var,
        "logo_image": logo_image,
    }
