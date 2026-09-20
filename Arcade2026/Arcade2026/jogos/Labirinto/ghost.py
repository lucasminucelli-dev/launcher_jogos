from collections import deque
from random import choice
from config import *
from gerar_labirinto import DIRECOES

class Ghost:
    def __init__(self, x, y, cor, cor_sombra, regiao):
        self.origem_x = x
        self.origem_y = y
        self.x = x
        self.y = y
        self.cor = cor
        self.cor_sombra = cor_sombra
        self.regiao = regiao
        
        self.rota = []
        self.visitadas = {(x, y)}
        self.direcao = "esquerda"
        self.tempo = 0
        self.alvo = None

    def atualizar(self, game):
        self.tempo += 1
        if self.tempo < TEMPO_INIMIGO:
            return

        self.tempo = 0
        atual = (self.x, self.y)

        # Se não tem rota, calcula uma nova
        if not self.rota:
            self.alvo = self.escolher_alvo(game)
            self.rota = self.criar_rota(game, atual, self.alvo)

        if not self.rota:
            return

        # Move para o próximo passo da rota
        proxima_posicao = self.rota.pop(0)
        self.direcao = self.direcao_entre(atual, proxima_posicao)
        self.x, self.y = proxima_posicao
        self.visitadas.add(proxima_posicao)

    def escolher_alvo(self, game):
        atual = (self.x, self.y)
        
        # Mapeia todas as células exceto onde o jogador está
        todas_as_celulas = {
            (x, y)
            for y in range(game.altura_mapa)
            for x in range(game.largura_mapa)
            if (x, y) != (game.player.x, game.player.y)
        }
        
        # Divide as regiões (rosa em cima, ciano embaixo)
        if self.regiao == "superior":
            area_preferida = {c for c in todas_as_celulas if c[1] < game.altura_mapa // 2}
        else:
            area_preferida = {c for c in todas_as_celulas if c[1] >= game.altura_mapa // 2}

        nao_visitadas = list((area_preferida or todas_as_celulas) - self.visitadas)

        if not nao_visitadas:
            self.visitadas = {(self.x, self.y)}
            nao_visitadas = list((area_preferida or todas_as_celulas) - self.visitadas)

        if not nao_visitadas:
            nao_visitadas = list(todas_as_celulas - self.visitadas)

        if not nao_visitadas:
            return choice(list(todas_as_celulas))

        # Escolhe a célula mais próxima baseada no tamanho da rota
        return min(
            nao_visitadas,
            key=lambda alvo: len(self.criar_rota(game, atual, alvo)) or (game.largura_mapa * game.altura_mapa),
        )

    def vizinhos_validos(self, game, x, y):
        for direcao in DIRECOES:
            if game.labirinto.pode_mover(x, y, direcao):
                dx, dy = DIRECOES[direcao]
                yield direcao, (x + dx, y + dy)

    def criar_rota(self, game, inicio, destino):
        # Algoritmo de Busca em Largura (BFS)
        fila = deque([inicio])
        anterior = {inicio: None}

        while fila:
            atual = fila.popleft()
            if atual == destino:
                break

            for _, proximo in self.vizinhos_validos(game, atual[0], atual[1]):
                if proximo in anterior:
                    continue
                anterior[proximo] = atual
                fila.append(proximo)

        if destino not in anterior:
            return []

        rota = []
        atual = destino
        while atual != inicio:
            rota.append(atual)
            atual = anterior[atual]

        rota.reverse()
        return rota

    def direcao_entre(self, origem, destino):
        ox, oy = origem
        dx, dy = destino
        if dx < ox: return "esquerda"
        if dx > ox: return "direita"
        if dy < oy: return "cima"
        return "baixo"

    def resetar(self, x, y):
        self.x = x
        self.y = y
        self.rota.clear()
        self.alvo = None
        self.visitadas = {(x, y)}