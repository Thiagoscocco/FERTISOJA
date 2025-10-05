import importlib
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
import customtkinter as ctk


class TabHost:
    def __init__(self, tabview: ctk.CTkTabview):
        self._tabview = tabview

    @property
    def widget(self):
        return self._tabview

    def add_tab(self, title: str):
        return self._tabview.add(title)

    def tab(self, title: str):
        return self._tabview.tab(title)


@dataclass
class AppContext:
    janela: ctk.CTk
    abas: TabHost
    campos: dict
    labels_classificacao: dict
    labels_resultado: dict
    cultivo_var: ctk.StringVar
    calcular: callable

    def get_entradas(self):
        out = {}
        for chave, widget in self.campos.items():
            try:
                out[chave] = widget.get()
            except Exception:
                out[chave] = None
        out["Cultivo"] = self.cultivo_var.get()
        return out

    def get_resultados(self):
        out = {}
        for chave, widget in self.labels_resultado.items():
            try:
                out[chave] = widget.cget("text")
            except Exception:
                out[chave] = None
        return out

    def get_classificacoes(self):
        out = {}
        for chave, widget in self.labels_classificacao.items():
            try:
                out[chave] = widget.cget("text")
            except Exception:
                out[chave] = None
        return out


def carregar_abas_externas(tabhost: TabHost, ctx: AppContext, package_name: str = "tabs"):
    base_dir = Path(__file__).resolve().parent.parent / package_name
    if not base_dir.exists():
        return
    root_dir = str(base_dir.parent)
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    for _, modname, _ in pkgutil.iter_modules([str(base_dir)]):
        try:
            mod = importlib.import_module(f"{package_name}.{modname}")
            add_tab = getattr(mod, "add_tab", None)
            if callable(add_tab):
                add_tab(tabhost, ctx)
        except Exception as exc:
            print(f"[WARN] Falha ao carregar aba '{modname}': {exc}")
