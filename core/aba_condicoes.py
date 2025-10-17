from __future__ import annotations

import re
import customtkinter as ctk

from .context import AppContext, TabHost
from . import diagnostico
from .ui import (
    add_value_row,
    coletar_diagnostico_entradas,
    create_label,
    make_section,
)
from .design_constants import (
    FONT_SIZE_BODY,
    FONT_SIZE_HEADING,
    FONT_SIZE_SMALL,
    PADX_STANDARD,
    PADY_SMALL,
    PADY_STANDARD,
    WARNING_ORANGE,
)


def _criar_alerta_widgets(container: ctk.CTkFrame, alertas: list[str], wrap: int = 520) -> None:
    """Renderiza alertas técnicos em cartões compactos."""
    for widget in container.winfo_children():
        widget.destroy()

    if not alertas:
        vazio = create_label(
            container,
            "Nenhum alerta específico identificado.",
            font_size=FONT_SIZE_BODY,
            weight="normal",
        )
        vazio.configure(anchor="w", justify="left", wraplength=wrap, text_color=WARNING_ORANGE)
        vazio.pack(fill="x", pady=PADY_SMALL)
        return

    pattern = re.compile(r"([A-ZÁÉÍÓÚÃÕÇ%\s]+):")
    for alerta in alertas:
        alerta_formatado = alerta.lstrip("- ").strip()
        match = pattern.search(alerta_formatado)

        card = ctk.CTkFrame(container, fg_color="transparent")
        card.pack(fill="x", pady=PADY_SMALL)

        if match:
            titulo = match.group(1).strip().title()
            restante = alerta_formatado[match.end():].strip()
            titulo_lbl = create_label(card, f"{titulo}:", font_size=FONT_SIZE_BODY, weight="bold")
            titulo_lbl.configure(text_color=WARNING_ORANGE)
            titulo_lbl.pack(anchor="w")

            corpo_lbl = create_label(card, restante, font_size=FONT_SIZE_BODY)
            corpo_lbl.configure(anchor="w", justify="left", wraplength=wrap, text_color=WARNING_ORANGE)
            corpo_lbl.pack(fill="x")
        else:
            texto_lbl = create_label(card, alerta_formatado, font_size=FONT_SIZE_BODY)
            texto_lbl.configure(anchor="w", justify="left", wraplength=wrap, text_color=WARNING_ORANGE)
            texto_lbl.pack(fill="x")


def add_tab(tabhost: TabHost, ctx: AppContext):
    heading_font = getattr(ctx, "heading_font", ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"))

    aba = tabhost.add_tab("🧭 Condições do Solo")
    outer = ctk.CTkScrollableFrame(aba, fg_color="transparent")
    outer.pack(fill="both", expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)
    outer.grid_columnconfigure(0, weight=1)

    sec_prop = make_section(outer, "🧱 Propriedades Gerais", heading_font)
    for nome in ["Classe do teor de Argila", "CTC", "M.O."]:
        add_value_row(sec_prop, nome, ctx.labels_classificacao)

    sec_macro = make_section(outer, "🌱 Macronutrientes", heading_font)
    for nome in ["Fósforo (P)", "Potássio (K)", "Cálcio (Ca)", "Magnésio (Mg)", "Enxofre (S)"]:
        add_value_row(sec_macro, nome, ctx.labels_classificacao)

    sec_micro = make_section(outer, "🔬 Micronutrientes", heading_font)
    for nome in ["Zinco (Zn)", "Cobre (Cu)", "Boro (B)", "Manganês (Mn)"]:
        add_value_row(sec_micro, nome, ctx.labels_classificacao)

    resumo_section = make_section(outer, "🩺 Resumo do Diagnóstico", heading_font)
    resumo_section.grid_columnconfigure(0, weight=0)
    resumo_section.grid_columnconfigure(1, weight=1)

    summary_vars = {
        "p": ctk.StringVar(value="-"),
        "k": ctk.StringVar(value="-"),
        "tecnica": ctk.StringVar(
            value="Informe os dados e calcule na aba principal para ver o diagnóstico."
        ),
    }
    resumo_rows = [
        ("Resposta ao P:", "p"),
        ("Resposta ao K:", "k"),
        ("Recomendação:", "tecnica"),
    ]
    for idx, (rotulo, chave) in enumerate(resumo_rows):
        create_label(resumo_section, rotulo, font_size=FONT_SIZE_SMALL, weight="bold").grid(
            row=idx, column=0, sticky="w", pady=PADY_SMALL
        )
        valor = create_label(resumo_section, "", font_size=FONT_SIZE_SMALL)
        valor.configure(textvariable=summary_vars[chave], anchor="w", justify="left")
        valor.grid(row=idx, column=1, sticky="w", pady=PADY_SMALL)

    alertas_section = make_section(outer, "⚠️ Alertas Técnicos", heading_font)
    alertas_container = ctk.CTkFrame(alertas_section, fg_color="transparent")
    alertas_container.pack(fill="x")

    if getattr(ctx, "logo_image", None) is not None:
        logo_label = ctk.CTkLabel(aba, image=ctx.logo_image, text="")
        logo_label.pack(anchor="se", padx=PADX_STANDARD, pady=PADY_STANDARD)
        logo_label.image = ctx.logo_image

    ctx.condicoes_controls = {
        "summary": summary_vars,
        "alertas_container": alertas_container,
    }
    return ctx.condicoes_controls


def atualizar(ctx: AppContext) -> None:
    controles = getattr(ctx, "condicoes_controls", None)
    if not controles:
        return

    entradas = ctx.get_entradas()
    dados_diag = coletar_diagnostico_entradas(entradas)
    diag = diagnostico.diagnosticar_soja(dados_diag)
    ctx._diag_cache = diag  # reutilizado por outras abas

    summary = controles["summary"]
    macros = diag["macronutrientes"]
    alertas = diag["alertas"]

    p_prob = macros["P"].get("prob_resposta") or "-"
    summary["p"].set(p_prob)

    k_prob = macros["K"].get("prob_resposta") or "-"
    summary["k"].set(k_prob)

    if macros["P"].get("classe") in ("Muito Baixo", "Baixo") or macros["K"].get("classe") in ("Muito Baixo", "Baixo"):
        summary["tecnica"].set("Repetir a análise na próxima safra para confirmar a correção.")
    else:
        summary["tecnica"].set("Repetir a análise na próxima safra para monitoramento.")

    _criar_alerta_widgets(controles["alertas_container"], alertas)
