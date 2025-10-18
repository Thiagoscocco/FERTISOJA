from __future__ import annotations

"""
Overlay de boas-vindas replicando o layout inicial do FertiCalc,
adaptado para o contexto do Fertisoja.
"""

import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .design_constants import (
    FONT_SIZE_BODY,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
    TEXT_PRIMARY,
)


def _resource_path(relative: str) -> Path:
    """Resolve paths tanto em desenvolvimento quanto em bundles PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


class IntroOverlay:
    """Overlay inicial com instrucoes de uso do Fertisoja."""

    def __init__(self, parent: ctk.CTk | ctk.CTkFrame) -> None:
        self._parent = parent
        self._frame: ctk.CTkFrame | None = None
        self._logo_image: ctk.CTkImage | None = None
        self._build()

    def _build(self) -> None:
        logo_path = _resource_path(Path("imagem.png"))

        self._frame = ctk.CTkFrame(self._parent, fg_color="#2d2f36")
        self._frame.place(relx=0.5, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")

        content = ctk.CTkScrollableFrame(
            self._frame,
            fg_color="#343741",
            scrollbar_button_color="#4f6ecf",
            scrollbar_button_hover_color="#4059a6",
        )
        content.pack(expand=True, padx=60, pady=50, fill="both")
        content.grid_columnconfigure(0, weight=1)

        titulo_font = ctk.CTkFont(size=24, weight="bold")
        corpo_font = ctk.CTkFont(size=FONT_SIZE_BODY + 1)
        destaque_font = ctk.CTkFont(size=FONT_SIZE_BODY + 2, weight="bold")
        button_font = ctk.CTkFont(size=20, weight="bold")

        row = 0
        if logo_path.exists():
            imagem = Image.open(logo_path)
            largura, altura = imagem.size
            alvo_largura = 260
            alvo_altura = int(alvo_largura * altura / largura) if largura else 260
            self._logo_image = ctk.CTkImage(
                light_image=imagem, dark_image=imagem, size=(alvo_largura, alvo_altura)
            )
            ctk.CTkLabel(content, image=self._logo_image, text="").grid(row=row, column=0, pady=(0, 24))
            row += 1

        ctk.CTkLabel(
            content,
            text="BEM-VINDO AO FERTISOJA",
            font=titulo_font,
            text_color=TEXT_PRIMARY,
        ).grid(row=row, column=0, pady=(0, 18), sticky="n")
        row += 1

        descricao = (
            "Plataforma integrada para interpretar laudos de solo e planejar calc\u00e1rio e aduba\u00e7\u00e3o "
            "dedicados \u00e0 soja. Transforme an\u00e1lises laboratoriais em diagn\u00f3sticos pr\u00e1ticos com o "
            "m\u00e9todo CQFS-RS/SC, vis\u00e3o por talh\u00e3o e suporte para parcelar doses e exportar planos."
        )
        ctk.CTkLabel(
            content,
            text=descricao,
            font=corpo_font,
            wraplength=720,
            justify="center",
            text_color="#dfe3f7",
        ).grid(row=row, column=0, pady=(0, 24), padx=30, sticky="n")
        row += 1

        bloco_instr = ctk.CTkFrame(content, fg_color="#3d414d", corner_radius=18)
        bloco_instr.grid(row=row, column=0, pady=(0, 24), padx=30, sticky="ew")
        bloco_instr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            bloco_instr,
            text="INSTRU\u00c7\u00d5ES",
            font=destaque_font,
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", pady=(14, 6), padx=20)
        bullets = [
            "ABA DADOS DA AN\u00c1LISE DE SOLO \u2014 importe o laudo, use o exemplo padr\u00e3o e gere o diagn\u00f3stico inicial.",
            "ABA CONDI\u00c7\u00d5ES DO SOLO \u2014 visualize classes, probabilidades de resposta e alertas autom\u00e1ticos.",
            "ABA RECOMENDA\u00c7\u00c3O DE CALC\u00c1RIO \u2014 ajuste metas de saturac\u00e3o, SMP e compare cen\u00e1rios por talh\u00e3o.",
            "ABA RECOMENDA\u00c7\u00d5ES DE ADUBA\u00c7\u00c3O \u2014 escolha entre corre\u00e7\u00e3o, manuten\u00e7\u00e3o ou rep\u00f5s\u00e3o e confira nutrientes extras.",
            "ABA ESCOLHA DOS FERTILIZANTES \u2014 combine fontes comerciais, controle limites na linha e salve o plano por cultivo.",
            "ABAS RESULTADOS E EXPORTA\u00c7\u00c3O \u2014 revise totais por hectare e por \u00e1rea, gere planilhas e relat\u00f3rios finais.",
        ]
        bullet_font = ctk.CTkFont(size=FONT_SIZE_BODY + 1)
        for idx, item in enumerate(bullets, start=1):
            ctk.CTkLabel(
                bloco_instr,
                text=f"\u2022 {item}",
                font=bullet_font,
                text_color="#eef1fb",
                justify="left",
                wraplength=680,
            ).grid(row=idx, column=0, sticky="w", padx=20, pady=2)
        row += 1

        aviso = (
            "As recomenda\u00e7\u00f5es consideram refer\u00eancias regionais e assumem manejo padr\u00e3o. "
            "Revise resultados, valide com engenheiro agr\u00f4nomo e adapte \u00e0 realidade da propriedade."
        )
        ctk.CTkLabel(
            content,
            text=aviso,
            font=corpo_font,
            text_color="#b6bdcd",
            wraplength=720,
            justify="center",
        ).grid(row=row, column=0, pady=(0, 24), padx=40, sticky="n")
        row += 1

        agradecimentos = (
            "EQUIPE FERTISOJA\n"
            "UFRGS \u2022 GEAD \u2022 DEPLAV \u2022 SOLOS \u2022 COLABORADORES DO CAMPO\n"
            "DEV Thiagoscocco UFRGS 2025"
        )
        ctk.CTkLabel(
            content,
            text=agradecimentos,
            font=destaque_font,
            text_color=TEXT_PRIMARY,
            wraplength=720,
            justify="center",
        ).grid(row=row, column=0, pady=(0, 32), padx=30, sticky="n")
        row += 1

        ctk.CTkButton(
            content,
            text="COME\u00c7AR O PLANEJAMENTO",
            font=button_font,
            fg_color=PRIMARY_BLUE,
            hover_color=PRIMARY_HOVER,
            text_color="#ffffff",
            command=self.hide,
            width=280,
            height=46,
            corner_radius=18,
        ).grid(row=row, column=0, pady=(0, 12))

    def hide(self) -> None:
        """Remove o overlay da interface."""
        if self._frame is not None:
            self._frame.destroy()
            self._frame = None
            self._logo_image = None
