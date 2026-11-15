"""Dados e composição do laudo FertiSoja em uma página A4 PNG."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import aba_resultados

A4_SIZE = (2480, 3508)
DPI = 300
GREEN = '#25843a'
BLUE = '#1f538d'
INK = '#20272b'
LINE = '#ccd8d1'
LIGHT = '#edf5ef'


@dataclass
class Tabela:
    chave: str
    titulo: str
    linhas: list[tuple[str, ...]]


TABELAS = (
    ('producao', 'Informações da produção'),
    ('propriedades', 'Propriedades gerais do solo'),
    ('macronutrientes', 'Macronutrientes'),
    ('micronutrientes', 'Micronutrientes'),
    ('calagem', 'Recomendação de calagem'),
    ('necessidades', 'Necessidade bruta de nutrientes'),
    ('estrategia', 'Estratégia de aplicação'),
    ('fertilizantes', 'Escolha dos fertilizantes'),
    ('resultado_ha', 'Resultado final por hectare'),
    ('resultado_total', 'Resultado final na área total'),
)


def _valor(valor, vazio='—'):
    if valor is None:
        return vazio
    if hasattr(valor, 'get'):
        valor = valor.get()
    texto = str(valor).strip()
    return texto if texto else vazio


def _entrada(entradas, chave, unidade=''):
    valor = _valor(entradas.get(chave))
    return f'{valor} {unidade}'.strip() if valor != '—' else valor


def _classificacao(classificacoes, chave):
    valor = _valor(classificacoes.get(chave))
    return '—' if valor in {'-', '—'} else valor


def coletar_tabelas(ctx):
    """Captura os valores mostrados nas abas, sem recalcular silenciosamente."""
    entradas = ctx.get_entradas()
    classificacoes = ctx.get_classificacoes()
    adub = getattr(ctx, 'adubacao_controls', {}) or {}
    fertil = getattr(ctx, 'fertilizacao_controls', {}) or {}
    calc = getattr(ctx, 'calagem_controls', {}) or {}
    resultados = getattr(ctx, 'resultados_controls', {}) or {}
    diag = (getattr(ctx, 'condicoes_controls', {}) or {}).get('summary', {})
    metodo = _valor(adub.get('metodo'))
    modo = _valor(fertil.get('modo_var'))
    formula = fertil.get('formulado_inputs', {})

    producao = [
        ('Cultura', 'Soja'),
        ('Produtividade esperada', _entrada(entradas, 'Produtividade esperada', 't/ha')),
        ('Área', _entrada(entradas, 'Area (Ha)', 'ha')),
        ('Cultivo', _valor(entradas.get('Cultivo'))),
        ('Método de adubação', metodo),
        ('Tipo de fertilização', modo),
    ]
    if 'formulad' in modo.casefold() or 'misto' in modo.casefold():
        producao.append(('Fórmula N–P₂O₅–K₂O (%)',
                         ' – '.join(_valor(formula.get(chave)) for chave in ('N', 'P2O5', 'K2O'))))
    propriedades = [
        ('Índice SMP', _entrada(entradas, 'Indice SMP')),
        ('Argila (%)', f"{_entrada(entradas, 'Argila (%)')} | {_classificacao(classificacoes, 'Classe do teor de Argila')}"),
        ('CTC (cmolc/dm³)', f"{_entrada(entradas, 'CTC (cmolc/dm3)')} | {_classificacao(classificacoes, 'CTC')}"),
        ('M.O. (%)', f"{_entrada(entradas, 'M.O. (%)')} | {_classificacao(classificacoes, 'M.O.')}"),
        ('pH (água)', _entrada(entradas, 'pH (Agua)')),
        ('Sistema de manejo', _valor(calc.get('sistema'))),
        ('Profundidade da análise', _valor(calc.get('profundidade'))),
    ]
    def nutriente(nome, chave, classe):
        return nome, _entrada(entradas, chave), _classificacao(classificacoes, classe)
    macros = [
        nutriente('P (mg/dm³)', 'P (mg/dm3)', 'Fósforo (P)'),
        nutriente('K (mg/dm³)', 'K (mg/dm3)', 'Potássio (K)'),
        nutriente('Ca (cmolc/dm³)', 'Ca (cmolc/dm3)', 'Cálcio (Ca)'),
        nutriente('Mg (cmolc/dm³)', 'Mg (cmolc/dm3)', 'Magnésio (Mg)'),
        nutriente('S (mg/dm³)', 'S (mg/dm3)', 'Enxofre (S)'),
        ('Resposta ao P', _valor(diag.get('p')), '—'),
        ('Resposta ao K', _valor(diag.get('k')), '—'),
    ]
    micros = [
        nutriente('Zn (mg/dm³)', 'Zn (mg/dm3)', 'Zinco (Zn)'),
        nutriente('Cu (mg/dm³)', 'Cu (mg/dm3)', 'Cobre (Cu)'),
        nutriente('B (mg/dm³)', 'B (mg/dm3)', 'Boro (B)'),
        nutriente('Mn (mg/dm³)', 'Mn (mg/dm3)', 'Manganês (Mn)'),
    ]
    resumo_calc = calc.get('summary', {})
    calagem = [
        ('pH alvo', _valor(calc.get('ph_alvo'))),
        ('V% atual', _valor(calc.get('v_pct'))),
        ('Al% (saturação)', _valor(calc.get('al_pct'))),
        ('Al trocável (cmolc/dm³)', _valor(calc.get('al_trocavel'))),
        ('PRNT (%)', _valor(calc.get('prnt'))),
        ('Dose recomendada', _valor(resumo_calc.get('dose'))),
        ('Quantidade total', _valor(resumo_calc.get('total'))),
        ('Modo de aplicação', _valor(resumo_calc.get('mode'))),
        ('Época sugerida', _valor(resumo_calc.get('epoca'))),
        ('Tipo de corretivo', _valor(resumo_calc.get('tipo'))),
    ]
    summary = adub.get('summary', {})
    necessidades = [(rotulo, _valor(summary.get(chave))) for rotulo, chave in (
        ('Fósforo (P₂O₅)', 'P2O5'), ('Potássio (K₂O)', 'K2O'),
        ('Enxofre (S-SO₄)', 'S'), ('Molibdênio (Mo)', 'Mo'),
    )]
    estrategia = [('Método', metodo)]
    if metodo.casefold() == 'correção':
        estrategia.append(('Tipo de correção', _valor(adub.get('correcao_var'))))
    for rotulo, chave in (('P₂O₅', 'P'), ('K₂O', 'K')):
        estrategia.append((rotulo, _valor(adub.get('resultado_metodo', {}).get(chave))))

    escolha = [('Modo', modo)]
    modo_normalizado = modo.casefold()
    if 'formulad' in modo_normalizado or 'misto' in modo_normalizado:
        for nome, chave in (('N (%)', 'N'), ('P₂O₅ (%)', 'P2O5'), ('K₂O (%)', 'K2O')):
            escolha.append((nome, _valor(formula.get(chave))))
    if 'misto' in modo_normalizado:
        escolha.append(('Sacos de 50 kg', _valor(fertil.get('misto_sacos_var'))))
    if 'individual' in modo_normalizado or 'misto' in modo_normalizado:
        submodo = _valor(fertil.get('submodo_var'))
        escolha.append(('Seleção', submodo))
        if 'usuario' in submodo.casefold() or 'usuário' in submodo.casefold():
            escolha.extend([('Fosfatado', _valor(fertil.get('fosfatado_var'))),
                            ('Potássico', _valor(fertil.get('potassico_var')))])
    resultado_fert = fertil.get('ultimo_resultado')
    if resultado_fert is None:
        escolha.append(('Produtos', 'Ainda não calculados'))
    elif not resultado_fert.produtos:
        escolha.append(('Produtos', 'Nenhum produto necessário'))
    else:
        escolha.extend(('Produto', nome) for nome, _ in resultado_fert.produtos)
        for nutriente_faltante, valor in (resultado_fert.faltantes or {}).items():
            escolha.append((f'Faltante {nutriente_faltante}', f'{valor:.2f} kg/ha'))

    cache = resultados.get('dados_cache')
    if cache is None:
        cache = aba_resultados._coletar_dados(ctx)
    calcario, produtos, area = cache
    unidade_ha = _valor(resultados.get('unidade_ha'), 'kg')
    unidade_total = _valor(resultados.get('unidade_total'), 'kg')
    linhas_ha = aba_resultados._montar_itens_per_area(calcario, produtos, unidade_ha)
    linhas_total = aba_resultados._montar_itens_totais(calcario, produtos, unidade_total, area)
    tabelas = (producao, propriedades, macros, micros, calagem, necessidades, estrategia, escolha, linhas_ha, linhas_total)
    return [Tabela(chave, titulo, linhas) for (chave, titulo), linhas in zip(TABELAS, tabelas)]


def _fonte(tamanho, negrito=False):
    nome = 'DejaVuSans-Bold.ttf' if negrito else 'DejaVuSans.ttf'
    caminhos = [Path(__file__).resolve().parent.parent / 'assets' / nome,
                Path('/usr/share/fonts/truetype/dejavu') / nome,
                Path('C:/Windows/Fonts') / ('arialbd.ttf' if negrito else 'arial.ttf'),
                Path('/System/Library/Fonts/Supplemental') / ('Arial Bold.ttf' if negrito else 'Arial.ttf')]
    for caminho in caminhos:
        if caminho.exists():
            return ImageFont.truetype(str(caminho), tamanho)
    try:
        return ImageFont.truetype(nome, tamanho)
    except OSError:
        return ImageFont.load_default(size=tamanho)


def _quebrar(draw, texto, fonte, largura):
    linhas = []
    for paragrafo in str(texto).split('\n'):
        atual = ''
        for palavra in paragrafo.split():
            candidato = f'{atual} {palavra}'.strip()
            if draw.textlength(candidato, font=fonte) <= largura:
                atual = candidato
            else:
                if atual:
                    linhas.append(atual)
                    atual = ''
                while palavra and draw.textlength(palavra, font=fonte) > largura:
                    indice = 1
                    while indice < len(palavra) and draw.textlength(palavra[:indice + 1], font=fonte) <= largura:
                        indice += 1
                    linhas.append(palavra[:indice])
                    palavra = palavra[indice:]
                atual = palavra
        linhas.append(atual or ' ')
    return linhas or ['—']


def _recursos():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))


def gerar_laudo(destino, dados, tabelas, selecionadas):
    """Cria uma imagem A4 vertical; comprime as tabelas sem cortar conteúdo."""
    escolhidas = [tabela for tabela in tabelas if tabela.chave in selecionadas]
    if not escolhidas:
        raise ValueError('Selecione ao menos uma tabela para o laudo.')
    imagem = Image.new('RGB', A4_SIZE, 'white')
    marcas = (
        (_recursos() / 'assets' / 'Logo Thiago.png', (1250, 850), 800, True),
        (_recursos() / 'imagem.png', (1250, 850), 1770, False),
    )
    for caminho, tamanho, centro_y, tingir in marcas:
        if caminho.exists():
            with Image.open(caminho) as original:
                logo = original.convert('RGBA')
                if tingir:
                    # O desenho original é quase branco: tingi-lo permite vê-lo no papel branco.
                    alpha_original = logo.getchannel('A')
                    caixa = alpha_original.getbbox()
                    if caixa:
                        alpha_original = alpha_original.crop(caixa)
                    logo = Image.new('RGBA', alpha_original.size, '#23753b')
                    logo.putalpha(alpha_original)
                logo = ImageOps.contain(logo, tamanho)
                logo.putalpha(logo.getchannel('A').point(lambda a: int(a * 0.045)))
                imagem.paste(logo, ((A4_SIZE[0] - logo.width) // 2, centro_y - logo.height // 2), logo)
    draw = ImageDraw.Draw(imagem)
    largura, altura = imagem.size
    margem = 110
    draw.rectangle((margem, 95, margem + 14, 200), fill=GREEN)
    draw.text((margem + 42, 90), 'FERTISOJA', font=_fonte(68, True), fill=GREEN)
    draw.text((margem + 45, 174), 'LAUDO DE ADUBAÇÃO E CALAGEM', font=_fonte(31, True), fill=BLUE)
    draw.line((margem, 225, largura - margem, 225), fill=LINE, width=3)

    cabecalho = [('Produtor', dados.get('produtor', '')), ('Município', dados.get('municipio', '')),
                 ('Talhão', dados.get('talhao', '')), ('Ano', dados.get('ano', '')), ('Safra', dados.get('safra', ''))]
    cabecalho = [(rotulo, str(valor).strip()) for rotulo, valor in cabecalho if str(valor).strip()]
    cabecalho = cabecalho or [('Identificação', 'Não informada')]
    identificacao = Tabela('identificacao', 'Identificação', cabecalho)
    y_inicio = 255
    limite_y = altura - 160
    coluna_gap = 32
    coluna_largura = (largura - 2 * margem - coluna_gap) // 2

    def calcular_layout(escala):
        fonte = _fonte(max(16, int(30 * escala)))
        fonte_titulo = _fonte(max(18, int(32 * escala)), True)
        fonte_coluna = _fonte(max(16, int(27 * escala)), True)
        padding = max(7, int(16 * escala))
        espaco = max(7, int(18 * escala))
        linha_alt = max(20, int(40 * escala))
        titulo_alt = max(30, int(52 * escala))
        layout = []

        def medir_tabela(tabela, table_width):
            tres_colunas = tabela.chave in {'macronutrientes', 'micronutrientes'}
            fracoes = (.42, .24, .34) if tres_colunas else (.47, .53)
            widths = [int(table_width * fracao) for fracao in fracoes[:-1]]
            widths.append(table_width - sum(widths))
            linhas = tabela.linhas
            if tres_colunas:
                linhas = [('Nutriente', 'Valor', 'Classificação'), *linhas]
            rows = []
            for indice, linha in enumerate(linhas):
                cabecalho_colunas = tres_colunas and indice == 0
                fonte_linha = fonte_coluna if cabecalho_colunas else fonte
                celulas = [
                    _quebrar(draw, _valor(valor), fonte_linha, largura_coluna - 2 * padding)
                    for valor, largura_coluna in zip(linha, widths)
                ]
                row_h = max(map(len, celulas)) * linha_alt + 2 * padding
                rows.append((celulas, row_h, cabecalho_colunas))
            h = titulo_alt + sum(row[1] for row in rows)
            return h, rows, widths

        largura_total = largura - 2 * margem
        h, rows, widths = medir_tabela(identificacao, largura_total)
        layout.append((identificacao, 0, y_inicio, h, rows, widths, largura_total))
        y = y_inicio + h + espaco

        # A ordem do software é mantida; macro e micro permanecem juntos.
        grupos = []
        for tabela in escolhidas:
            if tabela.chave == 'micronutrientes' and grupos and grupos[-1][-1].chave == 'macronutrientes':
                grupos[-1].append(tabela)
            else:
                grupos.append([tabela])

        blocos = [[(tabela, *medir_tabela(tabela, coluna_largura)) for tabela in grupo]
                  for grupo in grupos]
        alturas = [sum(item[1] + espaco for item in bloco) for bloco in blocos]
        # Cada coluna cresce sem espaços reservados para tabelas desmarcadas.
        # Dividir a sequência em dois trechos mantém também a ordem de leitura.
        divisoes = range(1, len(blocos)) if len(blocos) > 1 else (len(blocos),)
        divisao = min(divisoes, key=lambda indice: max(sum(alturas[:indice]), sum(alturas[indice:])))
        fins = []
        for coluna, coluna_blocos in enumerate((blocos[:divisao], blocos[divisao:])):
            y_coluna = y
            for bloco in coluna_blocos:
                for tabela, h, rows, widths in bloco:
                    layout.append((tabela, coluna, y_coluna, h, rows, widths, coluna_largura))
                    y_coluna += h + espaco
            fins.append(y_coluna)
        return max(fins), layout, fonte, fonte_titulo, fonte_coluna, padding, linha_alt, titulo_alt

    for escala in (1.0, .9, .8, .7, .6, .5):
        fim, layout, fonte, fonte_titulo, fonte_coluna, padding, linha_alt, titulo_alt = calcular_layout(escala)
        if fim <= limite_y:
            break
    else:
        raise ValueError('As informações selecionadas são extensas demais para uma página A4. Reduza o texto ou selecione menos tabelas.')

    for tabela, col, y, h, rows, widths, table_width in layout:
        x = margem + col * (coluna_largura + coluna_gap)
        x2 = x + table_width
        draw.rectangle((x, y, x2, y + h), outline=LINE, width=2)
        draw.rectangle((x, y, x2, y + titulo_alt), fill=LIGHT)
        draw.rectangle((x, y, x + 7, y + titulo_alt), fill=GREEN)
        draw.text((x + padding + 8, y + max(1, (titulo_alt - fonte_titulo.size) // 2 - 2)), tabela.titulo, font=fonte_titulo, fill=BLUE)
        cursor = y + titulo_alt
        for celulas, row_h, cabecalho_colunas in rows:
            fonte_linha = fonte_coluna if cabecalho_colunas else fonte
            draw.line((x, cursor, x2, cursor), fill=LINE, width=1)
            esquerda = x
            for indice, (linhas_celula, largura_celula) in enumerate(zip(celulas, widths)):
                if indice:
                    draw.line((esquerda, cursor, esquerda, cursor + row_h), fill=LINE, width=1)
                for numero, linha in enumerate(linhas_celula):
                    draw.text((esquerda + padding, cursor + padding + numero * linha_alt),
                              linha, font=fonte_linha, fill=BLUE if cabecalho_colunas else INK)
                esquerda += largura_celula
            cursor += row_h

    draw.line((margem, altura - 128, largura - margem, altura - 128), fill=LINE, width=2)
    draw.text((margem, altura - 100), 'Consulte um engenheiro agrônomo.', font=_fonte(27), fill=INK)
    assinatura = 'DEV Thiagoscocco 2025'
    assinatura_font = _fonte(25, True)
    draw.text((largura - margem - draw.textlength(assinatura, font=assinatura_font), altura - 100), assinatura, font=assinatura_font, fill=BLUE)
    imagem.save(destino, format='PNG', dpi=(DPI, DPI))
