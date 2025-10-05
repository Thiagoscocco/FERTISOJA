import customtkinter as ctk
from pathlib import Path
from PIL import Image

from core.fonts import aplicar_fonte_global
from core.context import AppContext, TabHost, carregar_abas_externas
from core import calculo


def make_section(parent, title, heading_font):
    wrapper = ctk.CTkFrame(parent)
    wrapper.pack(fill="x", pady=(8, 0))
    header = ctk.CTkLabel(wrapper, text=title, font=heading_font, anchor="w")
    header.pack(anchor="w", padx=10, pady=(10, 6))
    body = ctk.CTkFrame(wrapper, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return body


def add_value_row(parent, text, store):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=3)
    label = ctk.CTkLabel(row, text=f"{text}:")
    label.pack(side="left")
    value = ctk.CTkLabel(row, text="", anchor="w")
    value.pack(side="left", padx=10)
    store[text] = value


janela = ctk.CTk()
janela.title("Fertisoja")
largura = 840
altura = 650
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
pos_x = (largura_tela // 2) - (largura // 2)
pos_y = (altura_tela // 2) - (altura // 2)
janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
janela.resizable(False, False)

_default_font, heading_font = aplicar_fonte_global(janela)

cultivo_var = ctk.StringVar(value="1º Cultivo")
calculo.ligar_cultivo_var(cultivo_var)

campos = calculo.campos
labels_classificacao = calculo.labels_classificacao
labels_resultado = calculo.labels_resultado

tabview = ctk.CTkTabview(janela)
tabview.pack(fill="both", expand=True, padx=16, pady=16)
tabhost = TabHost(tabview)

aba_entrada = tabhost.add_tab('Dados da análise de Solo')
aba_entrada.grid_columnconfigure(0, weight=1)
aba_entrada.grid_rowconfigure(0, weight=1)
aba_entrada.grid_rowconfigure(1, weight=0)

conteudo = ctk.CTkFrame(aba_entrada, fg_color="transparent")
conteudo.grid(row=0, column=0, sticky="nsew")
conteudo.grid_columnconfigure(0, weight=1)
conteudo.grid_columnconfigure(1, weight=0)

col_esq = ctk.CTkFrame(conteudo, fg_color="transparent")
col_esq.grid(row=0, column=0, sticky="nsew")

col_dir = ctk.CTkFrame(conteudo, fg_color="transparent")
col_dir.grid(row=0, column=1, sticky="ne", padx=(20, 0))

sec1 = make_section(col_esq, "INFORMAÇÕES DA PRODUÇÃO", heading_font)
sec1.grid_columnconfigure(1, weight=1)
sec1.grid_columnconfigure(3, weight=1)

ctk.CTkLabel(sec1, text="Produtividade esperada (T/Ha)").grid(row=0, column=0, sticky="w", pady=4)
entrada = ctk.CTkEntry(sec1, width=120)
entrada.grid(row=0, column=1, sticky="w", padx=6)
campos['Produtividade esperada'] = entrada

ctk.CTkLabel(sec1, text="Área (Ha)").grid(row=0, column=2, sticky="w", pady=4)
entrada_area = ctk.CTkEntry(sec1, width=100)
entrada_area.grid(row=0, column=3, sticky="w", padx=6)
campos['Área (Ha)'] = entrada_area

ctk.CTkLabel(sec1, text="Cultivo").grid(row=1, column=0, sticky="w", pady=(6, 0))
radio_frame = ctk.CTkFrame(sec1, fg_color="transparent")
radio_frame.grid(row=1, column=1, columnspan=3, sticky="w", pady=(6, 0))
ctk.CTkRadioButton(radio_frame, text="1º Cultivo", variable=cultivo_var, value="1º Cultivo").pack(side="left", padx=(0, 16))
ctk.CTkRadioButton(radio_frame, text="2º Cultivo", variable=cultivo_var, value="2º Cultivo").pack(side="left")

sec2 = make_section(col_esq, "CONDIÇÕES DO SOLO", heading_font)
sec2.grid_columnconfigure(1, weight=1)

linha = 0
for nome in ['Índice SMP', 'Argila (%)', 'CTC (cmolc/dm³)', 'M.O. (%)', 'pH (água)']:
    ctk.CTkLabel(sec2, text=nome).grid(row=linha, column=0, sticky="w", pady=4)
    entrada = ctk.CTkEntry(sec2, width=120)
    entrada.grid(row=linha, column=1, sticky="w", padx=6)
    campos[nome] = entrada
    linha += 1

sec3 = make_section(col_esq, "TEOR DE NUTRIENTES", heading_font)
sec3.grid_columnconfigure(0, weight=1)
sec3.grid_columnconfigure(1, weight=1)

linha = 0
for nome in ['P (mg/dm³)', 'K (mg/dm³)', 'S (mg/dm³)', 'Ca (cmolc/dm³)', 'Mg (cmolc/dm³)', 'Zn (mg/dm³)', 'Cu (mg/dm³)', 'B (mg/dm³)', 'Mn (mg/dm³)']:
    ctk.CTkLabel(sec3, text=nome).grid(row=linha, column=0, sticky="w", pady=3)
    entrada = ctk.CTkEntry(sec3, width=120)
    entrada.grid(row=linha, column=1, sticky="w", padx=6)
    campos[nome] = entrada
    linha += 1

rodape = ctk.CTkFrame(aba_entrada, fg_color="transparent")
rodape.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 16))
rodape.grid_columnconfigure(0, weight=1)
ctk.CTkButton(rodape, text="CALCULAR", command=calculo.calcular).grid(row=0, column=0, sticky="e")

logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
try:
    imagem = Image.open(logo_path)
    max_w = 220
    if imagem.width > max_w:
        ratio = max_w / imagem.width
        new_size = (int(imagem.width * ratio), int(imagem.height * ratio))
        imagem = imagem.resize(new_size, Image.LANCZOS)
    logo = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(imagem.width, imagem.height))
    ctk.CTkLabel(col_dir, image=logo, text="").pack(anchor="ne")
except Exception:
    ctk.CTkLabel(col_dir, text="(imagem não carregada)").pack(anchor="ne")

ctx = AppContext(
    janela=janela,
    abas=tabhost,
    campos=campos,
    labels_classificacao=labels_classificacao,
    labels_resultado=labels_resultado,
    cultivo_var=cultivo_var,
    calcular=calculo.calcular,
)

carregar_abas_externas(tabhost, ctx)

aba_class = tabhost.add_tab('Condições do Solo')
frame_class = ctk.CTkFrame(aba_class, fg_color="transparent")
frame_class.pack(fill="both", expand=True, padx=16, pady=16)

sec_class_prop = make_section(frame_class, "PROPRIEDADES GERAIS DO SOLO", heading_font)
for nome in ['Classe do teor de Argila', 'CTC', 'M.O.']:
    add_value_row(sec_class_prop, nome, labels_classificacao)

sec_class_macro = make_section(frame_class, "MACRONUTRIENTES", heading_font)
for nome in ['Fósforo (P)', 'Potássio (K)', 'Cálcio (Ca)', 'Magnésio (Mg)', 'Enxofre (S)']:
    add_value_row(sec_class_macro, nome, labels_classificacao)

sec_class_micro = make_section(frame_class, "MICRONUTRIENTES", heading_font)
for nome in ['Zinco (Zn)', 'Cobre (Cu)', 'Boro (B)', 'Manganês (Mn)']:
    add_value_row(sec_class_micro, nome, labels_classificacao)

aba_resultado = tabhost.add_tab('Recomendações')
frame_result = ctk.CTkFrame(aba_resultado, fg_color="transparent")
frame_result.pack(fill="both", expand=True, padx=16, pady=16)

sec_result_calc = make_section(frame_result, "CALCÁRIO", heading_font)
for nome in ['Calcário (PRNT 100%)']:
    add_value_row(sec_result_calc, nome, labels_resultado)

sec_result_macro = make_section(frame_result, "MACRONUTRIENTES", heading_font)
for nome in ['Fósforo (P2O5)', 'Potássio (K2O)', 'Enxofre (S)']:
    add_value_row(sec_result_macro, nome, labels_resultado)

sec_result_micro = make_section(frame_result, "MICRONUTRIENTES", heading_font)
for nome in ['Molibdênio (Mo)']:
    add_value_row(sec_result_micro, nome, labels_resultado)

janela.mainloop()
