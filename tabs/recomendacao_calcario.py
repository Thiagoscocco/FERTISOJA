from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

PH_REF_SOJA = 6.0
PH_NEED_THRESHOLD = 5.5
PH_SEVERE_PD = 5.2
ALPCT_RESTR_THRESHOLD = 30.0
V_LOW_PD = 40.0
V_MIN_NO_LIME = 65.0
ALPCT_MAX_NO_LIME = 10.0
MG_LOW_THRESHOLD = 1.0
SUPERFICIAL_LIMIT = 5.0

TABELA_SMP_FIXA = {
    4.4: 21.0, 4.5: 17.3, 4.6: 15.1, 4.7: 13.3, 4.8: 11.9, 4.9: 10.7,
    5.0: 9.9, 5.1: 9.1, 5.2: 8.3, 5.3: 7.5, 5.4: 6.8, 5.5: 6.1,
    5.6: 5.4, 5.7: 4.8, 5.8: 4.2, 5.9: 3.7, 6.0: 3.2, 6.1: 2.7,
    6.2: 2.2, 6.3: 1.8, 6.4: 1.4, 6.5: 1.1, 6.6: 0.8, 6.7: 0.5,
    6.8: 0.3, 6.9: 0.2, 7.0: 0.0,
}


def _f(x, default=None):
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(',', '.')
    if s == "":
        return default
    try:
        return float(s)
    except Exception:
        return default


def make_section(parent, title, font):
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=(8, 0))
    header = ctk.CTkLabel(frame, text=title, font=font, anchor="w")
    header.pack(anchor="w", padx=10, pady=(10, 6))
    body = ctk.CTkFrame(frame, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return body


def add_tab(tabhost, ctx):
    titulo_font = ctk.CTkFont(size=13, weight="bold")
    texto_font = ctk.CTkFont(size=11)

    aba = tabhost.add_tab("Recomendação de Calcário")
    outer = ctk.CTkFrame(aba, fg_color="transparent")
    outer.pack(fill="both", expand=True, padx=16, pady=16)

    sec_inputs = make_section(outer, "ENTRADAS (0-20 cm)", titulo_font)
    sec_inputs.grid_columnconfigure(1, weight=1)
    sec_inputs.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(sec_inputs, text="Sistema de manejo:", font=texto_font).grid(row=0, column=0, sticky="w", pady=4)
    sistema_var = ctk.StringVar(value="PD consolidado")
    sistema_cb = ctk.CTkComboBox(sec_inputs, values=["Convencional", "Implantação do PD", "PD consolidado"], state="readonly", variable=sistema_var, width=180)
    sistema_cb.grid(row=0, column=1, sticky="w", padx=6)

    ctk.CTkLabel(sec_inputs, text="V%:", font=texto_font).grid(row=1, column=0, sticky="w", pady=4)
    v_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=v_var, width=120).grid(row=1, column=1, sticky="w", padx=6)

    ctk.CTkLabel(sec_inputs, text="Al%:", font=texto_font).grid(row=1, column=2, sticky="w", pady=4)
    alpct_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=alpct_var, width=120).grid(row=1, column=3, sticky="w", padx=6)

    ctk.CTkLabel(sec_inputs, text="PRNT (%):", font=texto_font).grid(row=2, column=0, sticky="w", pady=4)
    prnt_var = ctk.StringVar(value="100")
    ctk.CTkEntry(sec_inputs, textvariable=prnt_var, width=120).grid(row=2, column=1, sticky="w", padx=6)

    ctk.CTkLabel(sec_inputs, text="Al trocável (cmolc/dm³):", font=texto_font).grid(row=2, column=2, sticky="w", pady=4)
    altroc_var = ctk.StringVar()
    ctk.CTkEntry(sec_inputs, textvariable=altroc_var, width=120).grid(row=2, column=3, sticky="w", padx=6)

    mid_row = ctk.CTkFrame(outer, fg_color="transparent")
    mid_row.pack(fill="both", expand=True, padx=10, pady=(6, 10))

    results_box = make_section(mid_row, "RESULTADOS", titulo_font)
    results_box.pack_propagate(False)
    resultados_frame = ctk.CTkFrame(results_box, fg_color="transparent")
    resultados_frame.pack(fill="both", expand=True)

    lbl_qtha_val = ctk.CTkLabel(resultados_frame, text="", width=120, anchor="w", font=texto_font)
    lbl_total_val = ctk.CTkLabel(resultados_frame, text="", width=120, anchor="w", font=texto_font)

    linha1 = ctk.CTkFrame(resultados_frame, fg_color="transparent")
    linha1.pack(fill="x", pady=4)
    ctk.CTkLabel(linha1, text="t/ha", font=texto_font).pack(side="right")
    lbl_qtha_val.pack(side="right", padx=6)
    ctk.CTkLabel(linha1, text="Dose", font=texto_font).pack(side="right", padx=(0, 6))

    linha2 = ctk.CTkFrame(resultados_frame, fg_color="transparent")
    linha2.pack(fill="x", pady=4)
    ctk.CTkLabel(linha2, text="t no total", font=texto_font).pack(side="right")
    lbl_total_val.pack(side="right", padx=6)
    ctk.CTkLabel(linha2, text="Total", font=texto_font).pack(side="right", padx=(0, 6))

    rec_box = make_section(mid_row, "RECOMENDAÇÕES TÉCNICAS", titulo_font)
    val_modo = ctk.CTkLabel(rec_box, text="", anchor="w", justify="left", wraplength=420, font=texto_font)
    val_modo.pack(fill="x", pady=2)
    val_epoca = ctk.CTkLabel(rec_box, text="", anchor="w", justify="left", wraplength=420, font=texto_font)
    val_epoca.pack(fill="x", pady=2)
    val_tipo = ctk.CTkLabel(rec_box, text="", anchor="w", justify="left", wraplength=420, font=texto_font)
    val_tipo.pack(fill="x", pady=2)

    btn_calc = ctk.CTkButton(outer, text="CALCULAR")
    btn_calc.pack(pady=(4, 12))

    def calcular():
        ent = ctx.get_entradas() if hasattr(ctx, 'get_entradas') else {}
        smp = _f(ent.get('Índice SMP'))
        ph = _f(ent.get('pH (água)'))
        argila = _f(ent.get('Argila (%)'))
        mo = _f(ent.get('M.O. (%)'))
        area = _f(ent.get('Área (Ha)'), 0.0)
        mg = _f(ent.get('Mg (cmolc/dm³)'))

        v_pct = _f(v_var.get())
        alpct = _f(alpct_var.get())
        prnt = _f(prnt_var.get(), 100.0)
        al_troc = _f(altroc_var.get())

        if v_pct is not None and alpct is not None and v_pct >= V_MIN_NO_LIME and alpct < ALPCT_MAX_NO_LIME:
            qtha = 0
            total = 0
            modo = "Sem necessidade"
            epoca = ""
        else:
            if ph is not None and ph >= PH_NEED_THRESHOLD:
                qtha = 0
                total = 0
                modo = "Sem necessidade"
                epoca = ""
            else:
                if argila is not None and argila < 20:
                    dose_nc = -0.516 + 0.805 * (mo or 0) + 2.435 * (al_troc or 0)
                    qtha = max(0, dose_nc)
                else:
                    qtha = TABELA_SMP_FIXA.get(round(smp, 1), 0)
                if sistema_var.get() == "PD consolidado":
                    if (alpct is not None and alpct >= ALPCT_RESTR_THRESHOLD) or (ph is not None and ph <= PH_SEVERE_PD):
                        modo = "Incorporar"
                    else:
                        modo = "Superficial"
                        qtha *= 0.25
                else:
                    modo = "Incorporar"
                qtha = qtha * (100.0 / prnt)
                total = qtha * (area or 0)
                if modo == "Incorporar":
                    epoca = "Aplicar e incorporar até 3 meses antes da semeadura."
                else:
                    epoca = "Aplicar superficialmente em PD, até 3 meses antes da semeadura."

        lbl_qtha_val.configure(text=f"{qtha:.2f}")
        lbl_total_val.configure(text=f"{total:.2f}")
        val_modo.configure(text=f"Modo: {modo}")
        val_epoca.configure(text=f"Época: {epoca}")
        if mg is not None and mg < MG_LOW_THRESHOLD:
            val_tipo.configure(text="Calcário dolomítico")
        else:
            val_tipo.configure(text="Calcítico ou dolomítico")

    btn_calc.configure(command=calcular)

    try:
        from PIL import Image
        base_dir = Path(__file__).resolve().parent
        logo_path = base_dir / ".." / "assets" / "logo.png"
        if not logo_path.exists():
            logo_path = base_dir / "logo.png"
        img = Image.open(logo_path)
        img.thumbnail((120, 60))
        logo = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        holder = ctk.CTkLabel(outer, image=logo, text="")
        holder.image = logo
        holder.pack(anchor="se", padx=10, pady=10)
    except Exception:
        pass
