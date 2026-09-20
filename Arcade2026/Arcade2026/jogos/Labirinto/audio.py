import math
from array import array
import pygame as pg

TAXA_AUDIO = 44100

def criar_som(frequencia, duracao, volume=0.25, descer=True):
    if not pg.mixer.get_init():
        return None

    quantidade = int(TAXA_AUDIO * duracao)
    amostras = array("h")

    for i in range(quantidade):
        tempo = i / TAXA_AUDIO
        envelope = 1 - (i / quantidade) if descer else 1
        valor = int(32767 * volume * envelope * math.sin(2 * math.pi * frequencia * tempo))
        amostras.append(valor)

    return pg.mixer.Sound(buffer=amostras.tobytes())

def criar_sons():
    try:
        if not pg.mixer.get_init():
            return {}

        return {
            "ponto": criar_som(880, 0.07, 0.18),
            "vida": criar_som(180, 0.28, 0.28),
            "vitoria": criar_som(660, 0.45, 0.28, False),
            "derrota": criar_som(110, 0.55, 0.30),
            "alerta": criar_som(520, 0.12, 0.20),
        }
    except pg.error:
        return {}

def tocar_som(sons, nome):
    som = sons.get(nome)
    if som:
        som.play()