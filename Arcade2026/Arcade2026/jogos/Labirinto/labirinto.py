from gerar_labirinto import gerar_labirinto, pode_mover
import config as cfg

class Labirinto:
    def __init__(self):
        self.mapa = gerar_labirinto(cfg.LARGURA, cfg.ALTURA)

    def gerar(self):
        self.mapa = gerar_labirinto(cfg.LARGURA, cfg.ALTURA)

    def pode_mover(self, x, y, direcao):
        return pode_mover(self.mapa, x, y, direcao)