import pygame

from config import *


class Platform:

    def __init__(
        self,
        x,
        y,
        quebravel=False,
        movendo=False,
        velocidade=0
    ):

        self.x = x
        self.y = y

        self.dano = 0

        self.quebravel = quebravel

        self.movendo = movendo
        self.velocidade = velocidade

    def update(self):

        if self.movendo:

            self.x += self.velocidade

            if self.x <= 0:
                self.velocidade *= -1

            elif self.x + PLAT_LARGURA >= LARGURA_JOGO:
                self.velocidade *= -1

    def draw(self, superficie):

        if not self.quebravel:

            cor = VERDE

        else:

            if self.dano == 0:
                cor = LARANJA

            elif self.dano == 1:
                cor = (255, 120, 0)

            else:
                cor = VERMELHO

        pygame.draw.rect(
            superficie,
            cor,
            (
                self.x,
                self.y,
                PLAT_LARGURA,
                PLAT_ALTURA
            )
        )

    def get_rect(self):

        return pygame.Rect(
            self.x,
            self.y,
            PLAT_LARGURA,
            PLAT_ALTURA
        )