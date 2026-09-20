import sys
from random import randrange, shuffle


sys.setrecursionlimit(10000)


DIRECOES = {
    "esquerda": (-1, 0),
    "direita": (1, 0),
    "cima": (0, -1),
    "baixo": (0, 1),
}

OPPOSTAS = {
    "esquerda": "direita",
    "direita": "esquerda",
    "cima": "baixo",
    "baixo": "cima",
}


def gerar_labirinto(largura=15, altura=10):
    labirinto = [
        [
            {
                "esquerda": True,
                "direita": True,
                "cima": True,
                "baixo": True,
                "visitado": False,
            }
            for _ in range(largura)
        ]
        for _ in range(altura)
    ]

    def visitar(x, y):
        labirinto[y][x]["visitado"] = True
        direcoes = list(DIRECOES.items())
        shuffle(direcoes)

        for direcao, (dx, dy) in direcoes:
            nx = x + dx
            ny = y + dy

            if not (0 <= nx < largura and 0 <= ny < altura):
                continue

            if labirinto[ny][nx]["visitado"]:
                continue

            labirinto[y][x][direcao] = False
            labirinto[ny][nx][OPPOSTAS[direcao]] = False
            visitar(nx, ny)

    visitar(randrange(largura), randrange(altura))

    for linha in labirinto:
        for celula in linha:
            celula.pop("visitado")

    return labirinto


def pode_mover(labirinto, x, y, direcao):
    altura = len(labirinto)
    largura = len(labirinto[0])
    dx, dy = DIRECOES[direcao]
    nx = x + dx
    ny = y + dy

    if not (0 <= nx < largura and 0 <= ny < altura):
        return False

    return not labirinto[y][x][direcao]
