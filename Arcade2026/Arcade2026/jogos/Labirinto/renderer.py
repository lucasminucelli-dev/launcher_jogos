import math
import pygame as pg
import config as cfg

class Renderer:
    def __init__(self, tela):
        self.tela = tela
        
        # Criação da superfície interna baseada nas proporções dinâmicas do mapa
        self.largura_jogo = cfg.LARGURA * cfg.TAMANHO_CELULA
        self.altura_jogo = cfg.ALTURA * cfg.TAMANHO_CELULA + cfg.ALTURA_HUD
        self.superficie_interna = pg.Surface((self.largura_jogo, self.altura_jogo))
        
        # Fontes tipográficas estruturadas
        self.fonte_titulo = pg.font.SysFont("Arial", 48, bold=True)
        self.fonte_menu = pg.font.SysFont("Arial", 32, bold=True)
        self.fonte_hud = pg.font.SysFont("Arial", 22, bold=True)
        self.fonte_mensagem = pg.font.SysFont("Arial", 42, bold=True)

        # Fallbacks seguros para mapeamento angular da boca
        self.angulos_boca = {
            "direita": (30, 330),
            "esquerda": (210, 150),
            "cima": (120, 60),
            "baixo": (300, 240)
        }

    def redimensionar_tela(self):
        """Garante o aspecto perfeito em Fullscreen aplicando barras pretas nas sobras"""
        largura_tela, altura_tela = self.tela.get_size()
        escala = min(largura_tela / self.largura_jogo, altura_tela / self.altura_jogo)
        largura_final = int(self.largura_jogo * escala)
        height_final = int(self.altura_jogo * escala)
        
        x_final = (largura_tela - largura_final) // 2
        y_final = (altura_tela - height_final) // 2
        
        self.tela.fill(cfg.PRETO)
        tela_esticada = pg.transform.smoothscale(self.superficie_interna, (largura_final, height_final))
        self.tela.blit(tela_esticada, (x_final, y_final))

    def centro_celula(self, x, y):
        """Calcula o centro absoluto em pixels de qualquer coordenada lógica"""
        return (
            x * cfg.TAMANHO_CELULA + cfg.TAMANHO_CELULA // 2,
            y * cfg.TAMANHO_CELULA + cfg.TAMANHO_CELULA // 2,
        )

    # ================= INTERFACES E MENUS ================= #

    def desenhar_menu(self, menu):
        self.superficie_interna.fill((15, 15, 30))
        titulo = self.fonte_titulo.render("PACMAN LABIRINTO", True, cfg.AMARELO)
        self.superficie_interna.blit(titulo, titulo.get_rect(center=(self.largura_jogo // 2, 150)))
        
        for i, texto in enumerate(menu.opcoes):
            cor = cfg.AMARELO if i == menu.selecionado else cfg.BRANCO
            render = self.fonte_menu.render(texto, True, cor)
            self.superficie_interna.blit(render, render.get_rect(center=(self.largura_jogo // 2, 350 + i * 60)))
            
        self.redimensionar_tela()

    def desenhar_creditos(self):
        self.superficie_interna.fill((15, 15, 30))
        titulo = self.fonte_titulo.render("CRÉDITOS", True, cfg.BRANCO)
        self.superficie_interna.blit(titulo, titulo.get_rect(center=(self.largura_jogo // 2, 100)))
        
        linhas = [
            "Desafio: Labirinto Mutavel em Tempo Real",
            "Sistema de Informação (SI) - IMMES",
            "Turma - 2026",
            "Desenvolvido por: Heloisa e Manuela"
        ]
        
        for i, linha in enumerate(linhas):
            render = self.fonte_menu.render(linha, True, cfg.BRANCO)
            self.superficie_interna.blit(render, render.get_rect(center=(self.largura_jogo // 2, 240 + i * 50)))
            
        voltar = self.fonte_menu.render("Pressione ESC para voltar", True, cfg.AMARELO)
        self.superficie_interna.blit(voltar, voltar.get_rect(center=(self.largura_jogo // 2, 540)))
        
        self.redimensionar_tela()

    def desenhar_ranking(self, lista_ranking):
        self.superficie_interna.fill((15, 15, 30))
        titulo = self.fonte_titulo.render("TOP 10 RECORDES", True, cfg.AMARELO)
        self.superficie_interna.blit(titulo, titulo.get_rect(center=(self.largura_jogo // 2, 100)))
        
        if not lista_ranking:
            vazio = self.fonte_menu.render("Nenhum recorde coletado!", True, cfg.BRANCO)
            self.superficie_interna.blit(vazio, vazio.get_rect(center=(self.largura_jogo // 2, 300)))
        else:
            for i, (nome, pontos) in enumerate(lista_ranking):
                texto = f"{i+1}. {nome}  ---  {pontos} pts"
                render = self.fonte_menu.render(texto, True, cfg.BRANCO)
                self.superficie_interna.blit(render, render.get_rect(center=(self.largura_jogo // 2, 200 + i * 42)))
                
        voltar = self.fonte_menu.render("Pressione ESC para voltar", True, cfg.AMARELO)
        self.superficie_interna.blit(voltar, voltar.get_rect(center=(self.largura_jogo // 2, 640)))
        
        self.redimensionar_tela()

    # ================= ELEMENTOS DO MAPA ================= #

    def desenhar_parede(self, inicio, fim, alerta=False):
        x1, y1 = inicio
        x2, y2 = fim
        espessura = 16

        if y1 == y2:
            rect = pg.Rect(min(x1, x2), y1 - espessura // 2, abs(x2 - x1), espessura)
        else:
            rect = pg.Rect(x1 - espessura // 2, min(y1, y2), espessura, abs(y2 - y1))

        cor_base = cfg.LARANJA if alerta else cfg.AZUL
        cor_escura = cfg.VERMELHO if alerta else getattr(cfg, "AZUL_ESCURO", (15, 35, 140))
        cor_brilho = getattr(cfg, "AMARELO_CLARO", (255, 240, 150)) if alerta else getattr(cfg, "AZUL_CLARO", (80, 160, 255))

        pg.draw.rect(self.superficie_interna, cor_escura, rect, border_radius=5)
        pg.draw.rect(self.superficie_interna, cor_base, rect.inflate(-4, -4), border_radius=4)
        pg.draw.rect(self.superficie_interna, cor_brilho, rect.inflate(-9, -9), border_radius=3)

    def desenhar_fantasma(self, x, y, direcao, quadro, cor, cor_sombra):
        cx, cy = self.centro_celula(x, y)
        cy += int(math.sin(quadro / 3) * 3) # Efeito de flutuação vertical
        raio = cfg.TAMANHO_CELULA // 2 - 7
        corpo = pg.Rect(cx - raio, cy - raio, raio * 2, raio * 2)

        pg.draw.circle(self.superficie_interna, cor_sombra, (cx - 4, cy - 1), raio)
        pg.draw.circle(self.superficie_interna, cor, (cx, cy - 3), raio)
        pg.draw.rect(self.superficie_interna, cor, (cx - raio, cy - 3, raio * 2, raio + 9))

        olhar_x = 3 if direcao == "direita" else -3 if direcao == "esquerda" else 0
        olhar_y = -3 if direcao == "cima" else 3 if direcao == "baixo" else 0

        # Desenho dos olhos direcionais
        for offset in (-8, 8):
            pg.draw.circle(self.superficie_interna, cfg.BRANCO, (cx + offset + olhar_x, cy - 6 + olhar_y), 5)
            pg.draw.circle(self.superficie_interna, cfg.PRETO, (cx + offset + olhar_x * 1.5, cy - 6 + olhar_y * 1.5), 2.5)

        # Franjas/Ondas na base do fantasma
        for ponta in range(3):
            px = corpo.left + ponta * (raio * 2 // 3)
            pontos = [(px, corpo.bottom + 5), (px + raio // 2, corpo.bottom - 2), (px + raio, corpo.bottom + 5)]
            pg.draw.polygon(self.superficie_interna, cor, pontos)

    def desenhar_pacman(self, x, y, direcao, boca_aberta, quadro):
        cx, cy = self.centro_celula(x, y)
        cy += int(math.sin(quadro / 4) * 2)
        raio = cfg.TAMANHO_CELULA // 2 - 6
        abertura = self.angulos_boca.get(direcao, (30, 330)) if boca_aberta else (8, 352)

        # Sombreamento tridimensional básico
        pg.draw.circle(self.superficie_interna, getattr(cfg, "AMARELO_ESCURO", (200, 150, 20)), (cx - 3, cy + 3), raio)
        pg.draw.circle(self.superficie_interna, cfg.AMARELO, (cx, cy), raio)

        # Corte poligonal para a boca simulada
        inicio, fim = abertura
        pontos_boca = [
            (cx, cy),
            (cx + raio * math.cos(math.radians(inicio)), cy - raio * math.sin(math.radians(inicio))),
            (cx + raio * math.cos(math.radians(fim)), cy - raio * math.sin(math.radians(fim))),
        ]
        pg.draw.polygon(self.superficie_interna, cfg.PRETO, pontos_boca)
        pg.draw.circle(self.superficie_interna, cfg.PRETO, (cx + (2 if direcao in ["cima","baixo"] else 4), cy - 10), 3.5)

    def desenhar_hud(self, game):
        topo = cfg.ALTURA * cfg.TAMANHO_CELULA
        painel = pg.Rect(0, topo, self.largura_jogo, cfg.ALTURA_HUD)
        pg.draw.rect(self.superficie_interna, (40, 50, 45), painel)
        pg.draw.rect(self.superficie_interna, (220, 235, 210), painel.inflate(-10, -10), border_radius=12)

        pontos_coletados = game.total_pontos - len(game.pontos)
        segundos_mapa = max(1, math.ceil(game.tempo_labirinto / cfg.FPS))
        
        textos = [
            f"Pontos: {pontos_coletados}/{game.total_pontos}",
            f"Vidas: ",
            f"Mudar em: {segundos_mapa}s",
            "Mover: Setas / WASD",
            "R: Reiniciar  |  ESC: Menu"
        ]
        posicoes = [(25, topo + 18), (250, topo + 18), (500, topo + 18), (25, topo + 54), (500, topo + 54)]

        for indice, (texto, posicao) in enumerate(zip(textos, posicoes)):
            cor = cfg.VERMELHO if (game.labirinto_em_alerta and indice == 2) else cfg.PRETO
            renderizado = self.fonte_hud.render(texto, True, cor)
            self.superficie_interna.blit(renderizado, posicao)

        # Iconografia de vidas no painel
        for vida in range(game.player.vidas):
            cx, cy = 320 + vida * 26, topo + 30
            pg.draw.circle(self.superficie_interna, cfg.AMARELO, (cx, cy), 9)
            pg.draw.polygon(self.superficie_interna, (220, 235, 210), [(cx, cy), (cx + 10, cy - 6), (cx + 10, cy + 6)])

    def desenhar_jogo(self, game):
        self.superficie_interna.fill(cfg.PRETO)

        # Grade sutil de fundo
        for y in range(0, cfg.ALTURA * cfg.TAMANHO_CELULA, cfg.TAMANHO_CELULA):
            for x in range(0, self.largura_jogo, cfg.TAMANHO_CELULA):
                pg.draw.circle(self.superficie_interna, (20, 20, 25), (x + cfg.TAMANHO_CELULA // 2, y + cfg.TAMANHO_CELULA // 2), 2)

        # Renderização dinâmica das paredes geométricas
        piscar = game.labirinto_em_alerta and game.quadro % 6 < 3
        for y, linha in enumerate(game.labirinto.mapa):
            for x, celula in enumerate(linha):
                esq, dir = x * cfg.TAMANHO_CELULA, (x + 1) * cfg.TAMANHO_CELULA
                topo, baixo = y * cfg.TAMANHO_CELULA, (y + 1) * cfg.TAMANHO_CELULA
                if celula["cima"]: self.desenhar_parede((esq, topo), (dir, topo), piscar)
                if celula["baixo"]: self.desenhar_parede((esq, baixo), (dir, baixo), piscar)
                if celula["esquerda"]: self.desenhar_parede((esq, topo), (esq, baixo), piscar)
                if celula["direita"]: self.desenhar_parede((dir, topo), (dir, baixo), piscar)

        # Renderização das pastilhas coletáveis
        cor_ponto = getattr(cfg, "MARROM", (215, 175, 110))
        for x, y in game.pontos:
            pg.draw.circle(self.superficie_interna, cor_ponto, self.centro_celula(x, y), 5)
            
        # Alvo / Saída do Labirinto
        sx, sy = self.centro_celula(cfg.LARGURA - 1, cfg.ALTURA - 1)
        pg.draw.rect(self.superficie_interna, cfg.LARANJA, (sx - 15, sy - 15, 30, 30), border_radius=5)
        pg.draw.rect(self.superficie_interna, cfg.VERMELHO, (sx - 8, sy - 8, 16, 16), border_radius=2)

        # Atores (Fantasmas e Pacman com efeito de frame intermitente sob invencibilidade)
        for ghost in game.ghosts:
            self.desenhar_fantasma(ghost.x, ghost.y, ghost.direcao, game.quadro, ghost.cor, ghost.cor_sombra)
            
        if game.player.invencivel == 0 or game.quadro % 4 < 2:
            self.desenhar_pacman(game.player.x, game.player.y, game.player.direcao, game.passos % 2 == 0, game.quadro)

        self.desenhar_hud(game)

        # Overlay (Camada de fim de estado - Vitória ou Derrota)
        if game.venceu or game.perdeu:
            camada_escura = pg.Surface((self.largura_jogo, self.altura_jogo), pg.SRCALPHA)
            camada_escura.fill((0, 0, 0, 185))
            self.superficie_interna.blit(camada_escura, (0, 0))
            
            titulo = "VOCÊ VENCEU!" if game.venceu else "FIM DE JOGO!"
            cor = cfg.VERDE if game.venceu else cfg.VERMELHO
            
            texto = self.fonte_mensagem.render(titulo, True, cor)
            dica = pg.font.SysFont("Arial", 22).render("Pressione R para recomeçar uma partida", True, cfg.BRANCO)
            
            self.superficie_interna.blit(texto, texto.get_rect(center=(self.largura_jogo // 2, self.altura_jogo // 2 - 30)))
            self.superficie_interna.blit(dica, dica.get_rect(center=(self.largura_jogo // 2, self.altura_jogo // 2 + 30)))

        self.redimensionar_tela()