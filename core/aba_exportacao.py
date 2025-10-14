# -*- coding: utf-8 -*-



from __future__ import annotations







import io



import re



import shutil



import tempfile



import unicodedata



import xml.etree.ElementTree as ET



import zipfile



from dataclasses import dataclass



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











class ExportError(RuntimeError):



    """Erro de exporta\u00e7\u00e3o controlado."""











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







    argila_float = _lookup_float(entradas, "Argila")



    argila_class = _lookup_value(classificacoes, "Classe do teor de Argila")



    ctc_float = _lookup_float(entradas, "CTC")



    mo_float = _lookup_float(entradas, "M.O")







    resposta_p = _lookup_value(classificacoes, "Fosforo (P)")



    resposta_k = _lookup_value(classificacoes, "Potassio (K)")







    nutrientes = {



        "fosforo": _lookup_value(entradas, "P (mg"),



        "potassio": _lookup_value(entradas, "K (mg"),



        "calcio": _lookup_value(entradas, "Ca (cmol"),



        "magnesio": _lookup_value(entradas, "Mg (cmol"),



        "enxofre": _lookup_value(entradas, "S (mg"),



        "zinco": _lookup_value(entradas, "Zn (mg"),



        "cobre": _lookup_value(entradas, "Cu (mg"),



        "boro": _lookup_value(entradas, "B (mg"),



        "manganes": _lookup_value(entradas, "Mn (mg"),



    }







    calagem = getattr(ctx, "calagem_resultado", None)



    if not isinstance(calagem, dict):



                    mensagem = (



                        f"Não foi possível converter para PDF ({exc}).\n"



                        f"O documento em DOCX foi salvo em: {destino_docx}"



                    )



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



        dose_p = _format_mass(dose_p_val, "kg", por_area=True)



        dose_k = _format_mass(dose_k_val, "kg", por_area=True)



        dose_s = _format_mass(dose_s_val, "kg", por_area=True)



        dose_mo = _format_molibdenio(dose_mo_val, por_area=True)







    dados = {



        "produtor": info_usuario.get("produtor", ""),



        "municipio": info_usuario.get("municipio", ""),



        "talhao": info_usuario.get("talhao", ""),



        "ano": info_usuario.get("ano", ""),



        "safra": info_usuario.get("safra", ""),



        "area_total": area_display,



        "argila_valor": _format_percent(argila_float) if argila_float is not None else "",



        "argila_class": argila_class,



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



            classe = dados.get("argila_class", "")



            _fill_placeholder_runs(paragrafo, [dados.get("argila_valor", ""), classe])



            if not classe:



                for elem in paragrafo.findall(".//w:t", NS):



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



    with zipfile.ZipFile(modelo, "r") as origem:



        with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as alvo:



            for item in origem.infolist():



                conteudo = origem.read(item.filename)



                if item.filename == "word/document.xml":



                    conteudo = _render_document_xml(conteudo, dados, fertilizantes)



                alvo.writestr(item.filename, conteudo)











def _converter_para_pdf(origem_docx: Path, destino_pdf: Path) -> None:



    try:



        from docx2pdf import convert



    except ImportError as exc:  # pragma: no cover - depende do ambiente do usu\u00e1rio



        raise ExportError(



            "A biblioteca 'docx2pdf' n\u00e3o est\u00e1 instalada. "



            "Instale-a com 'pip install docx2pdf' para gerar o PDF."



        ) from exc



    try:



        convert(str(origem_docx), str(destino_pdf))



    except Exception as exc:  # pragma: no cover - envolve automa\u00e7\u00e3o externa



        raise ExportError(f"Falha ao converter o DOCX em PDF: {exc}") from exc











def _executar_exportacao(ctx: AppContext, controles: dict) -> None:



    status_var = controles.get("status_var")



    if status_var is not None:



        status_var.set("Preparando exporta\u00e7\u00e3o...")







    try:



        modelo = _template_path()



        if not modelo.exists():



            raise ExportError(



                "O arquivo de modelo n\u00e3o foi encontrado no diret\u00f3rio do projeto."



            )







        dados, fertilizantes = _coletar_dados(ctx, controles)



        caminho_saida = filedialog.asksaveasfilename(



            title="Salvar documento",



            defaultextension=".pdf",



            filetypes=[("PDF", "*.pdf"), ("Documento do Word", "*.docx")],



        )



        if not caminho_saida:



            if status_var is not None:



                status_var.set("Exporta\u00e7\u00e3o cancelada.")



            return







        destino = Path(caminho_saida)



        salvar_pdf = destino.suffix.lower() == ".pdf"



        destino_docx = destino if not salvar_pdf else destino.with_suffix(".docx")







        with tempfile.TemporaryDirectory() as tmpdir:



            tmp_docx = Path(tmpdir) / "fertisoja_exportacao.docx"



            _gerar_documento_docx(modelo, tmp_docx, dados, fertilizantes)



            if salvar_pdf:



                try:



                    _converter_para_pdf(tmp_docx, destino)



                    mensagem = f"Documento salvo em: {destino}"



                except ExportError as exc:
                    shutil.copy2(tmp_docx, destino_docx)
                    mensagem = (
                        f"Não foi possível converter para PDF ({exc}).\n"
                        f"O documento em DOCX foi salvo em: {destino_docx}"
                    )



                    mensagem = (

                        f"Não foi possível converter para PDF ({exc}).\n"

                        f"O documento em DOCX foi salvo em: {destino_docx}"

                    )

                    ) from exc



            else:



                shutil.copy2(tmp_docx, destino_docx)



                mensagem = f"Documento salvo em: {destino_docx}"







        if status_var is not None:



            status_var.set(mensagem)



        messagebox.showinfo("Exporta\u00e7\u00e3o", mensagem)



    except ExportError as exc:



        if status_var is not None:



            status_var.set(str(exc))



        messagebox.showerror("Exporta\u00e7\u00e3o", str(exc))



    except Exception as exc:  # pragma: no cover - fallback gen\u00e9rico



        if status_var is not None:



            status_var.set("Falha ao exportar o documento.")



        messagebox.showerror("Exporta\u00e7\u00e3o", f"Erro inesperado: {exc}")











def add_tab(tabhost: TabHost, ctx: AppContext) -> None:



    heading_font = getattr(ctx, "heading_font", ctk.CTkFont(size=FONT_SIZE_HEADING, weight="bold"))



    aba = tabhost.add_tab("EXPORTA\u00c7\u00c3O")



    outer = ctk.CTkScrollableFrame(aba, fg_color="transparent")



    outer.pack(fill="both", expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)



    outer.grid_columnconfigure(0, weight=1)







    sec_dados = make_section(outer, "DADOS DO PRODUTOR", heading_font)



    sec_dados.grid_columnconfigure(0, weight=0)



    sec_dados.grid_columnconfigure(1, weight=1)







    campos: dict[str, ctk.CTkEntry] = {}



    linhas = [



        ("Produtor", "produtor", ENTRY_WIDTH_STANDARD),



        ("Munic\u00edpio", "municipio", ENTRY_WIDTH_STANDARD),



        ("Talh\u00e3o", "talhao", ENTRY_WIDTH_STANDARD),



        ("Ano", "ano", ENTRY_WIDTH_SMALL),



        ("Safra", "safra", ENTRY_WIDTH_SMALL),



    ]



    for idx, (rotulo, chave, largura) in enumerate(linhas):



        create_label(sec_dados, rotulo, weight="bold").grid(row=idx, column=0, sticky="w", pady=PADY_SMALL, padx=(0, PADX_MICRO))



        entrada = create_entry_field(sec_dados, width=largura)



        entrada.grid(row=idx, column=1, sticky="ew", pady=PADY_SMALL, padx=(0, PADX_SMALL))



        campos[chave] = entrada







    instrucoes = create_label(



        outer,



        "Informe os dados do produtor e gere o PDF a partir do modelo padr\u00e3o.",



        font_size=FONT_SIZE_BODY,



        weight="normal",



        anchor="w",



        justify="left",



        wraplength=520,



    )



    instrucoes.pack(fill="x", pady=(PADY_STANDARD, PADY_SMALL), padx=PADX_STANDARD)







    status_var = ctk.StringVar(value="Pronto para exportar.")



    status_label = create_label(



        outer,



        "",



        font_size=FONT_SIZE_BODY,



        weight="normal",



        anchor="w",



        justify="left",



        wraplength=520,



    )



    status_label.configure(textvariable=status_var, text_color=SUCCESS_GREEN)



    status_label.pack(fill="x", padx=PADX_STANDARD, pady=(0, PADY_SMALL))







    controles = {"entries": campos}  # preenchido abaixo







    botao = create_primary_button(



        outer,



        "Gerar PDF",



        lambda: _executar_exportacao(ctx, controles),



    )



    botao.pack(pady=(PADY_SMALL, PADY_STANDARD))







    controles["status_var"] = status_var



    ctx.exportacao_controls = controles











__all__ = ["add_tab"]