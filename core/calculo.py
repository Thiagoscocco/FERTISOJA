from __future__ import annotations

from typing import Iterable
from tkinter import messagebox

TABELA_SMP_FIXA = {
    4.4: 21.0, 4.5: 17.3, 4.6: 15.1, 4.7: 13.3, 4.8: 11.9, 4.9: 10.7,
    5.0: 9.9, 5.1: 9.1, 5.2: 8.3, 5.3: 7.5, 5.4: 6.8, 5.5: 6.1,
    5.6: 5.4, 5.7: 4.8, 5.8: 4.2, 5.9: 3.7, 6.0: 3.2, 6.1: 2.7,
    6.2: 2.2, 6.3: 1.8, 6.4: 1.4, 6.5: 1.1, 6.6: 0.8, 6.7: 0.5,
    6.8: 0.3, 6.9: 0.2, 7.0: 0.0,
}

recom_p2o5: float | None = None
recom_k2o: float | None = None

campos: dict[str, object] = {}
labels_classificacao: dict[str, object] = {}
labels_resultado: dict[str, object] = {}
_cultivo_var = None


def ligar_cultivo_var(var):
    global _cultivo_var
    _cultivo_var = var


def classificar_parametro(valor, limites):
    for faixa, limite in limites.items():
        if eval(limite):
            return faixa
    return "Desconhecido"


def _valor_widget(widget):
    try:
        valor = widget.get()
    except Exception:
        return ""
    return str(valor).strip().replace(",", ".")


def _float_obrigatorio(chave):
    widget = campos.get(chave)
    if widget is None:
        raise ValueError(f"Campo '{chave}' não encontrado")
    raw = _valor_widget(widget)
    if raw == "":
        raise ValueError(f"Campo '{chave}' vazio")
    return float(raw)


def _float_opcional(chaves: Iterable[str], default=0.0):
    for chave in chaves:
        widget = campos.get(chave)
        if widget is None:
            continue
        raw = _valor_widget(widget)
        if raw == "":
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return default


def calcular():
    global recom_p2o5, recom_k2o
    if _cultivo_var is None:
        return False
    try:
        smp = _float_obrigatorio('Índice SMP')
        produtividade = _float_obrigatorio('Produtividade esperada')
        cultivo = _cultivo_var.get()

        fosforo = _float_opcional(['Fósforo (mg/dm³)', 'P (mg/dm³)'], default=0.0)
        potassio = _float_opcional(['Potássio (mg/dm³)', 'K (mg/dm³)'], default=0.0)
        enxofre = _float_opcional(['Enxofre (mg/dm³)', 'S (mg/dm³)'], default=0.0)

        argila = _float_obrigatorio('Argila (%)')
        ctc = _float_obrigatorio('CTC (cmolc/dm³)')
        ph = _float_obrigatorio('pH (água)')

        if argila > 60:
            classe_argila = 1
        elif argila > 40:
            classe_argila = 2
        elif argila > 20:
            classe_argila = 3
        else:
            classe_argila = 4

        if classe_argila == 1:
            class_p = classificar_parametro(fosforo, {
                "Muito Baixo": "valor <= 3",
                "Baixo": "3 < valor <= 6",
                "Médio": "6 < valor <= 9",
                "Alto": "9 < valor <= 18",
                "Muito Alto": "valor > 18",
            })
        elif classe_argila == 2:
            class_p = classificar_parametro(fosforo, {
                "Muito Baixo": "valor <= 4",
                "Baixo": "4 < valor <= 8",
                "Médio": "8 < valor <= 12",
                "Alto": "12 < valor <= 24",
                "Muito Alto": "valor > 24",
            })
        elif classe_argila == 3:
            class_p = classificar_parametro(fosforo, {
                "Muito Baixo": "valor <= 6",
                "Baixo": "6 < valor <= 12",
                "Médio": "12 < valor <= 18",
                "Alto": "18 < valor <= 36",
                "Muito Alto": "valor > 36",
            })
        else:
            class_p = classificar_parametro(fosforo, {
                "Muito Baixo": "valor <= 10",
                "Baixo": "10 < valor <= 20",
                "Médio": "20 < valor <= 30",
                "Alto": "30 < valor <= 60",
                "Muito Alto": "valor > 60",
            })

        if ctc <= 7.5:
            class_k = classificar_parametro(potassio, {
                "Muito Baixo": "valor <= 20",
                "Baixo": "20 < valor <= 40",
                "Médio": "40 < valor <= 60",
                "Alto": "valor > 60",
            })
        elif ctc <= 15:
            class_k = classificar_parametro(potassio, {
                "Muito Baixo": "valor <= 30",
                "Baixo": "30 < valor <= 60",
                "Médio": "60 < valor <= 90",
                "Alto": "90 < valor <= 180",
                "Muito Alto": "valor > 180",
            })
        elif ctc <= 30:
            class_k = classificar_parametro(potassio, {
                "Muito Baixo": "valor <= 40",
                "Baixo": "40 < valor <= 80",
                "Médio": "80 < valor <= 120",
                "Alto": "120 < valor <= 240",
                "Muito Alto": "valor > 240",
            })
        else:
            class_k = classificar_parametro(potassio, {
                "Muito Baixo": "valor <= 45",
                "Baixo": "45 < valor <= 90",
                "Médio": "90 < valor <= 135",
                "Alto": "135 < valor <= 270",
                "Muito Alto": "valor > 270",
            })

        class_ctc = classificar_parametro(ctc, {
            "Baixa": "valor <= 7.5",
            "Média": "7.5 < valor <= 15",
            "Alta": "15 < valor <= 30",
            "Muito Alta": "valor > 30",
        })
        class_mo = classificar_parametro(_float_opcional(['M.O. (%)'], default=0), {
            "Baixa": "valor <= 2.5",
            "Média": "2.5 < valor <= 5",
            "Alta": "valor > 5",
        })
        class_ca = classificar_parametro(_float_opcional(['Ca (cmolc/dm³)'], default=0), {
            "Baixo": "valor < 2",
            "Médio": "2 <= valor <= 4",
            "Alto": "valor > 4",
        })
        class_mg = classificar_parametro(_float_opcional(['Mg (cmolc/dm³)'], default=0), {
            "Baixo": "valor < 0.5",
            "Médio": "0.5 <= valor <= 1",
            "Alto": "valor > 1",
        })
        class_s = classificar_parametro(enxofre, {
            "Baixo": "valor < 2",
            "Médio": "2 <= valor <= 5",
            "Alto": "valor > 5",
        })
        class_zn = classificar_parametro(_float_opcional(['Zn (mg/dm³)'], default=0), {
            "Baixo": "valor < 0.2",
            "Médio": "0.2 <= valor <= 0.5",
            "Alto": "valor > 0.5",
        })
        class_cu = classificar_parametro(_float_opcional(['Cu (mg/dm³)'], default=0), {
            "Baixo": "valor < 2",
            "Médio": "2 <= valor <= 4",
            "Alto": "valor > 4",
        })
        class_b = classificar_parametro(_float_opcional(['B (mg/dm³)'], default=0), {
            "Baixo": "valor <= 0.1",
            "Médio": "0.1 < valor <= 0.3",
            "Alto": "valor > 0.3",
        })
        class_mn = classificar_parametro(_float_opcional(['Mn (mg/dm³)'], default=0), {
            "Baixo": "valor < 2.5",
            "Médio": "2.5 <= valor <= 5",
            "Alto": "valor > 5",
        })

        dose_calagem = TABELA_SMP_FIXA.get(round(smp, 1), 'SMP fora da faixa')

        tabela_p = {
            "1º Cultivo": {"Muito Baixo": 155, "Baixo": 95, "Médio": 85, "Alto": 45, "Muito Alto": 0},
            "2º Cultivo": {"Muito Baixo": 95, "Baixo": 75, "Médio": 45, "Alto": 45, "Muito Alto": 30},
        }
        tabela_k = {
            "1º Cultivo": {"Muito Baixo": 155, "Baixo": 115, "Médio": 105, "Alto": 75, "Muito Alto": 0},
            "2º Cultivo": {"Muito Baixo": 95, "Baixo": 75, "Médio": 75, "Alto": 75, "Muito Alto": 50},
        }

        base_p = tabela_p.get(cultivo, {}).get(class_p, 0)
        correcao_p = max(0, produtividade - 3) * 15
        total_p = base_p + correcao_p

        base_k = tabela_k.get(cultivo, {}).get(class_k, 0)
        correcao_k = max(0, produtividade - 3) * 25
        total_k = base_k + correcao_k

        enxofre_ha = (enxofre * 2000) / 1000.0
        dose_s = 20 if enxofre_ha < 10 else 0
        dose_mo = 0.04 if ph < 5.5 and argila < 30 else 0

        recom_p2o5 = float(total_p)
        recom_k2o = float(total_k)

        resultados = {
            "Calcário (PRNT 100%)": f"{dose_calagem} t/ha",
            "Fósforo (P2O5)": f"{total_p:.1f} kg/ha",
            "Potássio (K2O)": f"{total_k:.1f} kg/ha",
            "Enxofre (S)": f"{dose_s} kg/ha",
            "Molibdênio (Mo)": f"{dose_mo * 1000:.0f} g/ha",
        }
        for chave, valor in resultados.items():
            widget = labels_resultado.get(chave)
            if widget is not None:
                try:
                    widget.configure(text=valor)
                except Exception:
                    pass

        classificacoes = {
            "Classe do teor de Argila": f"Classe {classe_argila}",
            "CTC": class_ctc,
            "M.O.": class_mo,
            "Fósforo (P)": class_p,
            "Potássio (K)": class_k,
            "Cálcio (Ca)": class_ca,
            "Magnésio (Mg)": class_mg,
            "Enxofre (S)": class_s,
            "Zinco (Zn)": class_zn,
            "Cobre (Cu)": class_cu,
            "Boro (B)": class_b,
            "Manganês (Mn)": class_mn,
        }
        for chave, valor in classificacoes.items():
            widget = labels_classificacao.get(chave)
            if widget is not None:
                try:
                    widget.configure(text=valor)
                except Exception:
                    pass
        return True
    except Exception as exc:
        messagebox.showerror("Erro", f"Entrada inválida: {exc}")
        return False
