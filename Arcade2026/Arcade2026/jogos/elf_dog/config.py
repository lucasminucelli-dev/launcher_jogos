import pygame

pygame.init()

# ================= TELA =================

info_tela = pygame.display.Info()

LARGURA_TELA = info_tela.current_w
ALTURA_TELA = info_tela.current_h

LARGURA_JOGO = 400
ALTURA_JOGO = 900

FPS = 60

# ================= FÍSICA =================

GRAVIDADE = 0.6
FORCA_PULO = -15

VELOCIDADE_HORIZONTAL = 6

# ================= PLAYER =================

PLAYER_LARGURA = 80
PLAYER_ALTURA = 80

# ================= PLATAFORMAS =================

PLAT_LARGURA = 70
PLAT_ALTURA = 15

# ================= CORES =================

BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)

VERDE = (0, 204, 102)
LARANJA = (255, 165, 0)
VERMELHO = (255, 0, 0)