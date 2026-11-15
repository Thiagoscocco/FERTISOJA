"""Interface de exportação de laudos em PNG A4."""
from __future__ import annotations

import re
import smtplib
import ssl
import tempfile
from email.message import EmailMessage
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .context import AppContext, TabHost
from .design_constants import (
    FONT_SIZE_BODY, FONT_SIZE_HEADING, PADX_SMALL, PADX_STANDARD,
    PADY_SMALL, PADY_STANDARD, PANEL_DARK, PANEL_LIGHT, PRIMARY_BLUE,
    SUCCESS_GREEN,
)
from .laudo_png import TABELAS, coletar_tabelas, gerar_laudo
from .ui import create_entry_field, create_label, create_primary_button, enable_mousewheel_scroll, make_section

EMAIL_CONFIG_PATH = Path(__file__).resolve().parent.parent / 'modelo_mail' / '.env'
EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _dados_e_selecao(ctx, controles):
    dados = {chave: campo.get().strip() for chave, campo in controles['entries'].items()}
    selecionadas = {chave for chave, var in controles['tabelas'].items() if var.get()}
    if not selecionadas:
        raise ValueError('Selecione pelo menos uma tabela para exportar.')
    return dados, selecionadas, coletar_tabelas(ctx)


def _exportar(ctx, controles):
    try:
        dados, selecionadas, tabelas = _dados_e_selecao(ctx, controles)
        destino = filedialog.asksaveasfilename(
            parent=ctx.janela,
            title='Salvar laudo FertiSoja em PNG',
            initialfile='Laudo_FertiSoja.png',
            defaultextension='.png',
            filetypes=[('Imagem PNG', '*.png')],
        )
        if not destino:
            return
        gerar_laudo(destino, dados, tabelas, selecionadas)
        controles['status_var'].set(f'Laudo salvo: {destino}')
        messagebox.showinfo('Exportação', 'Laudo PNG salvo com sucesso.', parent=ctx.janela)
    except Exception as exc:
        controles['status_var'].set('Não foi possível gerar o laudo.')
        messagebox.showerror('Exportação', str(exc), parent=ctx.janela)


def _config_email():
    if not EMAIL_CONFIG_PATH.exists():
        raise ValueError('Configurações de e-mail não encontradas em modelo_mail/.env.')
    config = {}
    for linha in EMAIL_CONFIG_PATH.read_text(encoding='utf-8').splitlines():
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            chave, valor = linha.split('=', 1)
            config[chave.strip()] = valor.strip().strip('"').strip("'")
    if any(not config.get(chave) for chave in ('EMAIL_FROM', 'SMTP_PASS', 'SMTP_HOST', 'SMTP_PORT')):
        raise ValueError('Configurações de e-mail incompletas em modelo_mail/.env.')
    return config


def _enviar_email(ctx, controles):
    try:
        dados, selecionadas, tabelas = _dados_e_selecao(ctx, controles)
        destinatarios = [item.strip() for item in re.split(r'[;,]', controles['email_entry'].get()) if item.strip()]
        if not destinatarios or any(not EMAIL_REGEX.fullmatch(item) for item in destinatarios):
            raise ValueError('Informe um e-mail válido para cada destinatário.')
        config = _config_email()
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = Path(diretorio) / 'Laudo_FertiSoja.png'
            gerar_laudo(arquivo, dados, tabelas, selecionadas)
            mensagem = EmailMessage()
            mensagem['Subject'] = 'Laudo de adubação e calagem — FertiSoja'
            mensagem['From'] = config['EMAIL_FROM']
            mensagem['To'] = ', '.join(destinatarios)
            mensagem.set_content('Olá! Segue em anexo o laudo selecionado no FertiSoja. Consulte um engenheiro agrônomo antes da aplicação.')
            mensagem.add_attachment(arquivo.read_bytes(), maintype='image', subtype='png', filename=arquivo.name)
            host = config['SMTP_HOST']
            porta = int(config['SMTP_PORT'])
            tls = config.get('SMTP_USE_TLS', 'true').lower() not in {'0', 'false', 'no', 'n'}
            contexto = ssl.create_default_context()
            if tls and porta != 465:
                with smtplib.SMTP(host, porta, timeout=30) as servidor:
                    servidor.ehlo()
                    servidor.starttls(context=contexto)
                    servidor.login(config.get('SMTP_USER') or config['EMAIL_FROM'], config['SMTP_PASS'])
                    servidor.send_message(mensagem)
            else:
                with smtplib.SMTP_SSL(host, porta, timeout=30, context=contexto) as servidor:
                    servidor.login(config.get('SMTP_USER') or config['EMAIL_FROM'], config['SMTP_PASS'])
                    servidor.send_message(mensagem)
        controles['status_var'].set('E-mail enviado com o laudo PNG.')
        messagebox.showinfo('Exportação', 'E-mail enviado com sucesso.', parent=ctx.janela)
    except Exception as exc:
        controles['status_var'].set('Não foi possível enviar o e-mail.')
        messagebox.showerror('Exportação', str(exc), parent=ctx.janela)


def add_tab(tabhost: TabHost, ctx: AppContext) -> None:
    heading_font = getattr(ctx, 'heading_font', ctk.CTkFont(size=FONT_SIZE_HEADING, weight='bold'))
    aba = tabhost.add_tab('🌱 Exportação')
    outer = ctk.CTkScrollableFrame(aba, fg_color='transparent')
    enable_mousewheel_scroll(ctx.janela, outer)
    outer.pack(fill='both', expand=True, padx=PADX_STANDARD, pady=PADY_STANDARD)

    sec_dados = make_section(outer, 'Dados do produtor', heading_font)
    sec_dados.grid_columnconfigure(0, weight=1, uniform='form')
    sec_dados.grid_columnconfigure(1, weight=1, uniform='form')
    campos = {}
    campos_layout = (
        ('Produtor', 'produtor', 'Nome completo do produtor'),
        ('Município', 'municipio', 'Cidade/UF'),
        ('Talhão', 'talhao', 'Identificação do talhão'),
        ('Ano', 'ano', 'AAAA'),
        ('Safra', 'safra', 'Ex.: 2025/26'),
    )
    for index, (rotulo, chave, placeholder) in enumerate(campos_layout):
        bloco = ctk.CTkFrame(sec_dados, fg_color='transparent')
        bloco.grid(row=index // 2, column=index % 2, sticky='ew', padx=PADX_SMALL, pady=PADY_SMALL)
        create_label(bloco, rotulo, weight='bold').pack(anchor='w')
        campo = create_entry_field(bloco, placeholder_text=placeholder, corner_radius=10,
                                   border_width=1, border_color=(PRIMARY_BLUE, PRIMARY_BLUE),
                                   fg_color=(PANEL_LIGHT, PANEL_DARK))
        campo.pack(fill='x')
        campos[chave] = campo

    sec_tabelas = make_section(outer, 'Tabelas do laudo', heading_font)
    for coluna in range(2):
        sec_tabelas.grid_columnconfigure(coluna, weight=1, uniform='tabelas')
    for linha in range((len(TABELAS) + 1) // 2):
        sec_tabelas.grid_rowconfigure(linha, minsize=40)
    selecoes = {}
    for index, (chave, titulo) in enumerate(TABELAS):
        variavel = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sec_tabelas, text=titulo, variable=variavel,
                        checkbox_width=24, checkbox_height=24).grid(
            row=index // 2, column=index % 2, sticky='w', padx=PADX_SMALL, pady=4)
        selecoes[chave] = variavel

    sec_acoes = make_section(outer, 'Gerar laudo', heading_font)
    create_label(sec_acoes, 'Selecione as tabelas e gere o laudo em PNG A4 vertical.',
                 font_size=FONT_SIZE_BODY, anchor='w', justify='left').pack(fill='x', pady=(0, PADY_SMALL))
    status_var = ctk.StringVar(value='Pronto para exportar.')
    status_label = create_label(sec_acoes, '', font_size=FONT_SIZE_BODY, anchor='w')
    status_label.configure(textvariable=status_var, text_color=SUCCESS_GREEN)
    status_label.pack(fill='x', pady=(0, PADY_SMALL))
    controles = {'entries': campos, 'tabelas': selecoes, 'status_var': status_var}
    create_primary_button(sec_acoes, 'Gerar PNG A4', lambda: _exportar(ctx, controles)).pack(fill='x', pady=(0, PADY_SMALL))
    create_label(sec_acoes, 'E-mail do destinatário', weight='bold').pack(anchor='w')
    email_entry = create_entry_field(sec_acoes, placeholder_text='ex.: produtor@email.com')
    email_entry.pack(fill='x', pady=(0, PADY_SMALL))
    controles['email_entry'] = email_entry
    create_primary_button(sec_acoes, 'Enviar PNG por e-mail', lambda: _enviar_email(ctx, controles)).pack(fill='x')
    ctx.exportacao_controls = controles
