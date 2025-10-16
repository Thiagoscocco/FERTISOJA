# -*- coding: utf-8 -*-

from __future__ import annotations

import io
import mimetypes
import re
import smtplib
import ssl
import shutil
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .context import AppContext, TabHost

from .design_constants import (

    ENTRY_WIDTH_SMALL,

    ENTRY_WIDTH_STANDARD,

    FONT_SIZE_BODY,

    FONT_SIZE_HEADING,

    PADX_MICRO,

    PADX_SMALL,

    PADX_STANDARD,

    PADY_SMALL,

    PADY_STANDARD,

    PANEL_LIGHT,

    PANEL_DARK,

    PRIMARY_BLUE,

    SUCCESS_GREEN,

)

from .ui import (

    create_entry_field,

    create_label,

    create_primary_button,

    make_section,

    normalize_key,

    parse_float,

)

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

PLACEHOLDER_PATTERN = re.compile(r"[xyXY]{3,}")

FERTILIZER_PATTERN = re.compile(r"\(FERTILIZANTE\s+\d+\)", re.IGNORECASE)

TEMPLATE_NAME = "Modelo recomenda\u00e7\u00e3o de aduba\u00e7\u00e3o e calagem.docx"

FERTILIZER_SLOTS = 5

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
HEADER_REL_ID = "rIdExportHeader"
HEADER_PART = "header1.xml"
HEADER_IMAGE_REL_ID = "rIdExportHeaderImage"
HEADER_IMAGE_PATH = "media/logo_thiago.png"
EMAIL_CONFIG_PATH = Path(__file__).resolve().parent.parent / "modelo_mail" / ".env"
EMAIL_SUBJECT = "Recomenda\u00e7\u00e3o de Aduba\u00e7\u00e3o e Calagem \u2013 FertiSoja"
EMAIL_SEPARATOR_PATTERN = re.compile(r"[;,]")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ET.register_namespace("", PKG_REL_NS)

class ExportError(RuntimeError):

    """Erro de exporta\u00e7\u00e3o controlado."""

_EMAIL_CONFIG_CACHE: dict[str, str] | None = None

@dataclass

class FertilizanteLinha:

    nome: str

    dose_ha: str

    dose_total: str

def _template_path() -> Path:

    return Path(__file__).resolve().parent.parent / TEMPLATE_NAME

def _normalize_text(text: str) -> str:

    base = PLACEHOLDER_PATTERN.sub("", text or "")

    normalized = unicodedata.normalize("NFKD", base)

    return normalized.encode("ascii", "ignore").decode("ascii").strip().lower()

def _get_entry_text(widget) -> str:

    try:

        value = widget.get()

    except Exception:

        return ""

    return str(value).strip()

def _load_email_config() -> dict[str, str]:

    global _EMAIL_CONFIG_CACHE

    if _EMAIL_CONFIG_CACHE is not None:

        return _EMAIL_CONFIG_CACHE

    if not EMAIL_CONFIG_PATH.exists():

        raise ExportError(

            "As configura\u00e7\u00f5es de e-mail n\u00e3o foram encontradas (arquivo modelo_mail/.env ausente)."

        )

    config: dict[str, str] = {}

    try:

        linhas = EMAIL_CONFIG_PATH.read_text(encoding="utf-8").splitlines()

    except Exception as exc:

        raise ExportError("Falha ao ler o arquivo de configura\u00e7\u00e3o de e-mail.") from exc

    for linha in linhas:

        texto = linha.strip()

        if not texto or texto.startswith("#"):

            continue

        if "=" not in texto:

            continue

        chave, valor = texto.split("=", 1)

        config[chave.strip()] = valor.strip().strip('"').strip("'")

    obrigatorios = ["EMAIL_FROM", "SMTP_PASS", "SMTP_HOST", "SMTP_PORT"]

    ausentes = [item for item in obrigatorios if not config.get(item)]

    if ausentes:

        raise ExportError(

            "Configura\u00e7\u00f5es de e-mail incompletas. Verifique o arquivo modelo_mail/.env."

        )

    _EMAIL_CONFIG_CACHE = config

    return config

def _config_bool(value: str | None, default: bool = True) -> bool:

    if value is None:

        return default

    return value.strip().lower() not in {"0", "false", "no", "n"}

def _parse_recipient_list(raw_value: str) -> list[str]:

    if not raw_value:

        raise ExportError("Informe o e-mail do destinat\u00e1rio.")

    candidatos = EMAIL_SEPARATOR_PATTERN.split(raw_value)

    emails: list[str] = []

    for item in candidatos:

        email = item.strip()

        if not email:

            continue

        if not EMAIL_REGEX.fullmatch(email):

            raise ExportError(f"E-mail inv\u00e1lido: {email}")

        emails.append(email)

    if not emails:

        raise ExportError("Informe o e-mail do destinat\u00e1rio.")

    return emails

def _compose_email_body(dados: dict[str, str]) -> str:

    produtor = dados.get("produtor") or "Produtor(a)"

    municipio = dados.get("municipio") or "-"

    talhao = dados.get("talhao") or "-"

    safra = dados.get("safra") or "-"

    linhas = [

        f"Ol\u00e1, {produtor}!",

        "Segue em anexo o relat\u00f3rio gerado pelo FertiSoja, contendo a interpreta\u00e7\u00e3o da an\u00e1lise de solo e a recomenda\u00e7\u00e3o de aduba\u00e7\u00e3o e calagem para a sua \u00e1rea "

        f"({municipio} \u2013 {talhao}, {safra}).",

        "",

        "O documento apresenta:",

        "\u2022 Condi\u00e7\u00f5es gerais do solo (argila, CTC, mat\u00e9ria org\u00e2nica, etc.);",

        "\u2022 Classifica\u00e7\u00e3o dos nutrientes (macro e micronutrientes);",

        "\u2022 Recomenda\u00e7\u00e3o detalhada de calagem e fertiliza\u00e7\u00e3o, com doses por hectare e totais.",

        "",

        "Este laudo foi gerado automaticamente com base no Manual de Aduba\u00e7\u00e3o e Calagem para os Estados do RS e SC (2016) e deve ser interpretado por um Engenheiro Agr\u00f4nomo habilitado antes da aplica\u00e7\u00e3o em campo.",

        "O FertiSoja ainda est\u00e1 em fase de testes. Caso encontre diverg\u00eancias, sugest\u00f5es ou deseje validar os resultados, entre em contato com Thiago pelo WhatsApp +55 (51) 98019-1913.",

    ]

    return "\n".join(linhas)

def _build_attachment_filename(dados: dict[str, str], extension: str = ".docx") -> str:

    partes: list[str] = []

    for chave in ("produtor", "municipio", "talhao"):

        valor = dados.get(chave, "")

        if not valor:

            continue

        normalizado = _normalize_text(valor)

        normalizado = re.sub(r"[^a-z0-9]+", "_", normalizado).strip("_")

        if normalizado:

            partes.append(normalizado)

    base = "_".join(partes) if partes else "relatorio"
    ext = extension if extension.startswith(".") else f".{extension}"

    return f"Recomendacao_FertiSoja_{base}{ext}"


def _send_email_with_attachment(

    subject: str,

    body: str,

    recipients: list[str],

    attachment_path: Path,

    attachment_name: str,

    config: dict[str, str],

) -> None:

    remetente = config.get("EMAIL_FROM") or config.get("SMTP_USER")

    if not remetente:

        raise ExportError("Remetente de e-mail n\u00e3o configurado (EMAIL_FROM ou SMTP_USER).")

    msg = EmailMessage()

    msg["Subject"] = subject

    msg["From"] = remetente

    msg["To"] = ", ".join(recipients)

    msg.set_content(body, subtype="plain", charset="utf-8")

    try:

        with attachment_path.open("rb") as arquivo:

            mime_type, _ = mimetypes.guess_type(str(attachment_path))
            maintype = "application"
            subtype = "octet-stream"
            if mime_type and "/" in mime_type:
                maintype, subtype = mime_type.split("/", 1)
            msg.add_attachment(
                arquivo.read(),
                maintype=maintype,
                subtype=subtype,
                filename=attachment_name,
            )

    except Exception as exc:

        raise ExportError(f"Falha ao anexar o documento ao e-mail: {exc}") from exc

    host = config.get("SMTP_HOST", "smtp.gmail.com")

    port_raw = config.get("SMTP_PORT", "587") or "587"

    try:

        port = int(port_raw)

    except ValueError as exc:

        raise ExportError(f"Porta SMTP inv\u00e1lida: {port_raw}") from exc

    usuario = config.get("SMTP_USER") or remetente

    senha = config.get("SMTP_PASS", "")

    use_tls = _config_bool(config.get("SMTP_USE_TLS"), default=True)

    contexto = ssl.create_default_context()

    try:

        if use_tls and port != 465:

            with smtplib.SMTP(host, port) as server:

                server.ehlo()

                server.starttls(context=contexto)

                if usuario and senha:

                    server.login(usuario, senha)

                server.send_message(msg)

        else:

            with smtplib.SMTP_SSL(host, port, context=contexto) as server:

                if usuario and senha:

                    server.login(usuario, senha)

                server.send_message(msg)

    except Exception as exc:

        raise ExportError(f"Falha ao enviar o e-mail: {exc}") from exc

def _lookup_value(data: dict, *aliases: str) -> str:

    if not data:

        return ""

    normalized_targets = [normalize_key(alias) for alias in aliases]

    for chave, valor in data.items():

        key_norm = normalize_key(str(chave))

        for alvo in normalized_targets:

            if key_norm.startswith(alvo):

                return str(valor or "").strip()

    return ""

def _lookup_float(data: dict, *aliases: str) -> float | None:

    texto = _lookup_value(data, *aliases)

    return parse_float(texto)

def _format_number(valor: float) -> str:

    abs_val = abs(valor)

    if abs_val >= 1000:

        return f"{valor:.0f}"

    if abs_val >= 100:

        return f"{valor:.1f}"

    if abs_val >= 10:

        return f"{valor:.2f}"

    if abs_val >= 1:

        return f"{valor:.2f}"

    return f"{valor:.3f}"

def _format_mass(valor_kg: float, unidade: str, por_area: bool) -> str:

    unidade = (unidade or "kg").lower()

    if unidade.startswith("saca"):

        numero = valor_kg / 50.0

        sufixo = " sacas/ha" if por_area else " sacas"

    elif unidade == "t":

        numero = valor_kg / 1000.0

        sufixo = " t/ha" if por_area else " t"

    else:

        numero = valor_kg

        sufixo = " kg/ha" if por_area else " kg"

    return f"{_format_number(numero)}{sufixo}"

def _format_calcario(valor_kg: float, unidade: str, por_area: bool) -> str:

    unidade = (unidade or "kg").lower()

    if unidade.startswith("saca"):

        unidade = "t"

    if unidade not in {"kg", "t"}:

        unidade = "kg"

    return _format_mass(valor_kg, unidade, por_area)

def _format_molibdenio(valor_kg: float, por_area: bool) -> str:

    valor_g = valor_kg * 1000.0

    sufixo = " g/ha" if por_area else " g"

    return f"{_format_number(valor_g)}{sufixo}"

def _format_percent(valor: float | None) -> str:

    if valor is None:

        return ""

    return f"{valor:.2f}%"

def _format_decimal(valor: float | None, unidade: str = "") -> str:

    if valor is None:

        return ""

    texto = f"{valor:.2f}"

    return f"{texto} {unidade}".strip()

def _coletar_fertilizantes(

    ctx: AppContext,

    area_ha: float,

    unidade_ha: str,

    unidade_total: str,

) -> list[FertilizanteLinha]:

    controles = getattr(ctx, "fertilizacao_controls", None)

    if not isinstance(controles, dict):

        return []

    resultado = controles.get("ultimo_resultado")

    if resultado is None or not getattr(resultado, "produtos", None):

        return []

    linhas: list[FertilizanteLinha] = []

    area_base = max(area_ha, 0.0)

    for nome, dose_ha in resultado.produtos:

        dose_ha = max(float(dose_ha or 0.0), 0.0)

        if "molibdato" in normalize_key(nome):

            dose_ha_texto = f"{_format_number(dose_ha * 1000)} g/ha"

            total_texto = f"{_format_number(dose_ha * area_base * 1000)} g"

        else:

            dose_ha_texto = _format_mass(dose_ha, unidade_ha, por_area=True)

            total_texto = _format_mass(dose_ha * area_base, unidade_total, por_area=False)

        linhas.append(FertilizanteLinha(nome=nome, dose_ha=dose_ha_texto, dose_total=total_texto))

        if len(linhas) >= FERTILIZER_SLOTS:

            break

    return linhas

def _coletar_dados(ctx: AppContext, controles: dict) -> tuple[dict[str, str], list[FertilizanteLinha]]:
    entradas = ctx.get_entradas()
    classificacoes = ctx.get_classificacoes()
    campos_extras = controles.get("entries", {})
    info_usuario = {chave: _get_entry_text(widget) for chave, widget in campos_extras.items()}
    resultados_controles = getattr(ctx, "resultados_controls", None)
    unidade_ha_sel = "kg"
    unidade_total_sel = "kg"
    if isinstance(resultados_controles, dict):
        unidade_ha_var = resultados_controles.get("unidade_ha")
        if unidade_ha_var is not None:
            try:
                unidade_ha_sel = unidade_ha_var.get() or "kg"
            except Exception:
                unidade_ha_sel = "kg"
        unidade_total_var = resultados_controles.get("unidade_total")
        if unidade_total_var is not None:
            try:
                unidade_total_sel = unidade_total_var.get() or "kg"
            except Exception:
                unidade_total_sel = "kg"
    area_texto = _lookup_value(entradas, "Area (Ha)")
    area_float = parse_float(area_texto) or 0.0
    area_display = area_texto
    if area_display:
        area_display = f"{area_display} ha" if not area_display.lower().endswith("ha") else area_display
    argila_class = _lookup_value(classificacoes, "Classe do teor de Argila")
    ctc_float = _lookup_float(entradas, "CTC")
    mo_float = _lookup_float(entradas, "M.O")
    resposta_p = _lookup_value(classificacoes, "Fosforo (P)")
    resposta_k = _lookup_value(classificacoes, "Potassio (K)")
    def _classe(chave: str) -> str:
        return _lookup_value(classificacoes, chave)
    nutrientes = {
        "fosforo": _classe("Fosforo (P)"),
        "potassio": _classe("Potassio (K)"),
        "calcio": _classe("Calcio (Ca)"),
        "magnesio": _classe("Magnesio (Mg)"),
        "enxofre": _classe("Enxofre (S)"),
        "zinco": _classe("Zinco (Zn)"),
        "cobre": _classe("Cobre (Cu)"),
        "boro": _classe("Boro (B)"),
        "manganes": _classe("Manganes (Mn)"),
    }
    calagem = getattr(ctx, "calagem_resultado", None)
    if not isinstance(calagem, dict):
        raise ExportError("Calcule a recomendaÃ§Ã£o de calagem antes de exportar.")
    dose_t_ha = float(calagem.get("dose_t_ha") or 0.0)
    kg_total = float(calagem.get("kg_total") or 0.0)
    kg_ha = float(calagem.get("kg_ha") or dose_t_ha * 1000.0)
    prnt_usado = calagem.get("prnt")
    modo_aplicacao = calagem.get("modo") or ""
    epoca = calagem.get("epoca") or ""
    tipo_calcario = calagem.get("tipo") or ""
    adubacao_controles = getattr(ctx, "adubacao_controls", None)
    resultado_adub = None
    if isinstance(adubacao_controles, dict):
        resultado_adub = adubacao_controles.get("ultimo_resultado")
    dose_p = dose_k = dose_s = dose_mo = ""
    if resultado_adub is not None:
        totais = getattr(resultado_adub, "totais", {}) or {}
        dose_p_val = float(totais.get("P2O5_total") or 0.0)
        dose_k_val = float(totais.get("K2O_total") or 0.0)
        dose_s_val = float(totais.get("S_SO4") or 0.0)
        dose_mo_g = float(totais.get("Mo_g_ha") or 0.0)
        dose_mo_val = dose_mo_g / 1000.0
        dose_p = _format_number(dose_p_val)
        dose_k = _format_number(dose_k_val)
        dose_s = _format_number(dose_s_val)
        dose_mo = _format_number(dose_mo_val)
    dados = {
        "produtor": info_usuario.get("produtor", ""),
        "municipio": info_usuario.get("municipio", ""),
        "talhao": info_usuario.get("talhao", ""),
        "ano": info_usuario.get("ano", ""),
        "safra": info_usuario.get("safra", ""),
        "area_total": area_display,
        "argila_classe": argila_class,
        "ctc": _format_decimal(ctc_float),
        "mo": _format_percent(mo_float),
        "resposta_p": resposta_p,
        "resposta_k": resposta_k,
        "fosforo": nutrientes["fosforo"],
        "potassio": nutrientes["potassio"],
        "calcio": nutrientes["calcio"],
        "magnesio": nutrientes["magnesio"],
        "enxofre": nutrientes["enxofre"],
        "zinco": nutrientes["zinco"],
        "cobre": nutrientes["cobre"],
        "boro": nutrientes["boro"],
        "manganes": nutrientes["manganes"],
        "prnt_usado": f"{float(prnt_usado):.0f}%" if prnt_usado is not None else "",
        "dose_ha": _format_calcario(kg_ha, unidade_ha_sel, por_area=True),
        "dose_total": _format_calcario(kg_total, unidade_total_sel, por_area=False),
        "modo": modo_aplicacao,
        "epoca": epoca,
        "tipo_calcario": tipo_calcario,
        "dose_p": dose_p,
        "dose_k": dose_k,
        "dose_s": dose_s,
        "dose_mo": dose_mo,
    }
    fertilizantes = _coletar_fertilizantes(ctx, area_float, unidade_ha_sel, unidade_total_sel)
    return dados, fertilizantes

def _fill_runs_with_values(text_elements: list, valores: list[str]) -> None:

    for idx, elemento in enumerate(text_elements):

        texto = valores[idx] if idx < len(valores) else ""

        elemento.text = texto

    for restante in text_elements[len(valores):]:

        restante.text = ""

def _fill_placeholder_runs(paragraph, valores: list[str]) -> None:

    candidatos = []

    for elem in paragraph.findall(".//w:t", NS):

        texto = elem.text or ""

        if PLACEHOLDER_PATTERN.fullmatch(texto.strip()):

            candidatos.append(elem)

    _fill_runs_with_values(candidatos, valores)

def _parse_document_xml(xml_bytes: bytes) -> ET.Element:

    texto = xml_bytes.decode("utf-8")

    for prefixo, uri in re.findall(r'xmlns(?::([\w\d]+))?="([^"]+)"', texto):

        ET.register_namespace(prefixo or "", uri)

    return ET.fromstring(texto)







def _build_header_xml(include_image: bool, image_rel_id: str) -> bytes:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:v="urn:schemas-microsoft-com:vml">',
        '  <w:p>',
        '    <w:pPr><w:spacing w:after="0" w:before="0"/></w:pPr>',
        '    <w:r>',
        '      <w:pict>',
        '        <v:shapetype id="_x0000_t136" coordsize="1600,21600" o:spt="136" adj="10800" path="m@7,l@8,m@5,21600l@6,21600e">',
        '          <v:formulas>',
        '            <v:f eqn="sum #0 0 10800"/>',
        '            <v:f eqn="prod #0 2 1"/>',
        '            <v:f eqn="sum 21600 0 @1"/>',
        '            <v:f eqn="sum 0 0 @2"/>',
        '            <v:f eqn="prod 21600 1 2"/>',
        '            <v:f eqn="sum @0 0 @4"/>',
        '            <v:f eqn="sum 21600 0 @4"/>',
        '          </v:formulas>',
        '          <v:path textpathok="t" o:connecttype="custom" o:connectlocs="10800,0;0,10800;10800,21600;21600,10800" o:connectangles="270,180,90,0"/>',
        '          <v:textpath on="t" fitshape="t"/>',
        '          <v:handles>',
        '            <v:h position="#0" xrange="0,21600"/>',
        '          </v:handles>',
        '        </v:shapetype>',
        '        <v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f">',
        '          <v:formulas>',
        '            <v:f eqn="if lineDrawn pixelLineWidth 0"/>',
        '            <v:f eqn="sum @0 1 0"/>',
        '            <v:f eqn="sum 0 0 @1"/>',
        '            <v:f eqn="prod @2 1 2"/>',
        '            <v:f eqn="prod @3 21600 pixelWidth"/>',
        '            <v:f eqn="prod @3 21600 pixelHeight"/>',
        '            <v:f eqn="sum @0 0 1"/>',
        '            <v:f eqn="prod @6 1 2"/>',
        '            <v:f eqn="prod @7 21600 pixelWidth"/>',
        '            <v:f eqn="sum @8 21600 0"/>',
        '            <v:f eqn="prod @7 21600 pixelHeight"/>',
        '            <v:f eqn="sum @10 21600 0"/>',
        '          </v:formulas>',
        '          <v:path o:connecttype="rect"/>',
        '        </v:shapetype>',
        '        <v:shape id="WatermarkText" o:spid="_x0000_s2049" type="#_x0000_t136" style="position:absolute;left:0;top:0;width:800pt;height:600pt;z-index:-251658239;mso-position-horizontal:center;mso-position-horizontal-relative:page;mso-position-vertical:center;mso-position-vertical-relative:page;rotation:-35" stroked="f" fillcolor="#111111" o:allowincell="f" o:preferrelative="t">',
        '          <v:fill opacity="0.06" color2="#111111"/>',
        '          <v:textpath on="t" string="DEV Thiagoscocco UFRGS 2025" style="font-family:Arial;font-size:48pt"/>',
        '        </v:shape>',
        '      </w:pict>',
        '    </w:r>',
        '  </w:p>',
    ]
    if include_image:
        lines.extend([
            '  <w:p>',
            '    <w:pPr><w:spacing w:after="0" w:before="0"/></w:pPr>',
            '    <w:r>',
            '      <w:pict>',
            '        <v:shape id="WatermarkLogo" o:spid="_x0000_s2050" type="#_x0000_t75" style="position:absolute;left:0;top:0;width:520pt;height:520pt;z-index:-251658238;mso-position-horizontal:center;mso-position-horizontal-relative:page;mso-position-vertical:center;mso-position-vertical-relative:page" stroked="f" fillcolor="#111111" o:allowincell="f" o:preferrelative="t" wrapcoords="0 0 0 0" o:opacity2="0.15">',
            '          <v:fill opacity="0.08" color2="#111111"/>',
            f'          <v:imagedata r:id="{image_rel_id}" o:title=""/>',
            '        </v:shape>',
            '      </w:pict>',
            '    </w:r>',
            '  </w:p>',
        ])
    lines.append('</w:hdr>')
    return "\n".join(lines).encode("utf-8")
def _render_document_xml(xml_bytes: bytes, dados: dict[str, str], fertilizantes: list[FertilizanteLinha]) -> bytes:

    root = _parse_document_xml(xml_bytes)

    fertilizante_slots: dict[str, list[list[ET.Element]]] = {"names": [], "dose_ha": [], "dose_total": []}

    estado_fert = None

    for paragrafo in root.findall(".//w:body/w:p", NS):

        textos = [elem.text or "" for elem in paragrafo.findall(".//w:t", NS)]

        conteudo = "".join(textos)

        conteudo_stripped = conteudo.strip()

        normalizado = _normalize_text(conteudo)

        if conteudo_stripped == "FERTILIZANTES":

            estado_fert = "names"

            continue

        if conteudo_stripped == "Dose por Hectare":

            estado_fert = "dose_ha"

            continue

        if conteudo_stripped == "Dose Total":

            estado_fert = "dose_total"

            continue

        if FERTILIZER_PATTERN.search(conteudo_stripped):

            if estado_fert:

                elementos = [

                    elem for elem in paragrafo.findall(".//w:t", NS)

                    if FERTILIZER_PATTERN.search(elem.text or "")

                ]

                if elementos:

                    fertilizante_slots[estado_fert].append(elementos)

            continue

        if normalizado.startswith("produtor:"):

            _fill_placeholder_runs(paragrafo, [dados.get("produtor", "")])

        elif normalizado.startswith("municipio:"):

            _fill_placeholder_runs(paragrafo, [dados.get("municipio", "")])

        elif normalizado.startswith("talhao:"):

            _fill_placeholder_runs(paragrafo, [dados.get("talhao", "")])

        elif normalizado.startswith("area total:"):

            _fill_placeholder_runs(paragrafo, [dados.get("area_total", "")])

        elif normalizado.startswith("ano:"):

            _fill_placeholder_runs(paragrafo, [dados.get("ano", "")])

        elif normalizado.startswith("safra:"):

            _fill_placeholder_runs(paragrafo, [dados.get("safra", "")])

        elif normalizado.startswith("argila:"):

            classe = dados.get("argila_classe", "")

            _fill_placeholder_runs(paragrafo, [classe, ""])

            for elem in paragrafo.findall(".//w:t", NS):

                if elem.text in {" (", "(", ")", " )"}:
                    elem.text = ""
                    if elem.text in {" (", "(", ")", " )"}:

                        elem.text = ""

        elif normalizado.startswith("ctc:"):

            _fill_placeholder_runs(paragrafo, [dados.get("ctc", "")])

        elif "m.o" in normalizado:

            _fill_placeholder_runs(paragrafo, [dados.get("mo", "")])

        elif normalizado.startswith("resposta p:"):

            _fill_placeholder_runs(paragrafo, [dados.get("resposta_p", "")])

        elif normalizado.startswith("resposta k:"):

            _fill_placeholder_runs(paragrafo, [dados.get("resposta_k", "")])

        elif normalizado.startswith("fosforo:"):

            _fill_placeholder_runs(paragrafo, [dados.get("fosforo", "")])

        elif normalizado.startswith("potassio:"):

            _fill_placeholder_runs(paragrafo, [dados.get("potassio", "")])

        elif normalizado.startswith("calcio:"):

            _fill_placeholder_runs(paragrafo, [dados.get("calcio", "")])

        elif normalizado.startswith("magnesio:"):

            _fill_placeholder_runs(paragrafo, [dados.get("magnesio", "")])

        elif normalizado.startswith("enxofre:"):

            _fill_placeholder_runs(paragrafo, [dados.get("enxofre", "")])

        elif normalizado.startswith("zinco:"):

            _fill_placeholder_runs(paragrafo, [dados.get("zinco", "")])

        elif normalizado.startswith("cobre:"):

            _fill_placeholder_runs(paragrafo, [dados.get("cobre", "")])

        elif normalizado.startswith("boro:"):

            _fill_placeholder_runs(paragrafo, [dados.get("boro", "")])

        elif normalizado.startswith("manganes:"):

            _fill_placeholder_runs(paragrafo, [dados.get("manganes", "")])

        elif normalizado.startswith("prnt usado:"):

            _fill_placeholder_runs(paragrafo, [dados.get("prnt_usado", "")])

        elif normalizado.startswith("dose/ha:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_ha", "")])

        elif normalizado.startswith("dose total:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_total", "")])

        elif normalizado.startswith("modo de aplicacao:"):

            _fill_placeholder_runs(paragrafo, [dados.get("modo", "")])

        elif normalizado.startswith("epoca:"):

            _fill_placeholder_runs(paragrafo, [dados.get("epoca", "")])

        elif normalizado.startswith("tipo de calcario:"):

            _fill_placeholder_runs(paragrafo, [dados.get("tipo_calcario", "")])

        elif normalizado.startswith("p:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_p", "")])

        elif normalizado.startswith("k:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_k", "")])

        elif normalizado.startswith("s:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_s", "")])

        elif normalizado.startswith("mo:"):

            _fill_placeholder_runs(paragrafo, [dados.get("dose_mo", "")])

    for idx in range(FERTILIZER_SLOTS):

        linha = fertilizantes[idx] if idx < len(fertilizantes) else None

        nome = linha.nome if linha else ""

        dose_ha = linha.dose_ha if linha else ""

        dose_total = linha.dose_total if linha else ""

        if idx < len(fertilizante_slots["names"]):

            _fill_runs_with_values(fertilizante_slots["names"][idx], [nome])

        if idx < len(fertilizante_slots["dose_ha"]):

            _fill_runs_with_values(fertilizante_slots["dose_ha"][idx], [dose_ha])

        if idx < len(fertilizante_slots["dose_total"]):

            _fill_runs_with_values(fertilizante_slots["dose_total"][idx], [dose_total])


    sect_pr = root.find(".//w:body/w:sectPr", NS)
    if sect_pr is None:
        corpo = root.find(".//w:body", NS)
        if corpo is not None:
            sect_pr = ET.SubElement(corpo, f"{{{NS['w']}}}sectPr")
    if sect_pr is not None:
        rel_attr = f"{{{REL_NS}}}id"
        tipo_attr = f"{{{NS['w']}}}type"
        existentes = {ref.get(rel_attr) for ref in sect_pr.findall(f"{{{NS['w']}}}headerReference")}
        if HEADER_REL_ID not in existentes:
            header_ref = ET.Element(f"{{{NS['w']}}}headerReference", {tipo_attr: "default", rel_attr: HEADER_REL_ID})
            sect_pr.insert(0, header_ref)
    
    for elemento in root.findall(".//w:t", NS):

        texto = elemento.text or ""

        if PLACEHOLDER_PATTERN.fullmatch(texto.strip()):

            elemento.text = ""

        else:

            elemento.text = PLACEHOLDER_PATTERN.sub("", texto)

    buffer = io.BytesIO()

    tree = ET.ElementTree(root)

    tree.write(buffer, encoding="utf-8", xml_declaration=True, short_empty_elements=False)

    return buffer.getvalue()

def _gerar_documento_docx(modelo: Path, destino: Path, dados: dict[str, str], fertilizantes: list[FertilizanteLinha]) -> None:
    logo_bytes: bytes | None = None
    assets_dir = Path(__file__).resolve().parent.parent / 'assets'
    logo_candidates: list[Path] = []
    if assets_dir.exists():
        for candidate in assets_dir.glob('*'):
            if candidate.is_file() and candidate.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                normalized = candidate.stem.lower().replace(' ', '').replace('-', '').replace('_', '')
                if normalized == 'logothiago':
                    logo_candidates.append(candidate)
        explicit = assets_dir / 'logo thiago png'
        if explicit.exists():
            logo_candidates.append(explicit)
    if logo_candidates:
        try:
            logo_bytes = logo_candidates[0].read_bytes()
        except Exception:
            logo_bytes = None
    document_rels_bytes: bytes | None = None
    skip_files = {
        f'word/{HEADER_PART}',
        'word/_rels/header1.xml.rels',
        f'word/{HEADER_IMAGE_PATH}',
    }
    with zipfile.ZipFile(modelo, 'r') as origem:
        with zipfile.ZipFile(destino, 'w', compression=zipfile.ZIP_DEFLATED) as alvo:
            for item in origem.infolist():
                if item.filename in skip_files:
                    continue
                conteudo = origem.read(item.filename)
                if item.filename == 'word/document.xml':
                    conteudo = _render_document_xml(conteudo, dados, fertilizantes)
                if item.filename == 'word/_rels/document.xml.rels':
                    document_rels_bytes = conteudo
                    continue
                alvo.writestr(item.filename, conteudo)
            if document_rels_bytes is None:
                raise ExportError('Modelo invÃ¡lido: relacionamentos do documento ausentes.')
            rels_root = ET.fromstring(document_rels_bytes)
            existing = {rel.get('Id') for rel in rels_root.findall(f'{{{PKG_REL_NS}}}Relationship')}
            if HEADER_REL_ID not in existing:
                ET.SubElement(
                    rels_root,
                    f'{{{PKG_REL_NS}}}Relationship',
                    {
                        'Id': HEADER_REL_ID,
                        'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/header',
                        'Target': HEADER_PART,
                    },
                )
            rels_buffer = io.BytesIO()
            ET.ElementTree(rels_root).write(rels_buffer, encoding='utf-8', xml_declaration=True)
            alvo.writestr('word/_rels/document.xml.rels', rels_buffer.getvalue())
            header_xml = _build_header_xml(include_image=logo_bytes is not None, image_rel_id=HEADER_IMAGE_REL_ID)
            alvo.writestr(f'word/{HEADER_PART}', header_xml)
            header_rels_root = ET.Element(f'{{{PKG_REL_NS}}}Relationships')
            if logo_bytes is not None:
                ET.SubElement(
                    header_rels_root,
                    f'{{{PKG_REL_NS}}}Relationship',
                    {
                        'Id': HEADER_IMAGE_REL_ID,
                        'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
                        'Target': HEADER_IMAGE_PATH,
                    },
                )
                alvo.writestr(f'word/{HEADER_IMAGE_PATH}', logo_bytes)
            header_rels_buffer = io.BytesIO()
            ET.ElementTree(header_rels_root).write(header_rels_buffer, encoding='utf-8', xml_declaration=True)
            alvo.writestr('word/_rels/header1.xml.rels', header_rels_buffer.getvalue())


def _executar_envio_email(ctx: AppContext, controles: dict) -> None:

    status_var = controles.get("status_var")

    if status_var is not None:

        status_var.set("Preparando o e-mail...")

    try:

        modelo = _template_path()

        if not modelo.exists():

            raise ExportError(

                "O arquivo de modelo n\u00e3o foi encontrado no diret\u00f3rio do projeto."

            )

        dados, fertilizantes = _coletar_dados(ctx, controles)

        email_widget = controles.get("email_entry")

        destinatarios = _parse_recipient_list(_get_entry_text(email_widget))

        config = _load_email_config()

        with tempfile.TemporaryDirectory() as tmpdir:

            base_dir = Path(tmpdir)
            tmp_docx = base_dir / "fertisoja_email.docx"

            _gerar_documento_docx(modelo, tmp_docx, dados, fertilizantes)

            attachment_name = _build_attachment_filename(dados, ".docx")
            corpo_email = _compose_email_body(dados)

            _send_email_with_attachment(
                EMAIL_SUBJECT,
                corpo_email,
                destinatarios,
                tmp_docx,
                attachment_name,
                config,
            )

        mensagem = f"E-mail enviado para: {', '.join(destinatarios)}"

        if status_var is not None:

            status_var.set(mensagem)

        messagebox.showinfo("Exporta\u00e7\u00e3o", mensagem)

    except ExportError as exc:

        if status_var is not None:

            status_var.set(str(exc))

        messagebox.showerror("Exporta\u00e7\u00e3o", str(exc))

    except Exception as exc:  # pragma: no cover - fallback gen\u00e9rico

        if status_var is not None:

            status_var.set("Falha ao enviar o e-mail.")

        messagebox.showerror("Exporta\u00e7\u00e3o", f"Erro inesperado: {exc}")

def _executar_exportacao(ctx: AppContext, controles: dict) -> None:

    status_var = controles.get("status_var")

    if status_var is not None:

        status_var.set("Preparando exportação...")

    try:

        modelo = _template_path()

        if not modelo.exists():

            raise ExportError(

                "O arquivo de modelo não foi encontrado no diretório do projeto."

            )

        dados, fertilizantes = _coletar_dados(ctx, controles)

        caminho_saida = filedialog.asksaveasfilename(

            title="Salvar documento",

            defaultextension=".docx",

            filetypes=[("Documento do Word", "*.docx")],

        )

        if not caminho_saida:

            if status_var is not None:

                status_var.set("Exportação cancelada.")

            return

        destino = Path(caminho_saida)

        with tempfile.TemporaryDirectory() as tmpdir:

            tmp_docx = Path(tmpdir) / "fertisoja_exportacao.docx"

            _gerar_documento_docx(modelo, tmp_docx, dados, fertilizantes)

            shutil.copy2(tmp_docx, destino)

            mensagem = f"Documento salvo em: {destino}"

        if status_var is not None:

            status_var.set(mensagem)

        messagebox.showinfo("Exportação", mensagem)

    except ExportError as exc:

        if status_var is not None:

            status_var.set(str(exc))

        messagebox.showerror("Exportação", str(exc))

    except Exception as exc:  # pragma: no cover - fallback genérico

        if status_var is not None:

            status_var.set("Falha ao exportar o documento.")

        messagebox.showerror("Exportação", f"Erro inesperado: {exc}")

def add_tab(tabhost: TabHost, ctx: AppContext) -> None:

    heading_font = getattr(ctx, "heading_font", ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"))

    aba = tabhost.add_tab("Exporta\u00e7\u00e3o")

    outer = ctk.CTkScrollableFrame(aba, fg_color="transparent")

    outer.pack(fill="both", expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)

    outer.grid_columnconfigure(0, weight=1)

    sec_dados = make_section(outer, "DADOS DO PRODUTOR", heading_font)

    sec_dados.grid_columnconfigure(0, weight=1)

    form_card = ctk.CTkFrame(
        sec_dados,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        corner_radius=12,
    )

    form_card.grid(row=0, column=0, sticky="ew")

    form_card.grid_columnconfigure(0, weight=1, uniform="form")

    form_card.grid_columnconfigure(1, weight=1, uniform="form")

    campos: dict[str, ctk.CTkEntry] = {}

    field_layout = [
        [
            ("Produtor", "produtor", 320, "Nome completo do produtor"),
        ],
        [
            ("Munic\u00edpio", "municipio", 260, "Cidade/UF"),
            ("Talh\u00e3o", "talhao", 200, "Identifica\u00e7\u00e3o do talh\u00e3o"),
        ],
        [
            ("Ano", "ano", 140, "AAAA"),
            ("Safra", "safra", 180, "Ex.: 2023/24"),
        ],
    ]

    for row_index, group in enumerate(field_layout):

        for col_index, (rotulo, chave, largura, placeholder) in enumerate(group):

            column = col_index

            columnspan = 1

            if len(group) == 1:

                column = 0

                columnspan = 2

            field_wrapper = ctk.CTkFrame(form_card, fg_color="transparent")

            field_wrapper.grid(
                row=row_index,
                column=column,
                columnspan=columnspan,
                sticky="ew",
                padx=PADX_STANDARD,
                pady=(PADY_STANDARD if row_index == 0 else PADY_SMALL, PADY_SMALL),
            )

            field_wrapper.grid_columnconfigure(0, weight=1)

            create_label(field_wrapper, rotulo, weight="bold").pack(anchor="w", pady=(0, 2))

            entrada = create_entry_field(
                field_wrapper,
                width=largura,
                placeholder_text=placeholder,
                corner_radius=10,
                border_width=1,
                border_color=(PRIMARY_BLUE, PRIMARY_BLUE),
                fg_color=(PANEL_LIGHT, PANEL_DARK),
            )

            entrada.pack(fill="x")

            campos[chave] = entrada

    actions_card = ctk.CTkFrame(
        outer,
        fg_color=(PANEL_LIGHT, PANEL_DARK),
        corner_radius=12,
    )

    actions_card.pack(fill="x", padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))

    actions_card.grid_columnconfigure(0, weight=1)

    instrucoes = create_label(
        actions_card,
        "Informe os dados do produtor e gere o documento DOCX a partir do modelo padrão.",
        font_size=FONT_SIZE_BODY,
        weight="normal",
        anchor="w",
        justify="left",
        wraplength=520,
    )

    instrucoes.grid(row=0, column=0, sticky="ew", padx=PADX_STANDARD, pady=(PADY_STANDARD, PADY_SMALL))

    status_var = ctk.StringVar(value="Pronto para exportar.")

    status_label = create_label(
        actions_card,
        "",
        font_size=FONT_SIZE_BODY,
        weight="normal",
        anchor="w",
        justify="left",
        wraplength=520,
    )

    status_label.configure(textvariable=status_var, text_color=SUCCESS_GREEN)

    status_label.grid(row=1, column=0, sticky="ew", padx=PADX_STANDARD)

    controles = {"entries": campos}  # preenchido abaixo

    botao = create_primary_button(
        actions_card,
        "Gerar DOCX",
        lambda: _executar_exportacao(ctx, controles),
    )

    botao.grid(row=2, column=0, padx=PADX_STANDARD, pady=(PADY_SMALL, 0), sticky="ew")

    botao_email = create_primary_button(
        actions_card,
        "Enviar Por Email",
        lambda: _executar_envio_email(ctx, controles),
    )

    botao_email.grid(row=3, column=0, padx=PADX_STANDARD, pady=(PADY_SMALL, PADY_SMALL), sticky="ew")

    email_label = create_label(
        actions_card,
        "E-mail do destinat\u00e1rio",
        weight="bold",
        anchor="w",
    )

    email_label.grid(row=4, column=0, sticky="ew", padx=PADX_STANDARD, pady=(PADY_SMALL, 2))

    email_entry = create_entry_field(
        actions_card,
        width=ENTRY_WIDTH_STANDARD,
        placeholder_text="ex.: produtor@email.com",
        corner_radius=10,
        border_width=1,
        border_color=(PRIMARY_BLUE, PRIMARY_BLUE),
        fg_color=(PANEL_LIGHT, PANEL_DARK),
    )

    email_entry.grid(row=5, column=0, sticky="ew", padx=PADX_STANDARD, pady=(0, PADY_STANDARD))

    controles["status_var"] = status_var
    controles["email_entry"] = email_entry

    ctx.exportacao_controls = controles


__all__ = ["add_tab"]

