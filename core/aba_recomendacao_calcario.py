from __future__ import annotations

from .context import AppContext, TabHost


def add_tab(tabhost: TabHost, ctx: AppContext):
    try:
        from tabs import recomendacao_calcario as mod
        return mod.add_tab(tabhost, ctx)
    except Exception as exc:
        print(f"[WARN] Falha ao carregar aba de calcário: {exc}")
        return None


