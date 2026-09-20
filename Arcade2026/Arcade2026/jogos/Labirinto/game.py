import sys
import pygame as pg

import config as cfg
import audio
from menu import Menu
from ranking import RankingManager
from player import Player
from ghost import Ghost
from labirinto import Labirinto
from renderer import Renderer


class Game:

    def __init__(self):
        # 1. Inicialização do sistema de áudio seguro
        pg.mixer.pre_init(audio.TAXA_AUDIO, -16, 1, 512)
        pg.init()
        try:
            pg.mixer.init()
        except pg.error:
            pass

        # 2. Configuração de Tela Cheia Dinâmica
        self.tela = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        largura_tela, altura_tela = self.tela.get_size()

        # Ajusta o tamanho do mapa dinamicamente para o monitor do usuário
        cfg.LARGURA = min(20, max(15, largura_tela // cfg.TAMANHO_CELULA))
        cfg.ALTURA = min(
            13, max(10, (altura_tela - cfg.ALTURA_HUD) // cfg.TAMANHO_CELULA)
        )

        self.largura_mapa = cfg.LARGURA
        self.altura_mapa = cfg.ALTURA

        self.clock = pg.time.Clock()

        # 3. Inicialização dos Módulos Principais
        self.renderer = Renderer(self.tela)
        self.menu = Menu()
        self.ranking = RankingManager()
        self.player = Player()
        self.labirinto = Labirinto()
        self.estado = Menu.MENU
        self.running = True

        self.sons = audio.criar_sons()
        self.resetar_jogo()

    def resetar_jogo(self):
        self.player.resetar_posicao()
        self.player.vidas = cfg.VIDAS_INICIAIS
        self.player.pontos = 0
        self.player.invencivel = cfg.TEMPO_INVENCIVEL
        self.labirinto.gerar()

        # --- CORREÇÃO AQUI: Geração das Pastilhas no Labirinto ---
        self.pontos = set()
        for y in range(cfg.ALTURA):
            for x in range(cfg.LARGURA):
                # Não coloca ponto onde o jogador nasce nem na saída
                if (x, y) != (0, 0) and (x, y) != (cfg.LARGURA - 1, cfg.ALTURA - 1):
                    self.pontos.add((x, y))
        self.total_pontos = len(self.pontos)
        # ---------------------------------------------------------

        # Iniciar fantasmas posicionados nos 4 cantos da tela de forma segura
        self.ghosts = [
            Ghost(1, 1, cfg.VERMELHO, getattr(cfg, "AZUL_ESCURO", (15, 35, 140)), "superior"),
            Ghost(cfg.LARGURA - 2, 1, cfg.ROSA, getattr(cfg, "ROSA_ESCURO", (202, 55, 112)), "superior"),
            Ghost(1, cfg.ALTURA - 2, cfg.CIANO, getattr(cfg, "AZUL_ESCURO", (15, 35, 140)), "inferior"),
            Ghost(cfg.LARGURA - 2, cfg.ALTURA - 2, cfg.LARANJA, getattr(cfg, "AMARELO_ESCURO", (255, 188, 24)), "inferior"),
        ]

        self.quadro = 0
        self.passos = 0
        self.direcao = "direita"
        self.proxima_direcao = "direita"

        self.tempo_labirinto = cfg.SEGUNDOS_PARA_MUDAR_LABIRINTO * cfg.FPS
        self.labirinto_em_alerta = False

        self.venceu = False
        self.perdeu = False
        self.som_derrota_tocado = False
        self.som_vitoria_tocado = False
        self.nome_jogador = ""
        self.salvou_ranking = False

    def atualizar_jogador(self):
        if self.perdeu or self.venceu:
            return

        if self.quadro % cfg.TEMPO_JOGADOR == 0:
            # Tenta aplicar a próxima direção desejada pelo usuário
            if self.labirinto.pode_mover(
                self.player.x, self.player.y, self.proxima_direcao
            ):
                self.direcao = self.proxima_direcao
                self.player.direcao = self.proxima_direcao

            # Move na direção atual se o caminho estiver livre
            if self.labirinto.pode_mover(
                self.player.x, self.player.y, self.direcao
            ):
                dx, dy = 0, 0
                if self.direcao == "esquerda":
                    dx = -1
                elif self.direcao == "direita":
                    dx = 1
                elif self.direcao == "cima":
                    dy = -1
                elif self.direcao == "baixo":
                    dy = 1

                self.player.mover(dx, dy)
                self.passos += 1

                # --- CORREÇÃO AQUI: Coletar os pontos no mapa ---
                pos_atual = (self.player.x, self.player.y)
                if pos_atual in self.pontos:
                    self.pontos.remove(pos_atual)
                    self.player.adicionar_ponto()
                    audio.tocar_som(self.sons, "ponto")
                # ------------------------------------------------

                # Condição de vitória: alcançar a saída (canto inferior direito) ou comer todos os pontos
                if (self.player.x == cfg.LARGURA - 1 and self.player.y == cfg.ALTURA - 1) or not self.pontos:
                    self.venceu = True
                    # Bônus por vitória expressiva
                    for _ in range(50):
                        self.player.adicionar_ponto()
                    if not self.som_vitoria_tocado:
                        audio.tocar_som(self.sons, "vitoria")
                        self.som_vitoria_tocado = True

    def verificar_colisao(self):
        if self.perdeu or self.venceu:
            return

        colidiu = False
        for ghost in self.ghosts:
            if ghost.x == self.player.x and ghost.y == self.player.y:
                colidiu = True
                break

        if not colidiu:
            return

        if self.player.invencivel > 0:
            return

        self.player.perder_vida()
        if self.player.vidas <= 0:
            self.perdeu = True
            if not self.som_derrota_tocado:
                audio.tocar_som(self.sons, "derrota")
                self.som_derrota_tocado = True
            return

        audio.tocar_som(self.sons, "vida")
        self.player.resetar_posicao()
        self.player.invencivel = cfg.TEMPO_INVENCIVEL
        for g in self.ghosts:
            g.resetar(g.origem_x, g.origem_y)
        self.tempo_labirinto = cfg.SEGUNDOS_PARA_MUDAR_LABIRINTO * cfg.FPS
        self.labirinto_em_alerta = False

    def atualizar_labirinto(self):
        if self.perdeu or self.venceu:
            return

        self.tempo_labirinto -= 1

        if self.tempo_labirinto == cfg.AVISO_MUDANCA_LABIRINTO * cfg.FPS:
            self.labirinto_em_alerta = True
            audio.tocar_som(self.sons, "alerta")

        if self.tempo_labirinto <= 0:
            self.labirinto.gerar()
            audio.tocar_som(self.sons, "mudar")
            self.tempo_labirinto = cfg.SEGUNDOS_PARA_MUDAR_LABIRINTO * cfg.FPS
            self.labirinto_em_alerta = False
            # Bônus por sobreviver à mutação dinâmica do mapa
            for _ in range(15):
                self.player.adicionar_ponto()

    def eventos(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.estado in [
                        Menu.RANKING,
                        Menu.CREDITOS,
                        "INPUT_NAME",
                    ]:
                        self.estado = Menu.MENU
                    elif self.estado == Menu.JOGO:
                        self.estado = Menu.MENU

                elif self.estado == Menu.MENU:
                    if event.key == pg.K_UP:
                        self.menu.subir()
                    elif event.key == pg.K_DOWN:
                        self.menu.descer()
                    elif event.key == pg.K_RETURN:
                        opcao = self.menu.opcao_atual()
                        if opcao == "JOGAR":
                            self.resetar_jogo()
                            self.estado = Menu.JOGO
                        elif opcao == "RANKING":
                            self.estado = Menu.RANKING
                        elif opcao == "CREDITOS":
                            self.estado = Menu.CREDITOS
                        elif opcao == "SAIR":
                            self.running = False

                elif self.estado == Menu.JOGO:
                    if self.perdeu or self.venceu:
                        if event.key == pg.K_r:
                            self.resetar_jogo()
                        elif event.key == pg.K_RETURN:
                            self.estado = "INPUT_NAME"
                    else:
                        if event.key in [pg.K_UP, pg.K_w]:
                            self.proxima_direcao = "cima"
                        elif event.key in [pg.K_DOWN, pg.K_s]:
                            self.proxima_direcao = "baixo"
                        elif event.key in [pg.K_LEFT, pg.K_a]:
                            self.proxima_direcao = "esquerda"
                        elif event.key in [pg.K_RIGHT, pg.K_d]:
                            self.proxima_direcao = "direita"

                elif self.estado == "INPUT_NAME":
                    if event.key == pg.K_RETURN:
                        nome_final = self.nome_jogador.strip()
                        if nome_final:
                            # Salva o nome do jogador e a pontuação real dele
                            self.ranking.salvar(nome_final, self.player.pontos)
                            self.salvou_ranking = True
                            self.estado = Menu.RANKING
                    elif event.key == pg.K_BACKSPACE:
                        self.nome_jogador = self.nome_jogador[:-1]
                    else:
                        # Validação e limite de caracteres (máximo de 12 letras/números/espaços)
                        if len(self.nome_jogador) < 12 and (
                            event.unicode.isalnum() or event.unicode == " "
                        ):
                            self.nome_jogador += event.unicode

    def update(self):
        if self.estado == "INPUT_NAME":
            self.quadro += 1
            return

        if self.estado != Menu.JOGO:
            return

        self.quadro += 1
        if self.player.invencivel > 0:
            self.player.invencivel -= 1

        self.atualizar_jogador()
        for ghost in self.ghosts:
            ghost.atualizar(self)
        self.verificar_colisao()
        self.atualizar_labirinto()

    def desenhar_tela_nome(self):
        self.tela.fill((15, 15, 30))

        fonte_tit = pg.font.SysFont("Arial", 44, bold=True)
        fonte_sub = pg.font.SysFont("Arial", 26)
        fonte_txt = pg.font.SysFont("Arial", 36, bold=True)

        # Cabeçalho da tela de recordes
        texto_titulo = fonte_tit.render("FIM DA PARTIDA", True, cfg.AMARELO)
        rect_titulo = texto_titulo.get_rect(
            center=(self.tela.get_width() // 2, 140)
        )
        self.tela.blit(texto_titulo, rect_titulo)

        # Exibição dos pontos conquistados
        texto_pontos = fonte_sub.render(
            f"Sua Pontuação: {self.player.pontos} PONTOS", True, cfg.BRANCO
        )
        rect_pontos = texto_pontos.get_rect(
            center=(self.tela.get_width() // 2, 210)
        )
        self.tela.blit(texto_pontos, rect_pontos)

        # Instruções de digitação
        texto_inst = fonte_sub.render(
            "Digite seu nome para o Ranking:", True, cfg.AZUL_CLARO
        )
        rect_inst = texto_inst.get_rect(
            center=(self.tela.get_width() // 2, 310)
        )
        self.tela.blit(texto_inst, rect_inst)

        # Caixa visual estilizada para o Input de texto
        largura_caixa = 420
        altura_caixa = 64
        x_caixa = (self.tela.get_width() - largura_caixa) // 2
        y_caixa = 350

        pg.draw.rect(
            self.tela,
            cfg.AZUL,
            (x_caixa, y_caixa, largura_caixa, altura_caixa),
            border_radius=10,
        )
        pg.draw.rect(
            self.tela,
            (25, 25, 50),
            (x_caixa + 4, y_caixa + 4, largura_caixa - 8, altura_caixa - 8),
            border_radius=8,
        )

        # Efeito dinâmico do cursor piscante integrado ao loop frame-a-frame
        cursor = "|" if (self.quadro // 12) % 2 == 0 else ""
        texto_nome = fonte_txt.render(self.nome_jogador + cursor, True, cfg.BRANCO)
        rect_nome = texto_nome.get_rect(
            center=(self.tela.get_width() // 2, y_caixa + altura_caixa // 2)
        )
        self.tela.blit(texto_nome, rect_nome)

        # Ajuda / Rodapé de navegação
        texto_ajuda = fonte_sub.render(
            "Pressione [ENTER] para Gravar ou [ESC] para Cancelar",
            True,
            cfg.VERDE,
        )
        rect_ajuda = texto_ajuda.get_rect(
            center=(self.tela.get_width() // 2, 480)
        )
        self.tela.blit(texto_ajuda, rect_ajuda)

    def draw(self):
        if self.estado == Menu.MENU:
            self.renderer.desenhar_menu(self.menu)
        elif self.estado == Menu.CREDITOS:
            self.renderer.desenhar_creditos()
        elif self.estado == Menu.RANKING:
            dados_ranking = self.ranking.carregar()
            self.renderer.desenhar_ranking(dados_ranking)
        elif self.estado == Menu.JOGO:
            self.renderer.desenhar_jogo(self)
            # Adiciona a dica suplementar sobre o ranking por cima do overlay original
            if self.venceu or self.perdeu:
                fonte_suplementar = pg.font.SysFont("Arial", 24, bold=True)
                texto_sup = fonte_suplementar.render(
                    "Pressione [ENTER] para salvar seu recorde no ranking",
                    True,
                    cfg.AMARELO,
                )
                rect_sup = texto_sup.get_rect(
                    center=(
                        self.tela.get_width() // 2,
                        self.tela.get_height() - 60,
                    )
                )
                self.tela.blit(texto_sup, rect_sup)
        elif self.estado == "INPUT_NAME":
            self.desenhar_tela_nome()

        pg.display.flip()

    def run(self):
        while self.running:
            self.eventos()
            self.update()
            self.draw()
            self.clock.tick(cfg.FPS)
        pg.quit()
        sys.exit()