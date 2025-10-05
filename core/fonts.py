import customtkinter as ctk

DEFAULT_FONT_FAMILY = "Segoe UI"


def aplicar_fonte_global(root):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    default_font = ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12)
    heading_font = ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13, weight="bold")
    root._default_font = default_font
    root._heading_font = heading_font
    return default_font, heading_font
