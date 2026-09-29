#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECO NAVE - Desafio do Descarte
==============================
Jogo educativo sobre descarte correto de residuos e conscientizacao
sobre o lixo eletronico.

Uma nave alienigena despeja lixo do alto da tela. Use as SETAS para guiar
cada residuo ate a lixeira da cor certa (padrao de cores da coleta seletiva).
Com o tempo a queda fica cada vez mais rapida.

Como rodar
----------
    pip install pygame        (precisa do pygame 2.x)
    python eco_nave.py

Teclas
------
    <- ->  (ou A / D)   mover o lixo
    v      (ou S)       acelerar a queda
    P / ESC             pausar
    M                   ligar/desligar o som
    F11                 tela cheia
    ENTER               confirmar / jogar

O ranking fica salvo em "ranking.txt", na mesma pasta deste arquivo.
Nenhuma imagem ou som externo e necessario: tudo e desenhado/gerado no codigo.
"""
import array
import csv
import math
import os
import random
import sys
from datetime import datetime

try:
    import pygame
except ImportError:  # pragma: no cover
    print("O pygame nao esta instalado. Instale com:  pip install pygame")
    sys.exit(1)

D = pygame.draw

# ============================================================================
#  CONFIGURACOES
# ============================================================================
TITLE = "ECO NAVE - Desafio do Descarte"
W, H = 1280, 800
FPS = 60

LANES = 10
LANE_W = W // LANES              # largura da "faixa" de cada lixeira (128)
ITEM_SIZE = 84                   # tamanho do lixo na tela
HALF = ITEM_SIZE // 2
PLATE_H = 46                     # placa com o nome da lixeira
PLATE_Y = H - PLATE_H - 8
BIN_BODY_TOP = PLATE_Y - 4 - 80  # topo do corpo da lixeira
BIN_MOUTH_Y = BIN_BODY_TOP - 6   # boca da lixeira
SHIP_Y = 100

START_LIVES = 3
MAX_LIVES = 5
ITEMS_PER_LEVEL = 5              # acertos para subir de nivel
RANKING_SIZE = 10
NAME_MAX = 12


def fall_speed(level):
    """Velocidade de queda (px/s). Sobe pouco a pouco a cada nivel."""
    return min(130 + 10 * (level - 1), 420)


def move_speed(level):
    """Velocidade lateral do lixo (px/s)."""
    return min(470 + 5 * (level - 1), 620)


def spawn_delay(level):
    """Pausa (s) entre um lixo e o proximo."""
    return max(0.35, 0.9 - 0.03 * (level - 1))


# ============================================================================
#  UTILIDADES
# ============================================================================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def shade(c, f):
    return (clamp(int(c[0] * f), 0, 255), clamp(int(c[1] * f), 0, 255), clamp(int(c[2] * f), 0, 255))


def fmt(n):
    return f"{n:,}".replace(",", ".")


def blob(cx, cy, rx, ry, ang_deg, n=32):
    """Pontos de uma elipse rotacionada (eixo 'ry' inclinado 'ang' a partir da vertical)."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        u, v = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + u * ca + v * sa, cy - u * sa + v * ca))
    return pts


def hexagon(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(60 * i) + rot), cy + r * math.sin(math.radians(60 * i) + rot))
            for i in range(6)]


def draw_recycle(surf, cx, cy, r, color, width):
    """Simbolo de reciclagem (tres setas em circulo)."""
    for k in range(3):
        a0 = k * 120 + 12
        a1 = a0 + 78
        pts = []
        for a in range(a0, a1 + 1, 6):
            rad = math.radians(a)
            pts.append((cx + r * math.cos(rad), cy - r * math.sin(rad)))
        D.lines(surf, color, False, pts, max(1, int(width)))
        for p in pts:
            D.circle(surf, color, (int(p[0]), int(p[1])), max(1, int(width / 2)))
        ex, ey = pts[-1]
        ang = math.radians(a1)
        tx, ty = -math.sin(ang), -math.cos(ang)
        nx, ny = -ty, tx
        head = width * 1.9
        tip = (ex + tx * head * 1.3, ey + ty * head * 1.3)
        p1 = (ex + nx * head, ey + ny * head)
        p2 = (ex - nx * head, ey - ny * head)
        D.polygon(surf, color, [tip, p1, p2])


def blit_rotated(surf, image, pos, pivot, angle):
    """Desenha 'image' girada 'angle' graus (anti-horario) em torno do ponto 'pivot' da imagem,
    que fica fixo em 'pos' na tela."""
    image_rect = image.get_rect(topleft=(pos[0] - pivot[0], pos[1] - pivot[1]))
    offset = pygame.math.Vector2(pos) - pygame.math.Vector2(image_rect.center)
    rotated_offset = offset.rotate(-angle)
    center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)
    rotated = pygame.transform.rotate(image, angle)
    surf.blit(rotated, rotated.get_rect(center=center))


# ============================================================================
#  DADOS: LIXEIRAS (na ordem da imagem de referencia)
# ============================================================================
BINS = [
    dict(key="azul",     nome="AZUL",     mat="papel/papelão",      cor=(30, 80, 195),   glow=(80, 140, 255),  txt=(255, 255, 255)),
    dict(key="vermelho", nome="VERMELHO", mat="plástico/isopor",    cor=(212, 38, 46),   glow=(255, 96, 96),   txt=(255, 255, 255)),
    dict(key="verde",    nome="VERDE",    mat="vidro",              cor=(22, 128, 62),   glow=(70, 225, 120),  txt=(255, 255, 255)),
    dict(key="amarelo",  nome="AMARELO",  mat="metal",              cor=(244, 198, 22),  glow=(255, 232, 90),  txt=(70, 50, 0)),
    dict(key="preto",    nome="PRETO",    mat="madeira",            cor=(34, 34, 40),    glow=(160, 160, 185), txt=(255, 255, 255)),
    dict(key="laranja",  nome="LARANJA",  mat="perigosos",          cor=(245, 138, 30),  glow=(255, 185, 90),  txt=(60, 30, 0)),
    dict(key="branco",   nome="BRANCO",   mat="serviços de saúde",  cor=(242, 242, 244), glow=(255, 255, 255), txt=(40, 40, 46)),
    dict(key="roxo",     nome="ROXO",     mat="radioativos",        cor=(124, 80, 170),  glow=(195, 145, 255), txt=(255, 255, 255)),
    dict(key="marrom",   nome="MARROM",   mat="orgânicos",          cor=(148, 88, 48),   glow=(215, 145, 95),  txt=(255, 255, 255)),
    dict(key="cinza",    nome="CINZA",    mat="não recicláveis",    cor=(106, 108, 114), glow=(195, 197, 205), txt=(255, 255, 255)),
]
BIN_INDEX = {b["key"]: i for i, b in enumerate(BINS)}

FACTS = [
    "Celulares e computadores guardam metais valiosos, como cobre, prata e ouro, que podem ser reaproveitados.",
    "Pilhas e baterias têm metais pesados. Jogadas no lixo comum, podem contaminar o solo e a água.",
    "Muitas lojas e fabricantes recebem eletrônicos usados: é a chamada logística reversa.",
    "Consertar, doar ou vender um aparelho antigo evita a geração de lixo eletrônico.",
    "Antes de descartar um celular ou computador, apague todos os seus dados pessoais.",
    "Lâmpadas fluorescentes contêm mercúrio e precisam de descarte específico.",
    "Baterias de lítio danificadas podem pegar fogo. Nunca as jogue no lixo comum.",
    "Reciclar alumínio gasta bem menos energia do que produzir alumínio novo.",
    "O lixo eletrônico é um dos tipos de resíduo que mais crescem no mundo.",
]


# ============================================================================
#  DADOS: ITENS DE LIXO  (cada um tem um desenho feito so com formas do pygame)
#  Canvas de 128x128 px; depois e reduzido com suavizacao para ITEM_SIZE.
# ============================================================================
class ItemDef:
    def __init__(self, bin_index, name, tip, draw, ewaste):
        self.bin_index = bin_index
        self.name = name
        self.tip = tip
        self.draw = draw
        self.ewaste = ewaste


ITEMS = []


def item(bin_key, name, tip, ewaste=False):
    def deco(fn):
        ITEMS.append(ItemDef(BIN_INDEX[bin_key], name, tip, fn, ewaste))
        return fn
    return deco


def rr(s, color, rect, radius=6, outline=None, width=3):
    """Retangulo arredondado com contorno opcional."""
    D.rect(s, color, rect, 0, border_radius=radius)
    if outline is not None:
        D.rect(s, outline, rect, width, border_radius=radius)


def drawn_rotated(s, fn, angle):
    t = pygame.Surface((128, 128), pygame.SRCALPHA)
    fn(t)
    r = pygame.transform.rotate(t, angle)
    s.blit(r, r.get_rect(center=(64, 64)))


# ---------------------------------------------------------------- AZUL ------
@item("azul", "Caixa de papelão", "Papelão limpo e seco é reciclável. Achate a caixa antes de descartar.", True)
def _(s):
    top = [(14, 38), (114, 38), (104, 18), (24, 18)]
    D.rect(s, (190, 140, 85), (14, 38, 100, 72), 0, border_radius=5)
    D.polygon(s, (212, 165, 105), top)
    D.rect(s, (232, 208, 150), (54, 18, 20, 92))
    D.rect(s, (140, 98, 55), (14, 38, 100, 72), 4, border_radius=5)
    D.polygon(s, (140, 98, 55), top, 4)
    rr(s, (245, 240, 225), (80, 76, 26, 22), 2)
    D.line(s, (120, 120, 125), (84, 83), (102, 83), 2)
    D.line(s, (120, 120, 125), (84, 90), (98, 90), 2)


@item("azul", "Manual de instruções", "Manuais em papel podem ser reciclados. Prefira consultar a versão digital!", True)
def _(s):
    rr(s, (240, 238, 228), (28, 12, 72, 104), 5)
    rr(s, (70, 120, 210), (28, 12, 72, 32), 5)
    D.rect(s, (70, 120, 210), (28, 30, 72, 14))
    D.circle(s, (255, 255, 255), (64, 28), 8, 3)
    for i in range(5):
        D.line(s, (150, 150, 158), (40, 58 + i * 11), (88 - (i % 2) * 16, 58 + i * 11), 4)
    D.rect(s, (105, 105, 118), (28, 12, 72, 104), 3, border_radius=5)


@item("azul", "Jornal velho", "Jornais são recicláveis, desde que não estejam molhados nem engordurados.")
def _(s):
    rr(s, (228, 228, 220), (16, 16, 96, 96), 4)
    D.rect(s, (45, 45, 50), (24, 24, 80, 14))
    D.rect(s, (125, 125, 135), (24, 46, 36, 30))
    for i in range(3):
        D.line(s, (95, 95, 100), (66, 50 + i * 10), (104, 50 + i * 10), 3)
    for i in range(4):
        D.line(s, (95, 95, 100), (24, 84 + i * 7), (104, 84 + i * 7), 3)
    D.rect(s, (100, 100, 108), (16, 16, 96, 96), 3, border_radius=4)


@item("azul", "Envelope", "Envelopes de papel comum vão para a reciclagem.")
def _(s):
    rr(s, (246, 242, 226), (12, 30, 104, 70), 5)
    D.polygon(s, (228, 220, 198), [(12, 30), (116, 30), (64, 72)])
    D.line(s, (160, 150, 130), (14, 98), (54, 64), 3)
    D.line(s, (160, 150, 130), (114, 98), (74, 64), 3)
    D.rect(s, (160, 150, 130), (12, 30, 104, 70), 3, border_radius=5)
    D.rect(s, (215, 70, 70), (88, 38, 18, 18))
    D.rect(s, (255, 255, 255), (91, 41, 12, 12), 2)


# ------------------------------------------------------------ VERMELHO ------
@item("vermelho", "Isopor de embalagem", "O isopor leva muito tempo para se decompor. Leve-o a um ponto de reciclagem.")
def _(s):
    D.polygon(s, (238, 238, 242), [(14, 44), (96, 44), (114, 24), (32, 24)])
    D.polygon(s, (196, 198, 206), [(96, 44), (114, 24), (114, 84), (96, 104)])
    D.rect(s, (250, 250, 252), (14, 44, 82, 60))
    rr(s, (218, 220, 228), (28, 56, 54, 36), 4)
    D.rect(s, (170, 172, 182), (14, 44, 82, 60), 3)
    D.polygon(s, (170, 172, 182), [(96, 44), (114, 24), (114, 84), (96, 104)], 3)
    D.polygon(s, (170, 172, 182), [(14, 44), (96, 44), (114, 24), (32, 24)], 3)
    for (x, y) in ((24, 50), (46, 50), (70, 50), (88, 98), (22, 98), (44, 98)):
        D.circle(s, (205, 207, 215), (x, y), 2)


@item("vermelho", "Capa de celular", "Antes de descartar a capa, veja se dá para reutilizar ou doar.", True)
def _(s):
    rr(s, (232, 84, 112), (34, 10, 60, 108), 12, (176, 44, 76), 4)
    rr(s, (58, 22, 34), (42, 18, 28, 28), 8)
    D.circle(s, (130, 130, 145), (52, 28), 6)
    D.circle(s, (130, 130, 145), (60, 38), 6)
    D.rect(s, (255, 160, 180), (80, 30, 6, 52), 0, border_radius=3)


@item("vermelho", "Plástico-bolha", "Plástico de embalagem limpo e seco pode ser reciclado.")
def _(s):
    rr(s, (190, 225, 245), (12, 26, 104, 76), 8)
    for r in range(3):
        for c in range(4):
            cx, cy = 30 + c * 23, 44 + r * 22
            D.circle(s, (218, 240, 253), (cx, cy), 10)
            D.circle(s, (140, 185, 218), (cx, cy), 10, 2)
            D.circle(s, (255, 255, 255), (cx - 3, cy - 3), 3)
    D.rect(s, (120, 165, 200), (12, 26, 104, 76), 3, border_radius=8)


@item("vermelho", "Garrafa PET", "Garrafas PET são muito recicladas. Esvazie e amasse antes de descartar.")
def _(s):
    B = (170, 222, 245)
    O = (90, 150, 185)
    D.rect(s, B, (38, 54, 52, 60), 0, border_radius=8)
    D.polygon(s, B, [(38, 58), (90, 58), (74, 36), (54, 36)])
    D.rect(s, B, (54, 16, 20, 26))
    D.rect(s, (40, 110, 200), (51, 8, 26, 12), 0, border_radius=3)
    D.rect(s, (60, 170, 90), (38, 72, 52, 22))
    D.rect(s, (235, 250, 255), (44, 60, 6, 48), 0, border_radius=3)
    D.rect(s, O, (38, 54, 52, 60), 3, border_radius=8)
    D.polygon(s, O, [(38, 58), (54, 36), (74, 36), (90, 58)], 3)


# --------------------------------------------------------------- VERDE ------
@item("verde", "Garrafa de vidro", "O vidro pode ser reciclado várias vezes sem perder qualidade.")
def _(s):
    G = (46, 150, 80)
    D.rect(s, G, (38, 56, 52, 58), 0, border_radius=8)
    D.polygon(s, G, [(38, 62), (90, 62), (74, 36), (54, 36)])
    D.rect(s, G, (54, 12, 20, 34))
    D.rect(s, shade(G, 0.7), (51, 8, 26, 9), 0, border_radius=3)
    D.rect(s, (238, 236, 214), (38, 76, 52, 20))
    D.rect(s, (130, 215, 150), (45, 64, 7, 44), 0, border_radius=3)
    D.rect(s, shade(G, 0.55), (38, 56, 52, 58), 3, border_radius=8)


@item("verde", "Pote de vidro", "Potes de vidro limpos são recicláveis. Retire a tampa antes de descartar.")
def _(s):
    rr(s, (175, 226, 206), (26, 36, 76, 74), 10, (68, 150, 120))
    rr(s, (150, 206, 186), (32, 24, 64, 16), 4, (68, 150, 120))
    D.rect(s, (232, 252, 242), (35, 48, 8, 50), 0, border_radius=4)
    rr(s, (245, 240, 220), (50, 62, 42, 26), 3)


@item("verde", "Frasco de perfume", "Frascos de vidro são recicláveis. Retire tampa e borrifador antes de descartar.")
def _(s):
    rr(s, (160, 206, 240), (28, 50, 72, 62), 8, (80, 130, 182))
    rr(s, (240, 150, 192), (34, 72, 60, 34), 6)
    rr(s, (50, 50, 62), (50, 20, 28, 28), 4)
    D.rect(s, (190, 192, 204), (56, 46, 16, 8))
    D.rect(s, (232, 246, 255), (37, 56, 6, 44), 0, border_radius=3)


# ------------------------------------------------------------- AMARELO ------
@item("amarelo", "Lata de alumínio", "O alumínio pode ser reciclado muitas vezes, poupando energia e recursos.")
def _(s):
    S = (198, 204, 214)
    D.ellipse(s, shade(S, 0.75), (36, 96, 56, 20))
    D.rect(s, S, (36, 28, 56, 78))
    D.rect(s, (210, 50, 56), (36, 50, 56, 38))
    D.rect(s, (248, 248, 250), (36, 62, 56, 12))
    D.rect(s, (238, 242, 248), (43, 30, 6, 72))
    D.ellipse(s, S, (36, 18, 56, 22))
    D.ellipse(s, (150, 156, 168), (42, 22, 44, 14))
    D.circle(s, (118, 124, 136), (64, 29), 3)


@item("amarelo", "Porca e parafuso", "Sucata de metal pode ser derretida e reaproveitada pela indústria.")
def _(s):
    D.rect(s, (150, 156, 168), (50, 88, 66, 14), 0, border_radius=3)
    for x in range(58, 114, 8):
        D.line(s, (98, 104, 116), (x, 88), (x + 4, 102), 2)
    D.polygon(s, (188, 194, 206), hexagon(38, 95, 20))
    D.polygon(s, (108, 114, 126), hexagon(38, 95, 20), 3)
    D.circle(s, (108, 114, 126), (38, 95), 8, 3)
    nut = hexagon(60, 42, 30, 0.5)
    D.polygon(s, (172, 178, 190), nut)
    D.polygon(s, (108, 114, 126), nut, 3)
    D.circle(s, (0, 0, 0, 0), (60, 42), 13)
    D.circle(s, (108, 114, 126), (60, 42), 13, 3)


@item("amarelo", "Fio de cobre", "O cobre dos fios e cabos é valioso e pode ser reaproveitado.", True)
def _(s):
    C, C2 = (214, 128, 64), (150, 80, 36)
    for i in range(5):
        y = 16 + i * 15
        D.ellipse(s, C2, (14, y, 92, 44), 9)
        D.ellipse(s, C, (14, y, 92, 44), 5)
    D.lines(s, C, False, [(104, 82), (116, 96), (100, 116)], 5)


@item("amarelo", "Dissipador de calor", "Peças de alumínio de computadores antigos podem ser recicladas como metal.", True)
def _(s):
    for i in range(9):
        x = 12 + i * 11
        D.rect(s, (178, 184, 196), (x, 16, 8, 74), 0, border_radius=2)
        D.rect(s, (118, 124, 138), (x + 6, 16, 2, 74))
    rr(s, (152, 158, 170), (8, 86, 112, 24), 4, (100, 106, 120))


# --------------------------------------------------------------- PRETO ------
@item("preto", "Tábuas de madeira", "Sobras de madeira podem ser reutilizadas em móveis, artesanato e reformas.")
def _(s):
    for i, y in enumerate((24, 52, 80)):
        c = shade((156, 104, 60), 0.88 + 0.12 * (i % 2))
        rr(s, c, (10, y, 108, 26), 3, shade(c, 0.62))
        D.line(s, shade(c, 0.75), (22, y + 9), (72, y + 9), 2)
        D.line(s, shade(c, 0.75), (54, y + 18), (104, y + 18), 2)
        D.circle(s, (86, 88, 96), (20, y + 13), 2)
        D.circle(s, (86, 88, 96), (108, y + 13), 2)


@item("preto", "Caixote de madeira", "Caixotes podem ganhar novo uso. Se não der, a madeira segue para reciclagem.")
def _(s):
    D.rect(s, (170, 120, 70), (14, 22, 100, 86))
    for y in (22, 50, 78):
        D.rect(s, (192, 140, 84), (14, y, 100, 30))
        D.rect(s, (112, 72, 40), (14, y, 100, 30), 3)
    D.polygon(s, (146, 98, 56), [(14, 26), (26, 22), (114, 104), (102, 108)])
    D.polygon(s, (112, 72, 40), [(14, 26), (26, 22), (114, 104), (102, 108)], 2)
    D.rect(s, (112, 72, 40), (14, 22, 100, 86), 4)


@item("preto", "Palete de madeira", "Paletes de madeira são muito reaproveitados em móveis e decoração.")
def _(s):
    top = [(22, 16), (108, 16), (118, 34), (10, 34)]
    D.polygon(s, (206, 164, 104), top)
    for k in (0.33, 0.66):
        x0 = lerp(22, 10, 0) + (108 - 22) * k
        D.line(s, (140, 100, 56), (lerp(22, 10, k) + (86 * 0), 16), (lerp(22, 10, k), 34), 1)
    for x in (44, 66, 88):
        D.line(s, (140, 100, 56), (x, 16), (x - 8 + (x - 66) * 0.1, 34), 2)
    D.polygon(s, (140, 100, 56), top, 3)
    D.rect(s, (192, 148, 90), (10, 34, 108, 14))
    D.rect(s, (130, 92, 50), (10, 34, 108, 14), 3)
    for x in (14, 55, 96):
        D.rect(s, (170, 124, 70), (x, 48, 18, 28))
        D.rect(s, (120, 84, 46), (x, 48, 18, 28), 3)
    D.rect(s, (192, 148, 90), (10, 76, 108, 14))
    D.rect(s, (130, 92, 50), (10, 76, 108, 14), 3)


@item("preto", "Tronco de madeira", "Restos de madeira podem ser reaproveitados. Não queime: a fumaça polui o ar.")
def _(s):
    bark = (112, 72, 40)
    D.ellipse(s, shade(bark, 0.9), (10, 32, 26, 64))
    D.rect(s, bark, (22, 32, 66, 64))
    for y in (46, 62, 78):
        D.line(s, shade(bark, 0.7), (26, y), (82, y + 3), 2)
    D.line(s, shade(bark, 0.6), (22, 32), (94, 32), 3)
    D.line(s, shade(bark, 0.6), (22, 96), (94, 96), 3)
    D.ellipse(s, (216, 174, 114), (76, 32, 36, 64))
    D.ellipse(s, (146, 100, 58), (76, 32, 36, 64), 3)
    D.ellipse(s, (172, 126, 74), (83, 41, 22, 46), 2)
    D.ellipse(s, (172, 126, 74), (89, 54, 10, 20), 2)


# ------------------------------------------------------------- LARANJA ------
@item("laranja", "Pilha", "Pilhas têm metais pesados que contaminam solo e água. Use pontos de coleta!", True)
def _(s):
    rr(s, (200, 202, 208), (56, 8, 16, 16), 3)
    rr(s, (32, 34, 40), (40, 20, 48, 100), 8)
    rr(s, (226, 142, 40), (40, 20, 48, 36), 8)
    D.rect(s, (226, 142, 40), (40, 42, 48, 14))
    D.rect(s, (255, 212, 64), (40, 62, 48, 7))
    D.line(s, (255, 255, 255), (64, 82), (64, 102), 4)
    D.line(s, (255, 255, 255), (54, 92), (74, 92), 4)
    D.rect(s, (96, 98, 108), (46, 28, 6, 86), 0, border_radius=3)


@item("laranja", "Bateria de celular", "Baterias de lítio podem pegar fogo se amassadas. Nunca vão no lixo comum!", True)
def _(s):
    rr(s, (74, 84, 100), (20, 26, 88, 76), 8, (42, 50, 62))
    rr(s, (100, 112, 132), (27, 33, 74, 62), 6)
    for x in (34, 58, 82):
        D.rect(s, (232, 192, 62), (x, 102, 12, 10))
    D.polygon(s, (255, 222, 52), [(74, 38), (48, 68), (63, 68), (56, 92), (82, 60), (67, 60), (78, 38)])


@item("laranja", "Lâmpada fluorescente", "Lâmpadas fluorescentes contêm mercúrio, tóxico. Leve a um ponto de coleta.", True)
def _(s):
    D.circle(s, (255, 250, 200), (64, 50), 46)
    for x in (44, 64, 84):
        D.line(s, (222, 224, 200), (x, 80), (x, 28), 14)
        D.circle(s, (222, 224, 200), (x, 28), 7)
        D.line(s, (255, 255, 240), (x, 80), (x, 28), 10)
        D.circle(s, (255, 255, 240), (x, 28), 5)
    rr(s, (236, 236, 226), (34, 74, 60, 22), 4, (150, 150, 140), 2)
    rr(s, (196, 198, 204), (42, 94, 44, 14), 3)
    for x in (48, 58, 68, 78):
        D.line(s, (120, 122, 130), (x, 95), (x, 107), 2)
    rr(s, (60, 62, 68), (54, 108, 20, 10), 3)


@item("laranja", "Cartucho de tinta", "Cartuchos e toners contaminam. Devolva ao fabricante ou à loja.", True)
def _(s):
    rr(s, (60, 62, 76), (22, 24, 84, 68), 6, (36, 38, 48))
    for i, c in enumerate(((0, 190, 232), (232, 44, 142), (250, 222, 34))):
        rr(s, c, (30 + i * 26, 34, 20, 46), 4)
    rr(s, (208, 172, 62), (44, 92, 40, 14), 3)
    D.rect(s, (255, 255, 255), (34, 38, 4, 30), 0, border_radius=2)


# -------------------------------------------------------------- BRANCO ------
@item("branco", "Seringa", "Seringas e agulhas são resíduos de saúde e exigem descarte seguro e especial.")
def _(s):
    def fn(t):
        D.rect(t, (150, 156, 168), (4, 62, 26, 6))
        rr(t, (170, 176, 188), (2, 54, 6, 22), 2)
        rr(t, (244, 246, 250), (28, 50, 64, 28), 6, (100, 110, 124), 2)
        D.rect(t, (120, 202, 232), (36, 57, 46, 14))
        for x in range(42, 88, 9):
            D.line(t, (90, 100, 112), (x, 50), (x, 56 if (x // 9) % 2 else 54), 2)
        rr(t, (244, 246, 250), (24, 44, 6, 40), 2, (100, 110, 124), 2)
        D.polygon(t, (200, 206, 216), [(92, 58), (92, 70), (104, 64)])
        D.line(t, (170, 176, 188), (104, 64), (126, 64), 2)
    drawn_rotated(s, fn, 32)


@item("branco", "Máscara cirúrgica", "Máscaras usadas em serviços de saúde têm descarte próprio, separado do lixo comum.")
def _(s):
    D.ellipse(s, (232, 234, 240), (2, 46, 32, 34), 3)
    D.ellipse(s, (232, 234, 240), (94, 46, 32, 34), 3)
    rr(s, (158, 208, 234), (22, 36, 84, 60), 8, (98, 152, 188))
    for y in (50, 63, 76):
        D.line(s, (118, 170, 206), (24, y), (104, y), 3)
        D.line(s, (196, 232, 248), (24, y + 3), (104, y + 3), 1)
    D.line(s, (240, 242, 248), (40, 40), (88, 40), 3)


@item("branco", "Curativo usado", "Curativos usados em unidades de saúde vão no lixo de serviços de saúde.")
def _(s):
    def fn(t):
        rr(t, (234, 198, 152), (6, 44, 116, 40), 20, (196, 156, 110))
        D.rect(t, (250, 236, 210), (46, 44, 36, 40))
        D.rect(t, (196, 156, 110), (46, 44, 36, 40), 2)
        for x in (22, 32, 42, 86, 96, 106):
            for y in (54, 74):
                D.circle(t, (200, 160, 114), (x, y), 2)
    drawn_rotated(s, fn, 30)


@item("branco", "Luva descartável", "Luvas usadas em atendimentos de saúde exigem descarte separado.")
def _(s):
    C = (122, 192, 232)
    O = (70, 130, 175)
    D.polygon(s, C, blob(28, 76, 10, 18, -50))
    D.polygon(s, O, blob(28, 76, 10, 18, -50), 3)
    for x, top in ((34, 30), (48, 18), (62, 14), (76, 26)):
        rr(s, C, (x, top, 15, 74 - top), 7, O)
    rr(s, C, (34, 60, 57, 46), 12, O)
    D.rect(s, C, (37, 60, 51, 16))
    rr(s, shade(C, 0.82), (34, 102, 57, 16), 4, O)


# --------------------------------------------------------------- ROXO -------
@item("roxo", "Detector de fumaça", "Alguns detectores de fumaça têm uma pequena fonte radioativa. Devolva ao fabricante.", True)
def _(s):
    D.circle(s, (196, 196, 192), (64, 64), 52)
    D.circle(s, (240, 240, 234), (64, 64), 48)
    D.circle(s, (214, 214, 208), (64, 64), 34)
    for k in range(16):
        a = math.radians(k * 22.5)
        D.line(s, (150, 150, 146), (64 + 38 * math.cos(a), 64 + 38 * math.sin(a)),
               (64 + 45 * math.cos(a), 64 + 45 * math.sin(a)), 4)
    D.circle(s, (248, 248, 244), (64, 64), 15)
    D.circle(s, (160, 160, 155), (64, 64), 15, 2)
    D.circle(s, (232, 44, 44), (64, 64), 5)


@item("roxo", "Fonte radioativa", "Materiais radioativos só podem ser descartados por órgãos especializados.")
def _(s):
    D.circle(s, (252, 218, 44), (64, 64), 54)
    D.circle(s, (30, 30, 34), (64, 64), 54, 5)
    r_out, r_in = 38, 15
    for k in range(3):
        base = math.radians(90 + k * 120)
        pts = []
        for j in range(11):
            a = base - math.radians(30) + math.radians(60) * j / 10
            pts.append((64 + r_out * math.cos(a), 64 - r_out * math.sin(a)))
        for j in range(10, -1, -1):
            a = base - math.radians(30) + math.radians(60) * j / 10
            pts.append((64 + r_in * math.cos(a), 64 - r_in * math.sin(a)))
        D.polygon(s, (30, 30, 34), pts)
    D.circle(s, (30, 30, 34), (64, 64), 8)


@item("roxo", "Relógio luminoso antigo", "Relógios antigos com tinta luminosa podiam ter rádio, um material radioativo.", True)
def _(s):
    rr(s, (124, 82, 50), (50, 6, 28, 46), 5, (80, 50, 30), 2)
    rr(s, (124, 82, 50), (50, 76, 28, 46), 5, (80, 50, 30), 2)
    D.circle(s, (192, 194, 200), (64, 64), 42)
    D.circle(s, (110, 112, 120), (64, 64), 42, 3)
    D.circle(s, (22, 48, 34), (64, 64), 35)
    for k in range(12):
        a = math.radians(k * 30)
        r1 = 24 if k % 3 == 0 else 28
        D.line(s, (150, 255, 160), (64 + r1 * math.cos(a), 64 + r1 * math.sin(a)),
               (64 + 31 * math.cos(a), 64 + 31 * math.sin(a)), 4 if k % 3 == 0 else 2)
    D.line(s, (190, 255, 196), (64, 64), (64, 42), 4)
    D.line(s, (190, 255, 196), (64, 64), (82, 72), 3)
    D.circle(s, (190, 255, 196), (64, 64), 4)


# ------------------------------------------------------------- MARROM -------
@item("marrom", "Casca de banana", "Restos de comida viram adubo na compostagem.")
def _(s):
    Y, YO = (246, 212, 62), (190, 146, 22)
    px, py, ry = 64, 22, 46
    for ang in (-42, 42, 0):
        a = math.radians(ang)
        pts = blob(px + math.sin(a) * ry, py + math.cos(a) * ry, 13, ry, ang)
        D.polygon(s, Y, pts)
        D.polygon(s, YO, pts, 3)
        D.line(s, (150, 100, 30), (px + math.sin(a) * ry * 1.7, py + math.cos(a) * ry * 1.7),
               (px + math.sin(a) * ry * 1.85, py + math.cos(a) * ry * 1.85), 5)
    rr(s, (110, 74, 30), (57, 8, 14, 24), 4)
    for (x, y) in ((50, 70), (80, 66), (64, 92), (66, 60)):
        D.circle(s, (170, 120, 40), (x, y), 3)


@item("marrom", "Miolo de maçã", "Orgânicos podem virar adubo. Menos lixo no aterro, mais vida no solo!")
def _(s):
    core = [(44, 24), (84, 24), (70, 64), (84, 104), (44, 104), (58, 64)]
    D.polygon(s, (246, 238, 192), core)
    D.polygon(s, (204, 182, 120), core, 3)
    D.ellipse(s, (212, 52, 52), (34, 12, 60, 32))
    D.ellipse(s, (212, 52, 52), (34, 86, 60, 32))
    D.ellipse(s, (150, 30, 34), (34, 12, 60, 32), 3)
    D.ellipse(s, (150, 30, 34), (34, 86, 60, 32), 3)
    D.ellipse(s, (96, 56, 30), (57, 52, 7, 13))
    D.ellipse(s, (96, 56, 30), (66, 56, 7, 13))
    D.line(s, (96, 66, 34), (64, 14), (72, 2), 4)


@item("marrom", "Folhas", "Folhas e restos de poda são ótimos para a compostagem.")
def _(s):
    def leaf(cx, cy, rx, ry, ang, col, out):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        left, right = [], []
        for i in range(21):
            t = -1 + i * 0.1
            half = rx * (1 - t * t) ** 0.7
            u, v = half, t * ry
            left.append((cx + u * ca + v * sa, cy - u * sa + v * ca))
            u = -half
            right.append((cx + u * ca + v * sa, cy - u * sa + v * ca))
        pts = left + right[::-1]
        D.polygon(s, col, pts)
        D.polygon(s, out, pts, 3)
        D.line(s, out, (cx - math.sin(a) * ry, cy - math.cos(a) * ry),
               (cx + math.sin(a) * ry * 1.25, cy + math.cos(a) * ry * 1.25), 3)
    leaf(46, 62, 24, 46, 32, (96, 178, 72), (52, 116, 46))
    leaf(84, 64, 22, 40, -38, (196, 150, 60), (128, 86, 30))


@item("marrom", "Casca de ovo", "Cascas de ovo são ricas em cálcio e ótimas para a compostagem.")
def _(s):
    D.ellipse(s, (246, 240, 224), (26, 22, 76, 92))
    D.ellipse(s, (196, 184, 156), (26, 22, 76, 92), 3)
    zig = [(130, 56)]
    x = 118
    i = 0
    while x > -6:
        zig.append((x, 54 + (10 if i % 2 else -8)))
        x -= 12
        i += 1
    D.polygon(s, (0, 0, 0, 0), [(0, 0), (130, 0)] + zig + [(-2, 56)])
    D.lines(s, (196, 184, 156), False, zig[1:], 3)


# -------------------------------------------------------------- CINZA -------
@item("cinza", "Guardanapo sujo", "Papel sujo de gordura ou comida não é reciclável. Vai no lixo comum.")
def _(s):
    rnd = random.Random(7)
    pts = []
    for i in range(15):
        a = 2 * math.pi * i / 15
        r = 40 + rnd.randint(-9, 5)
        pts.append((64 + r * math.cos(a), 64 + r * math.sin(a)))
    D.polygon(s, (230, 230, 224), pts)
    D.polygon(s, (150, 150, 146), pts, 3)
    for _i in range(6):
        p1 = (64 + rnd.randint(-28, 28), 64 + rnd.randint(-28, 28))
        p2 = (p1[0] + rnd.randint(-22, 22), p1[1] + rnd.randint(-22, 22))
        D.line(s, (176, 176, 170), p1, p2, 2)
    D.circle(s, (214, 176, 112), (80, 50), 10)
    D.circle(s, (196, 150, 84), (80, 50), 10, 2)
    D.circle(s, (214, 176, 112), (50, 82), 6)


@item("cinza", "Chiclete mascado", "Chiclete não é reciclável: embrulhe em papel e jogue no lixo comum.")
def _(s):
    P = (240, 142, 188)
    blobs = ((58, 68, 34), (86, 58, 24), (44, 92, 20))
    for (x, y, r) in blobs:
        D.circle(s, (176, 84, 128), (x, y), r + 3)
    D.line(s, (176, 84, 128), (100, 78), (120, 102), 9)
    D.line(s, P, (100, 78), (120, 102), 5)
    for (x, y, r) in blobs:
        D.circle(s, P, (x, y), r)
    D.circle(s, (255, 214, 232), (48, 54), 9)
    D.circle(s, (255, 214, 232), (80, 50), 5)


@item("cinza", "Esponja de cozinha", "Esponjas de cozinha são feitas de materiais misturados e não recicláveis.")
def _(s):
    rr(s, (238, 208, 52), (16, 30, 96, 46), 8, (170, 140, 20))
    rr(s, (72, 152, 82), (16, 72, 96, 28), 8, (40, 100, 50))
    for (x, y) in ((32, 44), (56, 54), (84, 42), (98, 58), (44, 64), (72, 66)):
        D.circle(s, (204, 172, 30), (x, y), 4)
    for x in range(26, 104, 10):
        D.line(s, (100, 180, 108), (x, 80), (x + 5, 94), 2)


@item("cinza", "Fita adesiva", "Fita adesiva mistura cola e plástico e não é reciclável.")
def _(s):
    D.polygon(s, (240, 220, 132), [(88, 96), (124, 108), (120, 124), (80, 112)])
    D.polygon(s, (200, 180, 92), [(88, 96), (124, 108), (120, 124), (80, 112)], 2)
    D.circle(s, (240, 220, 132), (58, 60), 46)
    D.circle(s, (0, 0, 0, 0), (58, 60), 24)
    D.circle(s, (200, 180, 92), (58, 60), 46, 3)
    D.circle(s, (200, 180, 92), (58, 60), 24, 3)
    D.circle(s, (255, 246, 196), (58, 60), 37, 3)


# ============================================================================
#  FONTES E TEXTO
# ============================================================================
FONT_NAMES = "segoeui,helveticaneue,arial,dejavusans,liberationsans,freesans"
_FONTS = {}
_TEXTS = {}


def get_font(size, bold=False):
    key = (size, bold)
    f = _FONTS.get(key)
    if f is None:
        try:
            f = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
        except Exception:
            f = pygame.font.Font(None, int(size * 1.25))
        _FONTS[key] = f
    return f


def text_surf(text, size, color, bold=False):
    key = (text, size, color, bold)
    s = _TEXTS.get(key)
    if s is None:
        if len(_TEXTS) > 700:
            _TEXTS.clear()
        s = get_font(size, bold).render(text, True, color)
        _TEXTS[key] = s
    return s


def draw_text(surf, text, size, color, pos, anchor="center", bold=False,
              shadow=None, outline=None, alpha=None, max_w=None):
    """Desenha texto (com cache). Devolve o retangulo ocupado."""
    if max_w:
        while size > 9 and text_surf(text, size, color, bold).get_width() > max_w:
            size -= 1
    img = text_surf(text, size, color, bold)
    rect = img.get_rect()
    setattr(rect, anchor, (int(pos[0]), int(pos[1])))
    if alpha is not None and alpha < 255:
        img = img.copy()
        img.set_alpha(max(0, int(alpha)))
    if outline is not None:
        o = text_surf(text, size, outline, bold)
        if alpha is not None and alpha < 255:
            o = o.copy()
            o.set_alpha(max(0, int(alpha)))
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
            surf.blit(o, (rect.x + dx, rect.y + dy))
    elif shadow is not None:
        o = text_surf(text, size, shadow, bold)
        if alpha is not None and alpha < 255:
            o = o.copy()
            o.set_alpha(max(0, int(alpha)))
        surf.blit(o, (rect.x + 2, rect.y + 2))
    surf.blit(img, rect)
    return rect


def wrap_text(text, size, max_w, bold=False):
    font = get_font(size, bold)
    lines, cur = [], ""
    for word in text.split():
        test = word if not cur else cur + " " + word
        if font.size(test)[0] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_panel(surf, rect, color=(8, 12, 30), alpha=215, border=None, radius=16, bw=2):
    rect = pygame.Rect(rect)
    p = pygame.Surface(rect.size, pygame.SRCALPHA)
    D.rect(p, (color[0], color[1], color[2], alpha), (0, 0, rect.w, rect.h), 0, border_radius=radius)
    if border is not None:
        D.rect(p, border, (0, 0, rect.w, rect.h), bw, border_radius=radius)
    surf.blit(p, rect.topleft)


def draw_keycap(surf, cx, cy, kind, size=34):
    """Tecla desenhada por formas: kind = 'left' | 'right' | 'down'."""
    r = pygame.Rect(0, 0, size, size)
    r.center = (cx, cy)
    D.rect(surf, (28, 36, 64), r.move(0, 3), 0, border_radius=7)
    D.rect(surf, (226, 232, 246), r, 0, border_radius=7)
    D.rect(surf, (120, 132, 170), r, 2, border_radius=7)
    m = size * 0.24
    if kind == "left":
        pts = [(cx - m, cy), (cx + m * 0.8, cy - m), (cx + m * 0.8, cy + m)]
    elif kind == "right":
        pts = [(cx + m, cy), (cx - m * 0.8, cy - m), (cx - m * 0.8, cy + m)]
    else:
        pts = [(cx, cy + m), (cx - m, cy - m * 0.8), (cx + m, cy - m * 0.8)]
    D.polygon(surf, (40, 50, 86), pts)


def draw_keylabel(surf, label, x, y, size=16):
    """Tecla com texto (ENTER, R, ...). (x, y) = canto esquerdo/centro vertical. Devolve a largura."""
    t = text_surf(label, size, (30, 38, 70), True)
    w = t.get_width() + 18
    r = pygame.Rect(x, y - 13, w, 26)
    D.rect(surf, (28, 36, 64), r.move(0, 2), 0, border_radius=6)
    D.rect(surf, (226, 232, 246), r, 0, border_radius=6)
    D.rect(surf, (120, 132, 170), r, 2, border_radius=6)
    surf.blit(t, t.get_rect(center=r.center))
    return w


# ============================================================================
#  GRAFICOS PROCEDURAIS
# ============================================================================
def make_glow(radius, color, max_alpha=90):
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    steps = max(8, radius // 2)
    for i in range(steps):
        r = radius - i * radius / steps
        a = int(max_alpha * ((i + 1) / steps) ** 2)
        D.circle(s, (color[0], color[1], color[2], a), (radius, radius), int(r))
    return s


def make_background():
    bg = pygame.Surface((W, H))
    top, bot = (5, 8, 26), (34, 18, 62)
    for y in range(0, H, 2):
        c = mix(top, bot, (y / H) ** 1.2)
        D.line(bg, c, (0, y), (W, y), 2)
    for (x, y, r, col, a) in ((260, 250, 380, (60, 40, 140), 70), (980, 380, 420, (30, 90, 150), 55),
                             (640, 120, 300, (110, 40, 120), 45)):
        g = make_glow(r, col, a)
        bg.blit(g, (x - r, y - r))
    # lua
    mx, my = 1130, 190
    bg.blit(make_glow(90, (200, 210, 255), 60), (mx - 90, my - 90))
    D.circle(bg, (226, 228, 240), (mx, my), 42)
    for (dx, dy, r) in ((-14, -10, 9), (12, 8, 12), (-6, 18, 6), (16, -18, 5)):
        D.circle(bg, (196, 198, 214), (mx + dx, my + dy), r)
    # chao / painel das lixeiras
    gy = BIN_BODY_TOP - 40
    panel = pygame.Surface((W, H - gy), pygame.SRCALPHA)
    for y in range(H - gy):
        a = int(lerp(0, 235, min(1.0, y / 60.0)))
        D.line(panel, (10, 14, 34, a), (0, y), (W, y))
    bg.blit(panel, (0, gy))
    D.line(bg, (70, 110, 190), (0, gy + 30), (W, gy + 30), 2)
    for i in range(1, LANES):
        D.line(bg, (40, 56, 100), (i * LANE_W, gy + 34), (i * LANE_W, H), 1)
    return bg


def make_lane_glow(color):
    s = pygame.Surface((LANE_W, H), pygame.SRCALPHA)
    for y in range(0, H, 4):
        a = int(105 * (y / H) ** 1.6)
        D.rect(s, (color[0], color[1], color[2], a), (0, y, LANE_W, 4))
    D.line(s, (color[0], color[1], color[2], 150), (0, 0), (0, H), 2)
    D.line(s, (color[0], color[1], color[2], 150), (LANE_W - 1, 0), (LANE_W - 1, H), 2)
    return s


def make_bin_body(b):
    k = 2
    color = b["cor"]
    s = pygame.Surface((88 * k, 80 * k), pygame.SRCALPHA)
    dark = shade(color, 0.55) if b["key"] != "preto" else (110, 112, 130)
    light = mix(color, (255, 255, 255), 0.22)
    poly = [(8 * k, 0), (80 * k, 0), (72 * k, 80 * k), (16 * k, 80 * k)]
    D.polygon(s, color, poly)
    D.polygon(s, light, [(8 * k, 0), (21 * k, 0), (28 * k, 80 * k), (16 * k, 80 * k)])
    for f in (0.2, 0.8):
        x_top, x_bot = 8 + 72 * f, 16 + 56 * f
        D.line(s, shade(color, 0.8), (x_top * k, 4 * k), (x_bot * k, 76 * k), 2 * k)
    sym = (255, 255, 255) if b["key"] not in ("amarelo", "branco", "laranja") else (60, 60, 66)
    if b["key"] == "branco":
        sym = (170, 172, 180)
    draw_recycle(s, 44 * k, 42 * k, 15 * k, sym, 3.4 * k)
    D.polygon(s, dark, poly, 3 * k)
    return pygame.transform.smoothscale(s, (88, 80))


def make_bin_lid(b):
    k = 2
    color = b["cor"]
    s = pygame.Surface((96 * k, 18 * k), pygame.SRCALPHA)
    lid = mix(color, (255, 255, 255), 0.12)
    dark = shade(color, 0.55) if b["key"] != "preto" else (110, 112, 130)
    D.rect(s, lid, (0, 7 * k, 96 * k, 11 * k), 0, border_radius=4 * k)
    D.rect(s, dark, (0, 7 * k, 96 * k, 11 * k), 2 * k, border_radius=4 * k)
    D.rect(s, lid, (34 * k, 0, 28 * k, 11 * k), 0, border_radius=3 * k)
    D.rect(s, dark, (34 * k, 0, 28 * k, 11 * k), 2 * k, border_radius=3 * k)
    return pygame.transform.smoothscale(s, (96, 18))


def make_plate(b):
    s = pygame.Surface((116, PLATE_H), pygame.SRCALPHA)
    edge = mix(b["cor"], (255, 255, 255), 0.35)
    D.rect(s, b["cor"], (0, 0, 116, PLATE_H), 0, border_radius=7)
    D.rect(s, edge, (0, 0, 116, PLATE_H), 2, border_radius=7)
    draw_text(s, b["nome"], 16, b["txt"], (58, 14), "center", bold=True, max_w=104)
    draw_text(s, b["mat"], 13, b["txt"], (58, 32), "center", max_w=106)
    return s


def make_ship_sprite():
    k = 2
    w, h = 180, 110
    s = pygame.Surface((w * k, h * k), pygame.SRCALPHA)

    def E(x, y, ww, hh):
        return (x * k, y * k, ww * k, hh * k)

    cx = 90
    # cupula de vidro
    D.ellipse(s, (150, 214, 240), E(cx - 34, 6, 68, 64))
    D.ellipse(s, (96, 160, 200), E(cx - 34, 6, 68, 64), 3 * k)
    D.ellipse(s, (214, 244, 255), E(cx - 24, 12, 22, 26))
    # alienigena piloto
    D.ellipse(s, (128, 226, 116), E(cx - 14, 30, 28, 32))
    D.ellipse(s, (60, 140, 60), E(cx - 14, 30, 28, 32), 2 * k)
    D.ellipse(s, (20, 40, 20), E(cx - 10, 41, 8, 6))
    D.ellipse(s, (20, 40, 20), E(cx + 2, 41, 8, 6))
    D.line(s, (60, 140, 60), (cx * k, 30 * k), ((cx + 4) * k, 20 * k), 2 * k)
    D.circle(s, (255, 90, 90), ((cx + 4) * k, 19 * k), 3 * k)
    # casco
    D.ellipse(s, (98, 108, 134), E(cx - 60, 62, 120, 40))
    D.ellipse(s, (162, 172, 194), E(cx - 84, 44, 168, 44))
    D.ellipse(s, (230, 236, 248), E(cx - 84, 44, 168, 44), 2 * k)
    D.ellipse(s, (120, 130, 156), E(cx - 84, 62, 168, 22))
    D.ellipse(s, (180, 190, 210), E(cx - 84, 44, 168, 34))
    D.ellipse(s, (232, 238, 250), E(cx - 84, 44, 168, 34), 2 * k)
    # escotilha (por onde cai o lixo)
    D.ellipse(s, (44, 50, 70), E(cx - 16, 88, 32, 12))
    return pygame.transform.smoothscale(s, (w, h))


def make_beam():
    length, top_w = 150, 30
    s = pygame.Surface((140, length), pygame.SRCALPHA)
    for y in range(length):
        half = top_w / 2 + 50 * y / length
        a = int(120 * (1 - y / length) ** 1.3)
        D.line(s, (190, 255, 215, a), (70 - half, y), (70 + half, y))
    return s


def make_heart(size, color, outline):
    k = 3
    s = pygame.Surface((size * k, size * k), pygame.SRCALPHA)
    r = size * 0.27 * k
    cx, cy = size * k / 2, size * k * 0.42
    D.circle(s, color, (cx - r, cy - r * 0.35), r)
    D.circle(s, color, (cx + r, cy - r * 0.35), r)
    D.polygon(s, color, [(cx - 2 * r + 1, cy - r * 0.05), (cx + 2 * r - 1, cy - r * 0.05), (cx, size * k * 0.9)])
    return pygame.transform.smoothscale(s, (size, size))


class Assets:
    def __init__(self):
        self.background = make_background().convert()
        self.dim = pygame.Surface((W, H), pygame.SRCALPHA)
        self.dim.fill((2, 4, 14, 175))
        self.lane_glow = [make_lane_glow(b["glow"]).convert_alpha() for b in BINS]
        self.bin_body = [make_bin_body(b).convert_alpha() for b in BINS]
        self.bin_lid = [make_bin_lid(b).convert_alpha() for b in BINS]
        self.plate = [make_plate(b).convert_alpha() for b in BINS]
        self.ship = make_ship_sprite().convert_alpha()
        self.beam = make_beam().convert_alpha()
        self.heart_full = make_heart(28, (240, 70, 90), (120, 20, 40)).convert_alpha()
        self.heart_empty = make_heart(28, (70, 78, 108), (40, 44, 64)).convert_alpha()
        self.items = []
        for idef in ITEMS:
            canvas = pygame.Surface((128, 128), pygame.SRCALPHA)
            idef.draw(canvas)
            self.items.append(pygame.transform.smoothscale(canvas, (ITEM_SIZE, ITEM_SIZE)).convert_alpha())
        self.item_sprite = {id(idef): spr for idef, spr in zip(ITEMS, self.items)}


# ============================================================================
#  SOM (sintetizado no codigo, sem arquivos externos)
# ============================================================================
class SoundFx:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.fx = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            info = pygame.mixer.get_init()
            if not info or info[1] != -16:
                return
            self.rate, _fmt, self.channels = info
            self.fx = {
                "ok": self._tone([(660, 0.07), (880, 0.13)], "tri", 0.30),
                "bad": self._tone([(190, 0.12), (130, 0.24)], "square", 0.22),
                "level": self._tone([(523, 0.08), (659, 0.08), (784, 0.08), (1046, 0.20)], "tri", 0.30),
                "over": self._tone([(392, 0.18), (330, 0.18), (262, 0.18), (196, 0.45)], "square", 0.20),
                "spawn": self._tone([(360, 0.05), (480, 0.06)], "sine", 0.22),
                "select": self._tone([(620, 0.05)], "tri", 0.25),
            }
            self.enabled = True
        except Exception:
            self.enabled = False

    def _tone(self, notes, wave, vol):
        data = array.array("h")
        for freq, dur in notes:
            n = max(1, int(self.rate * dur))
            attack = max(1, int(self.rate * 0.004))
            for i in range(n):
                ph = (i * freq / self.rate) % 1.0
                if wave == "square":
                    v = 1.0 if ph < 0.5 else -1.0
                elif wave == "tri":
                    v = 4 * abs(ph - 0.5) - 1
                else:
                    v = math.sin(2 * math.pi * ph)
                env = min(1.0, i / attack) * (1 - i / n) ** 0.8
                smp = int(32767 * vol * v * env)
                for _c in range(self.channels):
                    data.append(smp)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def play(self, name):
        if self.enabled and not self.muted:
            try:
                self.fx[name].play()
            except Exception:
                pass

    def toggle(self):
        self.muted = not self.muted
        if not self.muted:
            self.play("select")


# ============================================================================
#  RANKING (arquivo TXT)
# ============================================================================
def ranking_path():
    base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    if not os.access(base, os.W_OK):
        base = os.path.expanduser("~")
    return os.path.join(base, "ranking.txt")


def load_ranking(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            rows = csv.reader(f, delimiter="\t")
            out = []
            for row in rows:
                if len(row) != 4:
                    continue
                name, score, level, date = row
                out.append({"name": name[:NAME_MAX],
                            "score": int(score),
                            "level": int(level),
                            "date": date})
        out.sort(key=lambda e: -e["score"])
        return out[:RANKING_SIZE]
    except Exception:
        return []


def save_ranking(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            for entry in data:
                writer.writerow((entry["name"], entry["score"], entry["level"], entry["date"]))
        os.replace(tmp, path)
        return True
    except Exception:
        return False


# ============================================================================
#  O JOGO
# ============================================================================
FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", None)
TEXT_EV = getattr(pygame, "TEXTINPUT", None)


class Trash:
    """Um lixo em queda."""

    def __init__(self, idef, x, y):
        self.idef = idef
        self.x = x
        self.y = y
        self.age = 0.0
        self.tilt = 0.0
        self.lane = clamp(int(x // LANE_W), 0, LANES - 1)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.scene = pygame.Surface((W, H)).convert()
        self.assets = Assets()
        self.snd = SoundFx()
        self.rank_path = ranking_path()
        self.ranking = load_ranking(self.rank_path)
        self.running = True
        self.state = "menu"
        self.t = 0.0
        self.shake = 0.0
        self.fact = random.choice(FACTS)
        self.new_entry = None
        self.rank_note = ""
        self.name = ""
        self.name_lock = 0.0
        self.stars = [[random.uniform(0, W), random.uniform(0, H), random.choice((1, 1, 2, 2, 3)),
                       random.uniform(6, 26), random.uniform(0, 6.28), random.randint(110, 230)]
                      for _ in range(130)]
        self.menu_items = []
        for _ in range(10):
            self.menu_items.append(self._new_menu_item(random.uniform(-100, H)))
        self.ship_bob = 0.0
        self.reset_game()

    # ------------------------------------------------------------------ setup
    def _new_menu_item(self, y):
        return {"i": random.randrange(len(ITEMS)), "x": random.uniform(40, W - 40), "y": y,
                "vy": random.uniform(30, 80), "rot": random.uniform(0, 360), "vr": random.uniform(-40, 40)}

    def reset_game(self):
        self.score = 0
        self.lives = START_LIVES
        self.streak = 0
        self.best_streak = 0
        self.correct = 0
        self.wrong = 0
        self.level = 1
        self.item = None
        self.item_fx = []
        self.particles = []
        self.popups = []
        self.msg = None
        self.banner = None
        self.hint = None
        self.dying = False
        self.end_timer = 0.0
        self.spawn_timer = 1.1
        self.ship_x = W / 2
        self.ship_target = W / 2
        self.beam_t = 0.0
        self.last_item = None
        self.last_bins = []
        self.bin_open = [0.0] * LANES
        self.bin_bounce = [0.0] * LANES
        self.bin_shake = [0.0] * LANES
        self.shake = 0.0

    def combo_mult(self):
        return 1 + min(self.streak // 5, 4)

    # ---------------------------------------------------------------- eventos
    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
            return
        if FOCUS_LOST is not None and ev.type == FOCUS_LOST and self.state == "playing":
            self.state = "paused"
            return
        if TEXT_EV is not None and ev.type == TEXT_EV and self.state == "name":
            if self.name_lock <= 0:
                for ch in ev.text:
                    if ch.isprintable() and len(self.name) < NAME_MAX:
                        self.name += ch
            return
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key
        if k == pygame.K_F11:
            try:
                pygame.display.toggle_fullscreen()
            except Exception:
                pass
            return
        st = self.state
        if st == "name":
            if k == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.name_lock <= 0:
                self.confirm_name()
            return
        if k == pygame.K_m:
            self.snd.toggle()
            return
        if st == "menu":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif k == pygame.K_r:
                self.new_entry = None
                self.rank_note = ""
                self.state = "ranking"
            elif k == pygame.K_ESCAPE:
                self.running = False
        elif st == "playing":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "paused"
                self.fact = random.choice(FACTS)
        elif st == "paused":
            if k in (pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.state = "playing"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"
        elif st == "ranking":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def start_game(self):
        self.reset_game()
        self.state = "playing"
        self.snd.play("select")

    def _text_input(self, on):
        try:
            if on:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()
        except Exception:
            pass

    def enter_name_state(self):
        self.snd.play("over")
        self.fact = random.choice(FACTS)
        if self.score <= 0:
            self.new_entry = None
            self.rank_note = "Nenhum ponto desta vez. Tente de novo!"
            self.state = "ranking"
            return
        self.name = ""
        self.name_lock = 0.7
        self.state = "name"
        self._text_input(True)

    def confirm_name(self):
        name = self.name.strip() or "Jogador"
        entry = {"name": name, "score": self.score, "level": self.level,
                 "date": datetime.now().strftime("%d/%m/%Y")}
        self.ranking.append(entry)
        self.ranking.sort(key=lambda e: -e["score"])
        self.ranking = self.ranking[:RANKING_SIZE]
        if any(e is entry for e in self.ranking):
            self.new_entry = entry
            self.rank_note = ""
        else:
            self.new_entry = None
            self.rank_note = f"Sua pontuação ({fmt(self.score)}) ficou fora do top {RANKING_SIZE}."
        save_ranking(self.rank_path, self.ranking)
        self._text_input(False)
        self.state = "ranking"

    # ------------------------------------------------------------- atualizacao
    def update(self, dt):
        self.t += dt
        if self.state == "paused":
            return
        for s in self.stars:
            s[1] += s[3] * dt
            if s[1] > H:
                s[1] = 0
                s[0] = random.uniform(0, W)
        if self.state in ("menu", "ranking"):
            self.update_menu(dt)
        elif self.state == "playing":
            self.update_play(dt)
        else:
            if self.name_lock > 0:
                self.name_lock -= dt
            self.update_effects(dt)

    def update_menu(self, dt):
        self.ship_bob += dt
        for m in self.menu_items:
            m["y"] += m["vy"] * dt
            m["rot"] += m["vr"] * dt
            if m["y"] > H + 60:
                m.update(self._new_menu_item(-60))
        self.ship_x = W / 2 + math.sin(self.t * 0.6) * 430

    def update_effects(self, dt):
        for p in self.particles:
            p[4] -= dt
            p[3] += 520 * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
        self.particles = [p for p in self.particles if p[4] > 0]
        for pop in self.popups:
            pop["t"] -= dt
            pop["y"] -= 46 * dt
        self.popups = [p for p in self.popups if p["t"] > 0]
        for fx in self.item_fx:
            fx["t"] += dt
        self.item_fx = [f for f in self.item_fx if f["t"] < f["dur"]]
        self.shake = max(0.0, self.shake - dt)
        for i in range(LANES):
            self.bin_bounce[i] = max(0.0, self.bin_bounce[i] - dt * 3.2)
            self.bin_shake[i] = max(0.0, self.bin_shake[i] - dt * 2.6)
        if self.msg:
            self.msg[3] -= dt
            if self.msg[3] <= 0:
                self.msg = None
        if self.banner:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None
        if self.hint:
            self.hint[1] -= dt
            if self.hint[1] <= 0:
                self.hint = None

    def update_play(self, dt):
        lvl = self.level
        self.ship_bob += dt
        rate = 4.0 + 0.15 * lvl
        self.ship_x += (self.ship_target - self.ship_x) * min(1.0, dt * rate)
        if self.beam_t > 0:
            self.beam_t -= dt
        self.update_effects(dt)
        hover = None
        if self.dying:
            self.end_timer -= dt
            if self.end_timer <= 0:
                self.dying = False
                self.enter_name_state()
        elif self.item is None:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and abs(self.ship_target - self.ship_x) < 40:
                self.spawn_item()
        else:
            it = self.item
            keys = pygame.key.get_pressed()
            right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
            left = keys[pygame.K_LEFT] or keys[pygame.K_a]
            down = keys[pygame.K_DOWN] or keys[pygame.K_s]
            dx = (1 if right else 0) - (1 if left else 0)
            it.age += dt
            it.x = clamp(it.x + dx * move_speed(lvl) * dt, HALF, W - HALF)
            it.tilt += (dx * 12 - it.tilt) * min(1.0, dt * 10)
            it.y += fall_speed(lvl) * (3.2 if down else 1.0) * dt
            it.lane = clamp(int(it.x // LANE_W), 0, LANES - 1)
            hover = it.lane
            if it.y >= BIN_MOUTH_Y - 20:
                self.resolve(it)
                hover = None
        for i in range(LANES):
            target = 1.0 if hover == i else 0.0
            self.bin_open[i] += (target - self.bin_open[i]) * min(1.0, dt * 14)

    def reach(self):
        """Distancia lateral (px) que da tempo de percorrer antes do lixo chegar embaixo.
        Usa so 70% do tempo teorico: sobra margem para o tempo de reacao."""
        fall_time = (BIN_MOUTH_Y - 20 - (SHIP_Y + 50)) / fall_speed(self.level)
        return move_speed(self.level) * fall_time * 0.7

    def pick_item(self, x=None):
        choices = list(range(LANES))
        if x is not None:
            # Justica: so sorteia lixeiras que ainda sao alcancaveis a partir de onde o lixo nasce.
            r = self.reach()
            near = [i for i in choices if abs((i * LANE_W + LANE_W / 2) - x) - LANE_W / 2 <= r]
            if near:
                choices = near
        if len(self.last_bins) >= 2 and self.last_bins[-1] == self.last_bins[-2] and len(choices) > 1 \
                and self.last_bins[-1] in choices:
            choices.remove(self.last_bins[-1])
        b = random.choice(choices)
        pool = [it for it in ITEMS if it.bin_index == b and it is not self.last_item]
        if not pool:
            pool = [it for it in ITEMS if it.bin_index == b]
        idef = random.choices(pool, weights=[2 if it.ewaste else 1 for it in pool])[0]
        self.last_item = idef
        self.last_bins = (self.last_bins + [b])[-3:]
        return idef

    def spawn_item(self):
        x = clamp(self.ship_x, HALF, W - HALF)
        idef = self.pick_item(x)
        self.item = Trash(idef, x, SHIP_Y + 50)
        self.beam_t = 0.35
        self.snd.play("spawn")

    def next_ship_target(self):
        for _ in range(8):
            t = random.uniform(160, W - 160)
            if abs(t - self.ship_x) > 240:
                break
        self.ship_target = t

    # ---------------------------------------------------------------- resolucao
    def resolve(self, it):
        lane = it.lane
        idef = it.idef
        correct = (lane == idef.bin_index)
        cx = lane * LANE_W + LANE_W // 2
        sprite = self.assets.item_sprite[id(idef)]
        if correct:
            old_level = self.level
            self.correct += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            mult = self.combo_mult()
            pts = (100 + 10 * (old_level - 1)) * mult
            self.score += pts
            self.level = 1 + self.correct // ITEMS_PER_LEVEL
            self.bin_bounce[lane] = 1.0
            self.confetti(cx, BIN_MOUTH_Y, BINS[lane]["glow"], 30)
            self.popups.append({"text": f"+{fmt(pts)}", "x": cx, "y": BIN_MOUTH_Y - 34, "t": 1.0, "dur": 1.0,
                                "color": (150, 255, 170), "size": 30})
            self.msg = [f"Certo! {idef.name} vai na lixeira {BINS[lane]['nome']}.", idef.tip, "ok", 4.2]
            self.snd.play("ok")
            if self.level > old_level:
                self.banner = [f"NÍVEL {self.level}", "A nave está mais rápida!", 1.8]
                self.snd.play("level")
            if self.streak % 10 == 0 and self.lives < MAX_LIVES:
                self.lives += 1
                self.popups.append({"text": "+1 vida", "x": cx, "y": BIN_MOUTH_Y - 70, "t": 1.4, "dur": 1.4,
                                    "color": (255, 140, 170), "size": 26})
            self.item_fx.append({"spr": sprite, "x": it.x, "y": it.y, "tx": cx, "ty": BIN_BODY_TOP + 34,
                                 "t": 0.0, "dur": 0.28, "ok": True, "vx": 0.0, "tilt": it.tilt})
        else:
            self.wrong += 1
            self.streak = 0
            self.lives -= 1
            right_bin = idef.bin_index
            self.bin_shake[lane] = 1.0
            self.shake = 0.35
            self.sparks(cx, BIN_MOUTH_Y, (255, 90, 90), 22)
            self.popups.append({"text": "Errou!", "x": cx, "y": BIN_MOUTH_Y - 34, "t": 1.0, "dur": 1.0,
                                "color": (255, 120, 120), "size": 30})
            self.msg = [f"Ops! {idef.name} vai na lixeira {BINS[right_bin]['nome']}.", idef.tip, "bad", 5.0]
            self.hint = [right_bin, 2.2]
            self.snd.play("bad")
            self.item_fx.append({"spr": sprite, "x": it.x, "y": it.y, "tx": it.x, "ty": it.y,
                                 "t": 0.0, "dur": 0.7, "ok": False, "vx": random.uniform(-170, 170),
                                 "tilt": it.tilt})
        self.item = None
        if self.lives <= 0:
            self.dying = True
            self.end_timer = 1.4
        else:
            self.spawn_timer = spawn_delay(self.level)
            self.next_ship_target()

    def confetti(self, x, y, color, n):
        cols = (color, (255, 255, 255), mix(color, (255, 255, 255), 0.5), (255, 230, 90))
        for _ in range(n):
            a = math.radians(random.uniform(-165, -15))
            sp = random.uniform(140, 430)
            self.particles.append([x + random.uniform(-20, 20), y, math.cos(a) * sp, math.sin(a) * sp,
                                   random.uniform(0.6, 1.1), random.choice(cols), random.randint(4, 8), 1.1])

    def sparks(self, x, y, color, n):
        for _ in range(n):
            a = math.radians(random.uniform(-170, -10))
            sp = random.uniform(120, 360)
            self.particles.append([x + random.uniform(-16, 16), y, math.cos(a) * sp, math.sin(a) * sp,
                                   random.uniform(0.4, 0.8), random.choice((color, (255, 190, 90), (90, 90, 96))),
                                   random.randint(3, 6), 0.8])

    # ------------------------------------------------------------------ desenho
    def draw(self):
        surf = self.scene
        if self.state == "menu":
            self.draw_menu(surf)
        elif self.state == "ranking":
            self.draw_backdrop(surf)
            self.draw_ranking(surf)
        else:
            self.draw_world(surf)
            if self.state == "paused":
                self.draw_pause(surf)
            elif self.state == "name":
                self.draw_name(surf)
        ox = oy = 0
        if self.shake > 0 and self.state == "playing":
            amp = 9 * min(1.0, self.shake / 0.35)
            ox, oy = random.randint(-int(amp), int(amp)), random.randint(-int(amp), int(amp))
            self.screen.fill((0, 0, 0))
        self.screen.blit(surf, (ox, oy))

    def draw_stars(self, surf):
        t = self.t
        for x, y, sz, _sp, ph, base in self.stars:
            b = int(base * (0.65 + 0.35 * math.sin(t * 2.0 + ph)))
            surf.fill((b, b, min(255, b + 25)), (int(x), int(y), sz, sz))

    def draw_ship(self, surf, cx, cy, with_beam=True):
        a = self.assets
        if with_beam and self.beam_t > 0:
            p = clamp(self.beam_t / 0.35, 0.0, 1.0)
            a.beam.set_alpha(int(255 * p))
            surf.blit(a.beam, (int(cx) - 70, int(cy) + 38))
        surf.blit(a.ship, (int(cx) - 90, int(cy) - 55))
        cols = ((255, 224, 90), (110, 240, 255), (255, 120, 190))
        for i in range(7):
            dx = -60 + i * 20
            ly = 64 + 10 * (1 - (dx / 88.0) ** 2) ** 0.5
            on = (int(self.t * 4) + i) % 2 == 0
            col = cols[i % 3] if on else (90, 96, 120)
            D.circle(surf, col, (int(cx + dx), int(cy - 55 + ly)), 4)

    def draw_world(self, surf):
        a = self.assets
        surf.blit(a.background, (0, 0))
        self.draw_stars(surf)
        it = self.item
        hover = None
        if it is not None:
            hover = it.lane
            surf.blit(a.lane_glow[it.lane], (it.lane * LANE_W, 0))
        cy = SHIP_Y + math.sin(self.ship_bob * 2.4) * 4
        self.draw_ship(surf, self.ship_x, cy)
        if it is not None:
            self.draw_item(surf, it)
        self.draw_item_fx(surf)
        self.draw_bins(surf, hover)
        self.draw_particles(surf)
        self.draw_popups(surf)
        self.draw_hud(surf)
        self.draw_message(surf)
        self.draw_banner(surf)

    def draw_item(self, surf, it):
        spr = self.assets.item_sprite[id(it.idef)]
        scale = min(1.0, 0.45 + it.age * 3.0)
        img = spr
        if scale < 1.0:
            sz = max(4, int(ITEM_SIZE * scale))
            img = pygame.transform.smoothscale(spr, (sz, sz))
        if abs(it.tilt) > 0.6:
            img = pygame.transform.rotate(img, -it.tilt)
        surf.blit(img, img.get_rect(center=(int(it.x), int(it.y))))
        draw_text(surf, it.idef.name, 17, (255, 255, 255), (it.x, it.y + HALF + 12), "center",
                  bold=True, shadow=(0, 0, 0), max_w=190)

    def draw_item_fx(self, surf):
        for fx in self.item_fx:
            p = clamp(fx["t"] / fx["dur"], 0.0, 1.0)
            spr = fx["spr"]
            if fx["ok"]:
                e = p * p * (3 - 2 * p)
                x = lerp(fx["x"], fx["tx"], e)
                y = lerp(fx["y"], fx["ty"], e)
                sz = max(4, int(ITEM_SIZE * lerp(1.0, 0.35, e)))
                img = pygame.transform.smoothscale(spr, (sz, sz))
            else:
                t = fx["t"]
                x = fx["x"] + fx["vx"] * t
                y = fx["y"] - 300 * t + 760 * t * t
                img = pygame.transform.rotate(spr, t * 420)
                img.set_alpha(int(255 * (1 - p)))
            surf.blit(img, img.get_rect(center=(int(x), int(y))))

    def draw_bins(self, surf, hover):
        a = self.assets
        for i, b in enumerate(BINS):
            cx = i * LANE_W + LANE_W // 2
            ox = math.sin(self.t * 70) * 7 * self.bin_shake[i]
            oy = -abs(math.sin(self.bin_bounce[i] * math.pi)) * 9
            top = BIN_BODY_TOP + oy
            surf.blit(a.bin_body[i], (cx - 44 + ox, top))
            op = self.bin_open[i]
            if op > 0.05:
                D.ellipse(surf, (6, 8, 12), (cx - 31 + ox, top - 5, 62, 12))
            blit_rotated(surf, a.bin_lid[i], (cx - 45 + ox, top + 1), (3, 15), op * 62)
            surf.blit(a.plate[i], (cx - 58, PLATE_Y))
            if hover == i:
                D.rect(surf, (255, 255, 255), (cx - 58, PLATE_Y, 116, PLATE_H), 3, border_radius=7)
        if self.hint:
            i = self.hint[0]
            cx = i * LANE_W + LANE_W // 2
            pulse = 0.5 + 0.5 * math.sin(self.t * 12)
            col = mix(BINS[i]["glow"], (255, 255, 255), pulse)
            D.rect(surf, col, (cx - 62, BIN_BODY_TOP - 30, 124, PLATE_Y + PLATE_H - BIN_BODY_TOP + 36), 4,
                   border_radius=14)

    def draw_particles(self, surf):
        for x, y, _vx, _vy, life, col, sz, mx in self.particles:
            k = clamp(life / mx, 0.0, 1.0)
            s = max(1, int(sz * k + 1))
            surf.fill(col, (int(x), int(y), s, s))

    def draw_popups(self, surf):
        for p in self.popups:
            k = clamp(p["t"] / p["dur"], 0.0, 1.0)
            draw_text(surf, p["text"], p["size"], p["color"], (p["x"], p["y"]), "center", bold=True,
                      outline=(10, 14, 30), alpha=255 * min(1.0, k * 2.5))

    def draw_hud(self, surf):
        a = self.assets
        draw_text(surf, "PONTOS", 15, (150, 172, 214), (24, 8), "topleft", bold=True)
        sc = fmt(self.score)
        draw_text(surf, sc, 40, (255, 255, 255), (24, 22), "topleft", bold=True, shadow=(0, 0, 0))
        mult = self.combo_mult()
        if mult > 1:
            w = text_surf(sc, 40, (255, 255, 255), True).get_width()
            draw_text(surf, f"COMBO x{mult}", 20, (255, 214, 80), (24 + w + 14, 40), "topleft",
                      bold=True, shadow=(0, 0, 0))
        draw_text(surf, f"NÍVEL {self.level}", 26, (255, 255, 255), (W - 24, 8), "topright", bold=True,
                  shadow=(0, 0, 0))
        bw = 118
        bx, by = W - 24 - bw, 44
        D.rect(surf, (40, 50, 84), (bx, by, bw, 9), 0, border_radius=4)
        prog = (self.correct % ITEMS_PER_LEVEL) / ITEMS_PER_LEVEL
        if prog > 0:
            D.rect(surf, (110, 240, 150), (bx, by, int(bw * prog), 9), 0, border_radius=4)
        n = max(START_LIVES, self.lives)
        hx = bx - 18 - n * 30
        for i in range(n):
            surf.blit(a.heart_full if i < self.lives else a.heart_empty, (hx + i * 30, 10))

    def draw_message(self, surf):
        if not self.msg:
            return
        title, tip, kind, t = self.msg
        alpha = 1.0 if t > 0.5 else max(0.0, t / 0.5)
        col = (130, 245, 160) if kind == "ok" else (255, 130, 130)
        pw, ph = 620, 58
        pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
        D.rect(pill, (8, 12, 30, 220), (0, 0, pw, ph), 0, border_radius=14)
        D.rect(pill, col, (0, 0, pw, ph), 2, border_radius=14)
        draw_text(pill, title, 20, col, (pw // 2, 18), "center", bold=True, max_w=pw - 30)
        draw_text(pill, tip, 16, (222, 230, 246), (pw // 2, 41), "center", max_w=pw - 24)
        pill.set_alpha(int(255 * alpha))
        surf.blit(pill, ((W - pw) // 2, 6))

    def draw_banner(self, surf):
        if not self.banner:
            return
        text, sub, t = self.banner
        p = clamp(t / 1.8, 0.0, 1.0)
        al = 255 * min(1.0, p * 3.0)
        y = 290 - (1 - p) * 30
        draw_text(surf, text, 84, (255, 236, 110), (W // 2, y), "center", bold=True, outline=(20, 16, 40), alpha=al)
        draw_text(surf, sub, 28, (255, 255, 255), (W // 2, y + 58), "center", bold=True, outline=(20, 16, 40),
                  alpha=al)

    # ---------------------------------------------------------------------- menu
    def draw_backdrop(self, surf):
        a = self.assets
        surf.blit(a.background, (0, 0))
        self.draw_stars(surf)
        for m in self.menu_items:
            img = pygame.transform.rotate(a.items[m["i"]], m["rot"])
            img.set_alpha(120)
            surf.blit(img, img.get_rect(center=(int(m["x"]), int(m["y"]))))

    def draw_menu(self, surf):
        a = self.assets
        self.draw_backdrop(surf)
        self.beam_t = 0.0
        self.draw_ship(surf, self.ship_x, 66 + math.sin(self.ship_bob * 2.4) * 4, with_beam=False)
        # titulo
        draw_text(surf, "ECO NAVE", 108, (112, 244, 158), (W // 2, 178), "center", bold=True, outline=(8, 40, 30))
        draw_text(surf, "Desafio do Descarte Consciente", 32, (226, 236, 255), (W // 2, 252), "center",
                  bold=True, shadow=(0, 0, 0))
        # como jogar
        draw_panel(surf, (230, 290, 820, 128), border=(70, 110, 190))
        draw_keycap(surf, 300, 328, "left")
        draw_keycap(surf, 342, 328, "right")
        draw_text(surf, "mova o lixo para os lados", 20, (230, 236, 250), (368, 328), "midleft")
        draw_keycap(surf, 690, 328, "down")
        draw_text(surf, "acelera a queda", 20, (230, 236, 250), (716, 328), "midleft")
        draw_text(surf, "Leve cada resíduo até a lixeira da cor certa. Errou 3 vezes? Fim de jogo!", 19,
                  (200, 214, 240), (W // 2, 366), "center")
        draw_text(surf, "Lixo eletrônico não é lixo comum: pilhas, baterias e lâmpadas vão para pontos de coleta!",
                  19, (130, 245, 160), (W // 2, 396), "center", bold=True, max_w=780)
        # chamada
        pulse = 0.5 + 0.5 * math.sin(self.t * 4)
        col = mix((255, 255, 255), (255, 232, 110), pulse)
        draw_text(surf, "Pressione ENTER para jogar", 34, col, (W // 2, 456), "center", bold=True, shadow=(0, 0, 0))
        # atalhos
        items = [("R", "Ranking"), ("M", "Som: " + ("desligado" if self.snd.muted else "ligado")),
                 ("F11", "Tela cheia"), ("ESC", "Sair")]
        total = 0
        for k, txt in items:
            total += text_surf(k, 16, (30, 38, 70), True).get_width() + 18 + 8 + \
                text_surf(txt, 17, (210, 220, 240)).get_width() + 34
        x = (W - total + 34) // 2
        for k, txt in items:
            w = draw_keylabel(surf, k, x, 510)
            r = draw_text(surf, txt, 17, (210, 220, 240), (x + w + 8, 510), "midleft")
            x = r.right + 34
        self.draw_bins(surf, None)

    # -------------------------------------------------------------------- overlays
    def draw_pause(self, surf):
        surf.blit(self.assets.dim, (0, 0))
        draw_panel(surf, (W // 2 - 340, 200, 680, 290), border=(70, 110, 190))
        draw_text(surf, "PAUSADO", 64, (255, 255, 255), (W // 2, 262), "center", bold=True, shadow=(0, 0, 0))
        x = W // 2 - 250
        w = draw_keylabel(surf, "P", x, 330)
        draw_text(surf, "continuar", 20, (226, 234, 250), (x + w + 10, 330), "midleft")
        x2 = W // 2 + 30
        w = draw_keylabel(surf, "ESC", x2, 330)
        draw_text(surf, "voltar ao menu", 20, (226, 234, 250), (x2 + w + 10, 330), "midleft")
        draw_text(surf, "VOCÊ SABIA?", 15, (130, 245, 160), (W // 2, 382), "center", bold=True)
        for i, line in enumerate(wrap_text(self.fact, 20, 600)[:3]):
            draw_text(surf, line, 20, (222, 230, 246), (W // 2, 414 + i * 26), "center")

    def draw_name(self, surf):
        surf.blit(self.assets.dim, (0, 0))
        pw, ph = 780, 470
        px, py = (W - pw) // 2, (H - ph) // 2 - 10
        draw_panel(surf, (px, py, pw, ph), border=(255, 130, 130), bw=3)
        cx = W // 2
        draw_text(surf, "FIM DE JOGO", 58, (255, 120, 120), (cx, py + 52), "center", bold=True, shadow=(0, 0, 0))
        draw_text(surf, "SUA PONTUAÇÃO", 16, (150, 172, 214), (cx, py + 104), "center", bold=True)
        draw_text(surf, fmt(self.score), 60, (255, 255, 255), (cx, py + 144), "center", bold=True, shadow=(0, 0, 0))
        tot = self.correct + self.wrong
        acc = int(100 * self.correct / tot) if tot else 0
        stats = f"Nível {self.level}   ·   Acertos {self.correct}   ·   Precisão {acc}%   ·   Melhor sequência {self.best_streak}"
        draw_text(surf, stats, 19, (214, 224, 244), (cx, py + 196), "center", max_w=pw - 40)
        draw_text(surf, "Digite seu nome e pressione ENTER", 22, (255, 255, 255), (cx, py + 240), "center", bold=True)
        box = pygame.Rect(0, 0, 440, 58)
        box.center = (cx, py + 296)
        D.rect(surf, (16, 22, 48), box, 0, border_radius=10)
        D.rect(surf, (110, 240, 150), box, 3, border_radius=10)
        caret = "|" if int(self.t * 2) % 2 == 0 else " "
        draw_text(surf, self.name + caret, 34, (255, 255, 255), box.center, "center", bold=True, max_w=420)
        draw_text(surf, f"{len(self.name)}/{NAME_MAX}", 14, (130, 145, 180), (box.right - 8, box.bottom + 12), "midright")
        draw_text(surf, "VOCÊ SABIA?", 15, (130, 245, 160), (cx, py + 372), "center", bold=True)
        for i, line in enumerate(wrap_text(self.fact, 19, pw - 90)[:2]):
            draw_text(surf, line, 19, (222, 230, 246), (cx, py + 400 + i * 25), "center")

    def draw_ranking(self, surf):
        surf.blit(self.assets.dim, (0, 0))
        cx = W // 2
        draw_text(surf, "RANKING", 64, (255, 226, 110), (cx, 62), "center", bold=True, outline=(40, 30, 10))
        pw = 800
        px = (W - pw) // 2
        draw_panel(surf, (px, 112, pw, 462), border=(70, 110, 190))
        hy = 138
        draw_text(surf, "#", 15, (150, 172, 214), (px + 30, hy), "midleft", bold=True)
        draw_text(surf, "NOME", 15, (150, 172, 214), (px + 80, hy), "midleft", bold=True)
        draw_text(surf, "NÍVEL", 15, (150, 172, 214), (px + 430, hy), "center", bold=True)
        draw_text(surf, "DATA", 15, (150, 172, 214), (px + 560, hy), "center", bold=True)
        draw_text(surf, "PONTOS", 15, (150, 172, 214), (px + pw - 30, hy), "midright", bold=True)
        if not self.ranking:
            draw_text(surf, "Ainda não há pontuações. Seja o primeiro!", 24, (226, 234, 250), (cx, 340), "center")
        for i, e in enumerate(self.ranking):
            y = 176 + i * 38
            mine = e is self.new_entry
            if mine:
                pulse = 0.5 + 0.5 * math.sin(self.t * 6)
                D.rect(surf, mix((30, 70, 60), (60, 140, 100), pulse), (px + 12, y - 17, pw - 24, 34), 0,
                       border_radius=8)
            elif i % 2 == 0:
                D.rect(surf, (18, 26, 54), (px + 12, y - 17, pw - 24, 34), 0, border_radius=8)
            if i < 3:
                rc = ((255, 214, 70), (208, 214, 226), (222, 150, 90))[i]
            else:
                rc = (200, 210, 235)
            tc = (255, 255, 255) if not mine else (170, 255, 190)
            draw_text(surf, str(i + 1), 24, rc, (px + 30, y), "midleft", bold=True)
            draw_text(surf, e["name"], 24, tc, (px + 80, y), "midleft", bold=mine, max_w=300)
            draw_text(surf, str(e["level"]), 22, (200, 210, 235), (px + 430, y), "center")
            draw_text(surf, e["date"], 18, (150, 165, 200), (px + 560, y), "center")
            draw_text(surf, fmt(e["score"]), 26, tc, (px + pw - 30, y), "midright", bold=True)
        if self.rank_note:
            draw_text(surf, self.rank_note, 22, (255, 200, 130), (cx, 604), "center", bold=True)
        elif self.new_entry is not None:
            draw_text(surf, "Parabéns! Você entrou no ranking!", 22, (170, 255, 190), (cx, 604), "center", bold=True)
        w1 = 18 + text_surf("ENTER", 16, (30, 38, 70), True).get_width() + 10 + \
            text_surf("jogar de novo", 20, (226, 234, 250)).get_width()
        w2 = 18 + text_surf("ESC", 16, (30, 38, 70), True).get_width() + 10 + \
            text_surf("menu", 20, (226, 234, 250)).get_width()
        x = (W - (w1 + 44 + w2)) // 2
        w = draw_keylabel(surf, "ENTER", x, 656)
        r = draw_text(surf, "jogar de novo", 20, (226, 234, 250), (x + w + 10, 656), "midleft")
        w = draw_keylabel(surf, "ESC", r.right + 44, 656)
        draw_text(surf, "menu", 20, (226, 234, 250), (r.right + 44 + w + 10, 656), "midleft")

    # ---------------------------------------------------------------- laco principal
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = min(clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                self.handle_event(ev)
            self.update(dt)
            self.draw()
            pygame.display.flip()


def main():
    if pygame.version.vernum[0] < 2:
        print("Este jogo precisa do pygame 2.x. Atualize com:  pip install --upgrade pygame")
        sys.exit(1)
    try:
        pygame.mixer.pre_init(22050, -16, 1, 512)
    except Exception:
        pass
    pygame.init()
    pygame.display.set_caption(TITLE)
    flags = pygame.SCALED | pygame.RESIZABLE
    try:
        screen = pygame.display.set_mode((W, H), flags, vsync=1)
    except Exception:
        try:
            screen = pygame.display.set_mode((W, H), flags)
        except Exception:
            screen = pygame.display.set_mode((W, H))
    Game(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
