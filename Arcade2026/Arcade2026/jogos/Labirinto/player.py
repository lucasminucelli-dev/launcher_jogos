from config import *


class Player:

    def __init__(self):

        self.x = 0
        self.y = 0

        self.vidas = VIDAS_INICIAIS

        self.pontos = 0

        self.direcao = "direita"

        self.invencivel = TEMPO_INVENCIVEL

    def mover(self, dx, dy):

        self.x += dx
        self.y += dy

    def adicionar_ponto(self):

        self.pontos += 1

    def perder_vida(self):

        self.vidas -= 1

    def resetar_posicao(self):

        self.x = 0
        self.y = 0