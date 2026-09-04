# -*- coding: utf-8 -*-
"""
Desenha a interface do Thor Patcher a partir do design "Launcher Midgard".

    python patcher/gerar-visual.py

Escreve em patcher/images/. Sao arquivos GERADOS - para mudar o visual mexa
aqui, nao neles.

DE ONDE VEM ISTO
Do bundle de handoff do Claude Design (Launcher Midgard.dc.html). O design e um
prototipo HTML/CSS: gradientes, animacoes, painel translucido, abas com estado.
O Thor Patcher nao tem nada disso - ele sabe desenhar UMA imagem de fundo e
posicionar quatro tipos de widget por cima (Button, ProgressBar, Label,
NoticeBox). A traducao e sempre a mesma pergunta: isto muda em tempo de
execucao?

    nao muda  -> vai ASSADO no bg.bmp (moldura, nome, painel, redes, moldura
                 da barra, marca d'agua do logo)
    muda      -> vira widget (START, fechar, engrenagem, barra, status)
    e conteudo-> vira NoticeBox, que e um controle do Internet Explorer e
                 portanto aceita HTML de verdade (abas, banner do evento,
                 status do mundo)

O QUE FOI CORTADO DO DESIGN, E POR QUE
  - abas de idioma (Portugues / Espanol / English): so entregamos PT-BR. Botao
    que nao faz nada e pior que botao ausente.
  - botao RE/PLAY: nao ha nada para ele abrir hoje. O Thor so sabe "abrir URL"
    ou "executar arquivo", e nenhum dos dois serve para "ver replays".
  - animacoes (shine na barra, pulse no START, bob no logo): o Thor desenha
    bitmap parado. O brilho do START virou gradiente fixo.
  - o TRANSBORDO da moldura (logo em cima, fechar no canto, mascote na base):
    o recorte da janela e chroma key, sem alfa, entao tudo que fica fora da
    moldura aparece com franja e degrau na borda. Ver a nota em MARGEM_*.
  - som ao clicar: o Thor so tem BGM, nao ha evento de audio por botao.

ESCALA
A moldura do design tem 1040x660 e a janela e exatamente ela. Em 0.92 sai
957x607, que cabe folgado em 1366x768 - a resolucao que o Padrao-Video.reg
entrega ao tester. Tudo e desenhado em coordenadas do design e convertido na
hora, entao mudar a escala nao exige remexer em numero nenhum.

DUAS REGRAS DO THOR QUE MANDAM NO DESENHO
1. O fundo em BMP usa o pixel do canto superior esquerdo como cor transparente
   (chroma key do Win32). E o que permite a moldura arredondada. A chave e uma
   magenta que nao aparece no tema. Comparacao EXATA, sem alfa - ver MARGEM_*.
2. As posicoes aqui e as do config.ini sao O MESMO LAYOUT escrito duas vezes.
   O config.ini e gerado por este script justamente para nao desencontrarem -
   ver escrever_config().
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
IMAGES = AQUI / 'images'
FONTES = AQUI / 'fontes'
FONTES_WIN = Path('C:/Windows/Fonts')

# ---------------------------------------------------------------------------
# Escala e enquadramento
# 0.92 cabe folgado em 1366x768 (957x607) depois que a janela deixou de ter
# transbordo. Antes era 0.85 porque o design somava 1170x790 com o logo e o
# botao de fechar para fora da moldura.
ESCALA = 0.92
SS = 2                                  # supersampling, so para as curvas

# Coordenadas do design, com a moldura em (0,0)
MOLDURA = (0, 0, 1040, 660)
RAIO_MOLDURA = 34
# NADA transborda a moldura, e isso e uma decisao, nao um esquecimento.
#
# O Thor recorta a janela por CHROMA KEY: a cor do pixel superior esquerdo vira
# transparente, comparada exata. Nao existe alfa. Qualquer coisa desenhada fora
# da moldura - o logo, o botao de fechar, o mascote do design - tem borda
# suavizada, e cada pixel meio-transparente fica visivel como franja magenta.
# Foi exatamente a "borda serrilhada" reportada no primeiro teste.
#
# Com a janela colada na moldura, o unico lugar que o chroma key toca sao os
# quatro cantos arredondados, onde o raio de 34px torna o degrau imperceptivel.
MARGEM_ESQ, MARGEM_TOPO = 0, 0
MARGEM_DIR, MARGEM_BASE = 0, 0
LARG_D = MOLDURA[2] + MARGEM_ESQ + MARGEM_DIR      # 1170
ALT_D = MOLDURA[3] + MARGEM_TOPO + MARGEM_BASE     # 790

# Area de conteudo: padding 108 40 34 116 e grid 1fr / 330 com gap 28
CONT = (116, 108, 1000, 626)
COL_DIR_LARG = 330
GAP_COL = 28
COL_ESQ = (CONT[0], CONT[2] - COL_DIR_LARG - GAP_COL)     # 116 .. 642
COL_DIR = (CONT[2] - COL_DIR_LARG, CONT[2])               # 670 .. 1000

# Pilha da coluna esquerda (gap 18)
Y_NOME = 108
ALT_NOME = 32
Y_NOTICE = 158                          # abas + banner, vira NoticeBox
ALT_NOTICE = 350
Y_BARRA_ROTULO = 526
Y_BARRA = 552
ALT_BARRA = 16
Y_REDES = 586
ALT_REDES = 40

# Coluna direita
PAINEL = (COL_DIR[0], 200, COL_DIR[1], 472)     # status do mundo (NoticeBox 2)
START_D = 140
BOT_PEQ = 48
Y_BOTOES = 486
X_START = COL_DIR[0] + (COL_DIR_LARG - (START_D + 16 + BOT_PEQ)) // 2
X_ENGRENAGEM = X_START + START_D + 16

# O fechar era 66px e ficava fora, no canto. Encolheu para 42 e entrou: fora da
# moldura ele era um circulo inteiro recortado por chroma key, que e onde o
# serrilhado mais aparece.
FECHAR_D = 42
FECHAR = (MOLDURA[2] - 40 - FECHAR_D, 26)

# ---------------------------------------------------------------------------
# Paleta, do design
CHAVE = (255, 0, 255)
AZUL_A, AZUL_B, AZUL_C = (26, 75, 125), (15, 47, 82), (10, 35, 64)
ACENTO = (120, 230, 255)
CLARO = (207, 238, 255)
TEXTO = (223, 242, 255)
APAGADO = (160, 196, 220)
FUNDO_FUNDO = (8, 10, 15)
# A MESMA cor que o body do patcher/web/style.css usa. Se mudar uma, mude a
# outra: e o que faz a caixa do IE nao aparecer recortada sobre o bitmap.
PAINEL_HTML = (6, 26, 48)

NOME_SERVIDOR = 'Midgard Eternal'
SELO = 'HIGH RATE'
REDES = ('DC', 'FB', 'IG', 'YT', 'TT')
VERSAO_TXT = '0.0.11'


def p(v):
    """Coordenada do design -> pixel do canvas, ja com margem e escala."""
    return int(round(v * ESCALA))


def px(x):
    return p(x + MARGEM_ESQ)


def py(y):
    return p(y + MARGEM_TOPO)


LARG, ALT = p(LARG_D), p(ALT_D)


def fonte(nome, tam, ss=1):
    """Fonte do design, com queda para o Windows se nao tiver sido baixada."""
    alvo = FONTES / nome
    if alvo.exists():
        return ImageFont.truetype(str(alvo), int(tam * ESCALA * ss))
    reserva = {'Cinzel-900.ttf': 'georgiab.ttf', 'Cinzel-700.ttf': 'georgiab.ttf',
               'BarlowCondensed-700.ttf': 'ARIALNB.TTF',
               'BarlowCondensed-600.ttf': 'ARIALN.TTF',
               'Barlow-700.ttf': 'segoeuib.ttf', 'Barlow-600.ttf': 'segoeuib.ttf',
               'Barlow-500.ttf': 'segoeui.ttf', 'Barlow-400.ttf': 'segoeui.ttf'}
    return ImageFont.truetype(str(FONTES_WIN / reserva[nome]), int(tam * ESCALA * ss))


def gradiente(larg, alt, paradas, angulo=0):
    """Gradiente linear. paradas = [(posicao 0..1, cor)]. angulo 0 = vertical."""
    if angulo == 90:
        base = Image.new('RGB', (larg, 1))
        pix = base.load()
        eixo = larg
    else:
        base = Image.new('RGB', (1, alt))
        pix = base.load()
        eixo = alt
    for i in range(eixo):
        t = i / max(1, eixo - 1)
        ant, prox = paradas[0], paradas[-1]
        for j in range(len(paradas) - 1):
            if paradas[j][0] <= t <= paradas[j + 1][0]:
                ant, prox = paradas[j], paradas[j + 1]
                break
        faixa = max(1e-6, prox[0] - ant[0])
        k = min(1.0, max(0.0, (t - ant[0]) / faixa))
        cor = tuple(int(ant[1][c] + (prox[1][c] - ant[1][c]) * k) for c in range(3))
        if angulo == 90:
            pix[i, 0] = cor
        else:
            pix[0, i] = cor
    return base.resize((larg, alt))


def texto_espacado(d, xy, txt, font, fill, espaco):
    """PIL nao tem letter-spacing; o design usa em quase todo rotulo."""
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + espaco
    return x


def largura_espacada(d, txt, font, espaco):
    return sum(d.textlength(c, font=font) + espaco for c in txt) - espaco


# ---------------------------------------------------------------------------
def desenhar_fundo():
    """O bg.bmp inteiro, em 2x, com a silhueta recortada no fim."""
    W, H = LARG * SS, ALT * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def X(v):
        return px(v) * SS

    def Y(v):
        return py(v) * SS

    def F(nome, tam):
        return fonte(nome, tam, SS)

    # --- moldura -----------------------------------------------------------
    mx0, my0, mx1, my1 = X(0), Y(0), X(MOLDURA[2]), Y(MOLDURA[3])
    mw, mh = mx1 - mx0, my1 - my0
    # o design usa 160deg; na pratica e quase vertical, com leve inclinacao
    corpo = gradiente(mw, mh, [(0.0, AZUL_A), (0.55, AZUL_B), (1.0, AZUL_C)])
    # veu de leitura: escurece a esquerda, onde fica o texto
    veu = gradiente(mw, mh, [(0.0, (6, 26, 48)), (0.42, (6, 26, 48)),
                             (0.68, (6, 26, 48)), (1.0, (6, 26, 48))], angulo=90)
    alfa = Image.new('L', (mw, mh))
    ap = alfa.load()
    for i in range(mw):
        t = i / max(1, mw - 1)
        if t < 0.42:
            a = 219 - (219 - 140) * (t / 0.42)
        elif t < 0.68:
            a = 140 - (140 - 15) * ((t - 0.42) / 0.26)
        else:
            a = 15 + (89 - 15) * ((t - 0.68) / 0.32)
        for j in range(mh):
            ap[i, j] = int(a)
    corpo = Image.composite(veu, corpo, alfa)

    mascara = Image.new('L', (mw, mh), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        [0, 0, mw - 1, mh - 1], radius=RAIO_MOLDURA * SS * ESCALA, fill=255)
    img.paste(corpo, (mx0, my0), mascara)
    d.rounded_rectangle([mx0, my0, mx1 - 1, my1 - 1],
                        radius=int(RAIO_MOLDURA * SS * ESCALA),
                        outline=(150, 225, 255, 72), width=SS)

    # --- selo HIGH RATE ----------------------------------------------------
    # O design tem DUAS marcas: o logo (imagem) transbordando por cima, e um
    # rotulo pequeno "MIDGARD ETERNAL" logo abaixo. Enquanto o logo for texto
    # tambem, os dois viram a mesma palavra duas vezes e parece erro. Fica so o
    # selo aqui; quando o PNG do logo entrar, o rotulo volta.
    # O selo e desenhado numa camada propria e so depois colado: medir texto
    # espacado somando textlength por caractere erra o avanco do primeiro e do
    # ultimo glifo, e o rotulo saia cortado dentro da pilula. Desenhando antes,
    # a caixa vem do proprio bitmap e sempre cabe.
    f_selo = F('Barlow-700.ttf', 13)
    esp_selo = 13 * ESCALA * SS * 0.2
    tinta = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    texto_espacado(ImageDraw.Draw(tinta), (0, 0), SELO, f_selo,
                   (222, 246, 255), esp_selo)
    caixa = tinta.getbbox()
    lsel, hsel = caixa[2] - caixa[0], caixa[3] - caixa[1]
    pad_x, pad_y = int(20 * ESCALA * SS), int(9 * ESCALA * SS)
    sx0, sy0 = X(COL_ESQ[0]), Y(Y_NOME) + int(4 * ESCALA * SS)
    sx1, sy1 = sx0 + lsel + pad_x * 2, sy0 + hsel + pad_y * 2
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=(sy1 - sy0) // 2,
                        fill=(22, 74, 112, 235), outline=(120, 230, 255, 190),
                        width=SS)
    img.alpha_composite(tinta.crop(caixa), (sx0 + pad_x, sy0 + pad_y))

    # --- fundo do NoticeBox das noticias -----------------------------------
    # CHAPADO e na cor EXATA do body do HTML (PAINEL_HTML / #061a30). O
    # controle do IE pinta um retangulo opaco, entao qualquer gradiente aqui
    # embaixo viraria uma emenda visivel em volta da caixa - foi o "fundo nao
    # esta transparente" do primeiro teste. Igualando a cor, a emenda some e so
    # os cantos arredondados denunciam onde uma coisa acaba e a outra comeca.
    d.rounded_rectangle([X(COL_ESQ[0]), Y(Y_NOTICE),
                         X(COL_ESQ[1]), Y(Y_NOTICE + ALT_NOTICE)],
                        radius=int(18 * ESCALA * SS), fill=PAINEL_HTML + (255,))

    # --- trilho da barra ---------------------------------------------------
    d.rounded_rectangle([X(COL_ESQ[0]), Y(Y_BARRA),
                         X(COL_ESQ[1]), Y(Y_BARRA + ALT_BARRA)],
                        radius=int(ALT_BARRA * ESCALA * SS / 2),
                        fill=(4, 20, 40, 166), outline=(150, 235, 255, 89), width=SS)

    # --- redes + versao ----------------------------------------------------
    f_rede = F('BarlowCondensed-700.ttf', 17)
    x = X(COL_ESQ[0])
    dia = int(40 * ESCALA * SS)
    for r in REDES:
        d.ellipse([x, Y(Y_REDES), x + dia, Y(Y_REDES) + dia],
                  fill=(10, 40, 70, 153), outline=(150, 235, 255, 102), width=SS)
        w = d.textlength(r, font=f_rede)
        cx = d.textbbox((0, 0), r, font=f_rede)
        d.text((x + (dia - w) / 2, Y(Y_REDES) + (dia - cx[3]) / 2 - cx[1]),
               r, font=f_rede, fill=(214, 243, 255))
        x += dia + int(10 * ESCALA * SS)

    f_ver = F('Barlow-400.ttf', 12)
    txt_ver = 'v%s \u00b7 servidor privado independente' % VERSAO_TXT
    w = d.textlength(txt_ver, font=f_ver)
    d.text((X(COL_ESQ[1]) - w, Y(Y_REDES) + int(13 * ESCALA * SS)),
           txt_ver, font=f_ver, fill=(200, 232, 250, 158))

    # --- painel de status do mundo (fundo do NoticeBox 2) ------------------
    d.rounded_rectangle([X(PAINEL[0]), Y(PAINEL[1]), X(PAINEL[2]), Y(PAINEL[3])],
                        radius=int(18 * ESCALA * SS), fill=PAINEL_HTML + (255,),
                        outline=(150, 235, 255, 82), width=SS)

    # --- marca no lugar do logo -------------------------------------------
    # O logo de verdade entra depois (image-slot ml-logo do design). Ate la,
    # o nome desenhado ocupa o lugar - melhor que um retangulo "sua arte aqui",
    # que pareceria erro de carregamento para o tester.
    #
    # NO DESIGN o logo TRANSBORDA a moldura, em (-34,-74). Aqui ele fica DENTRO,
    # ocupando o padding-top de 108px que existe justamente para abrir espaco
    # para ele. O motivo e o chroma key: texto flutuando fora da moldura tem
    # borda suavizada, e cada pixel meio-transparente vira franja magenta,
    # porque a chave compara cor exata. Com o PNG do logo pronto da para tentar
    # o transbordo de novo, recortando a silhueta pelo alfa dele.
    f_logo = F('Cinzel-900.ttf', 40)
    f_logo2 = F('Cinzel-700.ttf', 16)
    lx, ly = X(COL_ESQ[0]), Y(14)
    d.text((lx, ly), 'MIDGARD', font=f_logo, fill=(255, 255, 255))
    esp_l = 16 * ESCALA * SS * 0.34
    texto_espacado(d, (lx + int(3 * ESCALA * SS), ly + int(52 * ESCALA * SS)),
                   'ETERNAL', f_logo2, ACENTO, esp_l)

    img = img.resize((LARG, ALT), Image.LANCZOS)

    # --- silhueta ----------------------------------------------------------
    # So os quatro cantos arredondados. A mascara e DURA (sem antialias) de
    # proposito - o chroma key compara cor exata, e pixel meio-transparente
    # viraria franja magenta na borda.
    silhueta = Image.new('L', (LARG, ALT), 0)
    ImageDraw.Draw(silhueta).rounded_rectangle(
        [px(0), py(0), px(MOLDURA[2]) - 1, py(MOLDURA[3]) - 1],
        radius=p(RAIO_MOLDURA), fill=255)

    fora = Image.new('RGB', (LARG, ALT), CHAVE)
    fora.paste(img.convert('RGB'), (0, 0), silhueta)
    return fora


# ---------------------------------------------------------------------------
def circulo(diametro, paradas, texto=None, sub=None, f_texto=None, f_sub=None,
            cor_texto=(255, 255, 255), aro=None, escala_brilho=1.0, desloca=0):
    """Botao redondo, um estado. Usado pelo START, pelo fechar e pela engrenagem."""
    dm = int(diametro * ESCALA)
    img = Image.new('RGBA', (dm, dm), (0, 0, 0, 0))
    ss = 4
    grande = Image.new('RGBA', (dm * ss, dm * ss), (0, 0, 0, 0))
    cores = [(pos, tuple(min(255, int(c * escala_brilho)) for c in cor))
             for pos, cor in paradas]
    faixa = gradiente(dm * ss, dm * ss, cores).convert('RGBA')
    m = Image.new('L', (dm * ss, dm * ss), 0)
    ImageDraw.Draw(m).ellipse([0, 0, dm * ss - 1, dm * ss - 1], fill=255)
    grande.paste(faixa, (0, 0), m)
    if aro:
        ImageDraw.Draw(grande).ellipse([0, 0, dm * ss - 1, dm * ss - 1],
                                       outline=aro, width=ss * 2)
    img = grande.resize((dm, dm), Image.LANCZOS)

    d = ImageDraw.Draw(img)
    if texto:
        cx = d.textbbox((0, 0), texto, font=f_texto)
        w = d.textlength(texto, font=f_texto)
        alt_bloco = cx[3] - cx[1]
        y = (dm - alt_bloco) / 2 - cx[1] + desloca
        if sub:
            y -= int(10 * ESCALA)
        d.text(((dm - w) / 2, y), texto, font=f_texto, fill=cor_texto)
        if sub:
            esp = 11 * ESCALA * 0.24
            lw = largura_espacada(d, sub, f_sub, esp)
            texto_espacado(d, ((dm - lw) / 2, y + alt_bloco + int(6 * ESCALA)),
                           sub, f_sub, cor_texto, esp)
    return img


def trio_start():
    paradas = [(0.0, (233, 251, 255)), (0.38, (143, 224, 255)),
               (0.72, (42, 143, 214)), (1.0, (20, 99, 159))]
    f = fonte('Cinzel-900.ttf', 26)
    fs = fonte('Barlow-700.ttf', 11)
    for suf, brilho, desl in (('1', 1.0, 0), ('2', 1.08, 0), ('3', 0.9, 1)):
        circulo(START_D, paradas, 'START', 'JOGAR AGORA', f, fs,
                (10, 51, 88), aro=(150, 235, 255, 46),
                escala_brilho=brilho, desloca=desl).save(IMAGES / ('start%s.png' % suf))


# O X e a engrenagem sao DESENHADOS, nao escritos. A Barlow e a Cinzel nao tem
# U+2715 nem U+2699 - sairiam como o retangulo de glifo ausente. As fontes do
# Windows que tem (Segoe UI Symbol) nao combinam com o resto, e depender delas
# amarraria o desenho a uma fonte do sistema.
def marca_x(img, cor, grossura, desloca=0):
    d = ImageDraw.Draw(img)
    dm = img.size[0]
    r = dm * 0.22
    c = dm / 2 + desloca
    for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
        d.line([c + a[0] * r, c + a[1] * r, c + b[0] * r, c + b[1] * r],
               fill=cor, width=grossura)
    return img


def marca_engrenagem(img, cor, desloca=0):
    import math
    d = ImageDraw.Draw(img)
    dm = img.size[0]
    cx = cy = dm / 2 + desloca
    r_ext, r_int, dentes = dm * 0.30, dm * 0.20, 8
    pontos = []
    for i in range(dentes * 2):
        ang = math.pi * i / dentes - math.pi / 2
        r = r_ext if i % 2 == 0 else r_int
        pontos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pontos, fill=cor)
    furo = dm * 0.10
    d.ellipse([cx - furo, cy - furo, cx + furo, cy + furo], fill=(0, 0, 0, 0))
    return img


def trio_fechar():
    paradas = [(0.0, (76, 90, 112)), (0.55, (42, 52, 68)), (1.0, (23, 29, 40))]
    for suf, brilho, desl in (('1', 1.0, 0), ('2', 1.25, 0), ('3', 0.85, 1)):
        b = circulo(FECHAR_D, paradas, aro=(190, 225, 255, 71),
                    escala_brilho=brilho, desloca=desl)
        marca_x(b, (234, 250, 255), max(2, int(3 * ESCALA)), desl)
        b.save(IMAGES / ('Exit%s.png' % suf))


def trio_engrenagem():
    paradas = [(0.0, (42, 127, 189)), (1.0, (18, 73, 111))]
    for suf, brilho, desl in (('1', 1.0, 0), ('2', 1.15, 0), ('3', 0.88, 1)):
        b = circulo(BOT_PEQ, paradas, aro=(180, 240, 255, 128),
                    escala_brilho=brilho, desloca=desl)
        marca_engrenagem(b, (234, 250, 255), desl)
        b.save(IMAGES / ('gear%s.png' % suf))


def trio_cancelar():
    """O Cancel ocupa o lugar do START enquanto o patch roda."""
    paradas = [(0.0, (255, 214, 170)), (0.4, (232, 163, 61)),
               (1.0, (150, 92, 20))]
    f = fonte('Cinzel-700.ttf', 20)
    fs = fonte('Barlow-700.ttf', 11)
    for suf, brilho, desl in (('1', 1.0, 0), ('2', 1.1, 0), ('3', 0.9, 1)):
        circulo(START_D, paradas, 'PARAR', 'CANCELAR', f, fs,
                (48, 26, 4), aro=(255, 214, 170, 60),
                escala_brilho=brilho, desloca=desl).save(IMAGES / ('cancel%s.png' % suf))


def barra_progresso():
    w = px(COL_ESQ[1]) - px(COL_ESQ[0])
    h = p(ALT_BARRA)
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=255)
    # o trilho ja esta no bg; o BackImage tem que ser transparente, senao
    # aparece um retangulo por cima do desenho
    Image.new('RGBA', (w, h), (0, 0, 0, 0)).save(IMAGES / 'bar_back.png')
    frente = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    frente.paste(gradiente(w, h, [(0.0, (42, 143, 214)), (1.0, ACENTO)],
                           angulo=90).convert('RGBA'), (0, 0), m)
    frente.save(IMAGES / 'bar_front.png')


# ---------------------------------------------------------------------------
CONFIG_MODELO = """// Configuracao LOCAL do Thor Patcher do %(nome)s.
//
// GERADO por patcher/gerar-visual.py - NAO EDITE A MAO.
// As coordenadas abaixo saem das mesmas constantes que desenham o bg.bmp; foi
// para elas nao desencontrarem que este arquivo passou a ser gerado.
//
// ============================================================
//  O IP DO SERVIDOR SO APARECE NESTE ARQUIVO, em dois pontos: o RootURL e a
//  URL dos NoticeBox. Todos precisam ser absolutos - o NoticeBox e um
//  controle do Internet Explorer e nao herda o RootURL.
//
//  %(ip)s e o endereco Tailscale desta maquina. Ele MUDA se a maquina
//  sair e voltar para a tailnet, se o servidor mudar de host, ou se um dia
//  isso for para um dominio publico. A receita completa de troca esta em
//  docs/cliente/patcher.md - sao cinco lugares, e o exe e um deles.
//
//  O terceiro lugar com o IP e o file_url do patcher/web/main.ini, que fica no
//  SERVIDOR - esse vale para todos os testers assim que for salvo. Ele nao
//  pode ficar vazio: sem ele o patcher trava sem mensagem nenhuma.
// ============================================================

[Config:Main]

RootURL='%(base)s'

RemoteConfigFile='main.ini'

TimeOut=0

StatusFile='server.dat'

DefaultGRF='midgard.grf'

ClientEXE='MidgardEternal.exe'
ClientParameter=''

// Sem servidor no ar o tester ainda consegue entrar e ver a tela de login,
// em vez de ficar preso no patcher.
FinishOnConnectionFailure=true

[Config:Window]

Style='none'

DragHandling=true

// BMP: o pixel do canto superior esquerdo vira a cor transparente. E o que
// da a moldura arredondada e deixa o logo e o botao de fechar transbordarem.
Background='images/bg.bmp'

FadeOnDrag=true

[Config:BGM]
File=''
Loop=true
Volume=5
Directory=

[Config:Misc]
Title='%(nome)s - Atualizador'

HideProgressBarWhenFinish=true


[ProgressBar:bar1]
Width=%(barra_w)d
Height=%(barra_h)d
Left=%(barra_x)d
Top=%(barra_y)d
FrontImage='images/bar_front.png'
BackImage='images/bar_back.png'
Hook='ProgressChange'


[Label:Status]
AutoResize = false
Width=%(rotulo_w)d
Height=
Left=%(rotulo_x)d
Top=%(rotulo_y)d
Alignment='left'

// Delphi le a cor como $BBGGRR, nao $RRGGBB.
FontColor=$FBE6BF
FontName = 'Segoe UI'
FontSize = 9

Text='Pronto para jogar.'

Hook='StatusChange'

// Noticias: abas e banner do evento, em HTML de verdade
[NoticeBox:Box0]
Width=%(nt_w)d
Height=%(nt_h)d
Left=%(nt_x)d
Top=%(nt_y)d
URL='%(base)snotice.html'

// Status do mundo. E um segundo NoticeBox para o painel poder dizer a verdade
// e mudar sem cliente novo - assado no bmp ele mentiria no dia em que o
// servidor caisse.
[NoticeBox:Box1]
Width=%(st_w)d
Height=%(st_h)d
Left=%(st_x)d
Top=%(st_y)d
URL='%(base)sstatus.html'


[Button:Start]
Default='images/start1.png'
OnHover='images/start2.png'
OnDown='images/start3.png'
Left=%(start_x)d
Top=%(start_y)d
Hook='Start'

[Button:Exit]
Default='images/Exit1.png'
OnHover='images/Exit2.png'
OnDown='images/Exit3.png'
Left=%(fechar_x)d
Top=%(fechar_y)d
Hook='Exit'

[Button:Cancel]
// Ocupa o lugar do START enquanto o patch roda
Default='images/cancel1.png'
OnHover='images/cancel2.png'
OnDown='images/cancel3.png'
Left=%(start_x)d
Top=%(start_y)d
Hook='Cancel'

// Engrenagem: abre o opensetup, que e onde se resolve resolucao e VSync.
// Mode=2 executa arquivo; o caminho e relativo a pasta do patcher.
[Button:Config]
Default='images/gear1.png'
OnHover='images/gear2.png'
OnDown='images/gear3.png'
Left=%(gear_x)d
Top=%(gear_y)d
Mode=2
Action='opensetup.exe'
"""


def escrever_config(base_url, ip):
    vals = dict(
        nome=NOME_SERVIDOR, base=base_url, ip=ip,
        barra_x=px(COL_ESQ[0]), barra_y=py(Y_BARRA),
        barra_w=px(COL_ESQ[1]) - px(COL_ESQ[0]), barra_h=p(ALT_BARRA),
        rotulo_x=px(COL_ESQ[0]), rotulo_y=py(Y_BARRA_ROTULO),
        rotulo_w=px(COL_ESQ[1]) - px(COL_ESQ[0]),
        nt_x=px(COL_ESQ[0]), nt_y=py(Y_NOTICE),
        nt_w=px(COL_ESQ[1]) - px(COL_ESQ[0]), nt_h=p(ALT_NOTICE),
        st_x=px(PAINEL[0]), st_y=py(PAINEL[1]),
        st_w=px(PAINEL[2]) - px(PAINEL[0]), st_h=py(PAINEL[3]) - py(PAINEL[1]),
        start_x=px(X_START), start_y=py(Y_BOTOES),
        fechar_x=px(FECHAR[0]), fechar_y=py(FECHAR[1]),
        gear_x=px(X_ENGRENAGEM), gear_y=py(Y_BOTOES + (START_D - BOT_PEQ) // 2),
    )
    (AQUI / 'config.ini').write_text(CONFIG_MODELO % vals, encoding='utf-8')


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    if not FONTES.exists():
        print('AVISO: patcher/fontes/ nao existe - usando fontes do Windows.')
        print('       O desenho NAO vai bater com o design. Rode antes:')
        print('       python patcher/baixar-fontes.py')

    # o endereco atual e preservado do config anterior, para nao voltar sozinho
    antigo = AQUI / 'config.ini'
    base, ip = 'http://100.76.66.99:8099/', '100.76.66.99'
    if antigo.exists():
        import re
        m = re.search(r"(?m)^RootURL\s*=\s*'([^']+)'", antigo.read_text(encoding='utf-8'))
        if m:
            base = m.group(1)
            ip = base.split('//')[-1].split(':')[0].split('/')[0]

    desenhar_fundo().save(IMAGES / 'bg.bmp')
    trio_start()
    trio_fechar()
    trio_engrenagem()
    trio_cancelar()
    barra_progresso()
    escrever_config(base, ip)

    print('janela: %dx%d  (design %dx%d, escala %.2f)'
          % (LARG, ALT, LARG_D, ALT_D, ESCALA))
    print('servidor: %s' % base)
    print('gerado em %s' % IMAGES)
    for f in sorted(IMAGES.iterdir()):
        print('  %-16s %7d bytes' % (f.name, f.stat().st_size))
    print('config.ini reescrito com as coordenadas deste layout')
    return 0


if __name__ == '__main__':
    sys.exit(main())
