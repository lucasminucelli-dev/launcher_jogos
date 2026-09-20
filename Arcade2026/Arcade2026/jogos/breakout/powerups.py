
import pygame
import random

class PowerUp:

    def __init__(self, x, y, tipo):

        self.x = x
        self.y = y

        self.tipo = tipo

        self.velocidade = 3

        self.rect = pygame.Rect(self.x, self.y, 25, 25)

    def mover(self):

        self.y += self.velocidade
        self.rect.y = self.y

    def desenhar(self, tela):

        if self.tipo == "forca":
            cor = (255,0,0)
        else:
            cor = (0,255,255)

        pygame.draw.rect(tela, cor, self.rect)

def criar_powerup(x, y):

    tipos = ["forca", "velocidade"]

    tipo = random.choice(tipos)

    return PowerUp(x, y, tipo)
