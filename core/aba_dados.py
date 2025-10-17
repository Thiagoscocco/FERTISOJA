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
    make_section,
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


TEST_DEFAULTS = {
    "Produtividade esperada": "3.6",
    "Area (Ha)": "15",
    "Indice SMP": "6.7",
    "Argila (%)": "13",
    "CTC (cmolc/dm3)": "2.5",
    "M.O. (%)": "0.6",
    "pH (Agua)": "4.7",
    "P (mg/dm3)": "2.6",
    "K (mg/dm3)": "21",
    "S (mg/dm3)": "2.8",
    "Ca (cmolc/dm3)": "0.3",
    "Mg (cmolc/dm3)": "0.2",
    "Zn (mg/dm3)": "0.3",
    "Cu (mg/dm3)": "0.5",
    "B (mg/dm3)": "0.1",
    "Mn (mg/dm3)": "4",
}


def _carregar_logo(parent: ctk.CTkScrollableFrame) -> ctk.CTkImage | None:
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
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
        logo_label = ctk.CTkLabel(parent, image=logo_image, text="")
        logo_label.pack(anchor="ne", padx=PADX_STANDARD, pady=(0, PADY_STANDARD))
        logo_label.image = logo_image
        return logo_image
    except Exception:
        ctk.CTkLabel(parent, text="(imagem não carregada)").pack(
            anchor="ne", padx=PADX_STANDARD, pady=(0, PADY_STANDARD)
        )
        return None


def add_tab(tabhost: TabHost, ctx: AppContext):
    janela = ctx.janela
    _, heading_font = aplicar_fonte_global(janela)
    ctx.heading_font = heading_font

    cultivo_var = ctk.StringVar(value="1º Cultivo")
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
        TEST_DEFAULTS,
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
        TEST_DEFAULTS,
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
        TEST_DEFAULTS,
        columns=3,
        entry_width=ENTRY_WIDTH_SMALL,
    )

    status_var = ctk.StringVar(value="")

    def executar_calculo_principal() -> None:
        status_var.set("")
        if calculo.calcular():
            status_var.set("Cálculo atualizado com sucesso.")
            aba_condicoes.atualizar(ctx)
            aba_adubacao.atualizar(ctx)
            atualiza_fert = getattr(ctx, "atualizar_fertilizacao", None)
            if callable(atualiza_fert):
                atualiza_fert()
            atualiza_res = getattr(ctx, "atualizar_resultados", None)
            if callable(atualiza_res):
                atualiza_res()
            janela.after(4000, lambda: status_var.set(""))

    rodape = ctk.CTkFrame(aba_entrada, fg_color="transparent")
    rodape.grid(row=1, column=0, sticky="ew", padx=PADX_STANDARD, pady=(PADY_SMALL, PADY_STANDARD))
    rodape.grid_columnconfigure(0, weight=1)

    btn_calcular = create_calc_button(rodape, "🧮 Calcular", executar_calculo_principal)
    btn_calcular.grid(row=0, column=0, pady=(0, PADY_SMALL))

    status_label = create_label(rodape, "", weight="bold")
    status_label.configure(textvariable=status_var, text_color=PRIMARY_BLUE, anchor="center")
    status_label.grid(row=1, column=0, sticky="n", padx=0)

    ctx.logo_image = logo_image

    return {
        "status": status_var,
        "logo_image": logo_image,
    }
