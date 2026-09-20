import pygame

from config import *


class Player:

    def __init__(self, imagem):

        self.imagem = imagem

        self.x = LARGURA_JOGO // 2
        self.y = ALTURA_JOGO - 150

        self.vel_x = 0
        self.vel_y = 0

    def update(self):

        self.vel_y += GRAVIDADE

        self.x += self.vel_x
        self.y += self.vel_y

        if self.x > LARGURA_JOGO:
            self.x = -PLAYER_LARGURA

        elif self.x < -PLAYER_LARGURA:
            self.x = LARGURA_JOGO

    def jump(self):

        self.vel_y = FORCA_PULO

    def draw(self, superficie):

        superficie.blit(
            self.imagem,
            (self.x, self.y)
        )

    def get_rect(self):

        return pygame.Rect(
            self.x,
            self.y,
            PLAYER_LARGURA,
            PLAYER_ALTURA
        )