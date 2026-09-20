import pygame as pg

# Dimensões base e Tempos
TAMANHO_CELULA = 64
LARGURA = 18
ALTURA = 12
FPS = 18
ALTURA_HUD = 92
TEMPO_JOGADOR = 2
TEMPO_INIMIGO = 5
VIDAS_INICIAIS = 3
TEMPO_INVENCIVEL = 18
SEGUNDOS_PARA_MUDAR_LABIRINTO = 18
AVISO_MUDANCA_LABIRINTO = 4

# Cores
PRETO = (0, 0, 0)
FUNDO = (0, 0, 0)
CHAO_1 = (0, 0, 0)
CHAO_2 = (0, 0, 0)
AZUL = (43, 99, 255)
AZUL_CLARO = (79, 164, 255)
AZUL_ESCURO = (11, 36, 145)
AMARELO = (255, 219, 67)
AMARELO_CLARO = (255, 238, 91)
AMARELO_ESCURO = (255, 188, 24)
BRANCO = (245, 245, 245)
VERMELHO = (255, 80, 142)
ROSA = (255, 80, 142)
ROSA_CLARO = (255, 138, 180)
ROSA_ESCURO = (202, 55, 112)
CIANO = (72, 197, 216)
LARANJA = (255, 166, 74)
MARROM = (255, 222, 174)
VERDE = (88, 186, 103)
ROXO = (160, 112, 224)
TERRA = (20, 20, 20)
FLOR = (255, 80, 142)

# Controles
TECLAS_DIRECAO = {
    pg.K_LEFT: "esquerda",
    pg.K_a: "esquerda",
    pg.K_RIGHT: "direita",
    pg.K_d: "direita",
    pg.K_UP: "cima",
    pg.K_w: "cima",
    pg.K_DOWN: "baixo",
    pg.K_s: "baixo",
}

TECLAS_SEGURADAS = [
    (pg.K_LEFT, "esquerda"),
    (pg.K_a, "esquerda"),
    (pg.K_RIGHT, "direita"),
    (pg.K_d, "direita"),
    (pg.K_UP, "cima"),
    (pg.K_w, "cima"),
    (pg.K_DOWN, "baixo"),
    (pg.K_s, "baixo"),
]

ANGULOS_BOCA = {
    "direita": (35, 325),
    "esquerda": (215, 145),
    "cima": (125, 55),
    "baixo": (305, 235),
}