import pygame
import random
import sys

from config import *
from player import Player
from platform import Platform
from ranking_manager import RankingManager

MENU = "menu"
PLAYING = "playing"
RECORDS = "records"
CREDITS = "credits"
ENTER_NAME = "enter_name"

class Game:
    def __init__(self):
        pygame.init()

        self.tela = pygame.display.set_mode(
            (LARGURA_TELA, ALTURA_TELA),
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("Elf Dog Jump")

        self.superficie_jogo = pygame.Surface((LARGURA_JOGO, ALTURA_JOGO))

        self.escala = min(
            LARGURA_TELA / LARGURA_JOGO,
            ALTURA_TELA / ALTURA_JOGO
        )
        self.largura_escalada = int(LARGURA_JOGO * self.escala)
        self.altura_escalada = int(ALTURA_JOGO * self.escala)
        self.x_jogo = (LARGURA_TELA - self.largura_escalada) // 2
        self.y_jogo = (ALTURA_TELA - self.altura_escalada) // 2

        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("Arial", 30)
        self.fonte_titulo = pygame.font.SysFont("Arial", 60, bold=True)

        self.estado = MENU
        self.ranking = RankingManager()
        self.nome_digitado = ""
        self.pontuacao = 0

        self.inicializar_audio()
        self.tocar_musica_fundo("sons/musica_fundo.wav")

        self.carregar_imagens()

    # ==================================================
    # MÚSICA E SONS
    # ==================================================
    def inicializar_audio(self):
        # Inicializa o mixer de áudio e carrega o efeito sonoro de pulo.
        try:
            pygame.mixer.init()
            self.som_colisao = pygame.mixer.Sound("sons/colisao.wav")
            self.som_colisao.set_volume(0.6)
        except Exception as e:
            print(f"Erro ao inicializar efeitos sonoros: {e}")
            self.som_colisao = None

    def tocar_musica_fundo(self, caminho_musica):
        # Carrega e toca uma música de fundo em loop infinito.
        try:
            pygame.mixer.music.load(caminho_musica)
            pygame.mixer.music.set_volume(0.3) # 30% do volume original
            pygame.mixer.music.play(-1) # -1 faz repetir para sempre
        except Exception as e:
            print(f"Não foi possível tocar a música {caminho_musica}: {e}")

    def parar_musica(self):
        # Para a música de fundo atual.
        pygame.mixer.music.stop()

    # ==================================================
    # IMAGENS
    # ==================================================
    def carregar(self, caminho, largura, altura):
        try:
            imagem = pygame.image.load(caminho)
            return pygame.transform.scale(imagem, (largura, altura))
        except:
            superficie = pygame.Surface((largura, altura))
            superficie.fill((100, 100, 100))
            return superficie

    def carregar_imagens(self):
        self.fundo_caverna = self.carregar("imagem/caverna.png", LARGURA_TELA, ALTURA_TELA)
        self.fundo_floresta = self.carregar("imagem/floresta.png", LARGURA_TELA, ALTURA_TELA)
        self.fundo_ceu = self.carregar("imagem/ceu.png", LARGURA_TELA, ALTURA_TELA)
        self.fundo_espaco = self.carregar("imagem/espaco.png", LARGURA_TELA, ALTURA_TELA)
        self.theo_menu = self.carregar("imagem/Theo_menu.png", 250, 250)
        self.theo = self.carregar("imagem/Theo.png", PLAYER_LARGURA, PLAYER_ALTURA)

    # ==================================================
    # JOGO
    # ==================================================
    def iniciar_jogo(self):
        self.player = Player(self.theo)
        self.plataformas = []
        espacamento = ALTURA_JOGO // 8

        # Criar plataformas iniciais
        for i in range(8):
            x = random.randint(0, LARGURA_JOGO - PLAT_LARGURA)
            y = ALTURA_JOGO - (i * espacamento) - 150
            self.plataformas.append(Platform(x, y))

        # Plataforma base para não cair direto
        self.plataformas.append(
            Platform(LARGURA_JOGO // 2 - (PLAT_LARGURA // 2), ALTURA_JOGO - 80)
        )

        self.player.x = LARGURA_JOGO // 2 - (PLAYER_LARGURA // 2)
        self.player.y = ALTURA_JOGO - 80 - PLAYER_ALTURA
        
        self.pontuacao = 0
        self.estado = PLAYING

        # Reinicia a música de fundo para o jogo
        self.tocar_musica_fundo("sons/musica_fundo.wav")

    # ==================================================
    # EVENTOS
    # ==================================================
    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # MENU E TELAS DE TEXTO
                if self.estado == MENU:
                    if evento.key == pygame.K_1:
                        self.iniciar_jogo()
                    elif evento.key == pygame.K_2:
                        self.estado = RECORDS
                    elif evento.key == pygame.K_3:
                        self.estado = CREDITS

                elif self.estado in (RECORDS, CREDITS):
                    if evento.key == pygame.K_RETURN:
                        self.estado = MENU

                # ENTRADA DE NOME (RECORDE)
                elif self.estado == ENTER_NAME:
                    if evento.key == pygame.K_RETURN:
                        if self.nome_digitado.strip() == "":
                            self.nome_digitado = "Anonimo"
                        self.ranking.salvar_score(self.nome_digitado, self.pontuacao)
                        self.estado = RECORDS
                    elif evento.key == pygame.K_BACKSPACE:
                        self.nome_digitado = self.nome_digitado[:-1]
                    else:
                        if len(self.nome_digitado) < 10 and evento.unicode.isprintable():
                            self.nome_digitado += evento.unicode

                # CONTROLES DO JOGADOR
                elif self.estado == PLAYING:
                    if evento.key == pygame.K_LEFT:
                        self.player.vel_x = -VELOCIDADE_HORIZONTAL
                    elif evento.key == pygame.K_RIGHT:
                        self.player.vel_x = VELOCIDADE_HORIZONTAL

            if evento.type == pygame.KEYUP:
                if self.estado == PLAYING:
                    if evento.key == pygame.K_LEFT and self.player.vel_x < 0:
                        self.player.vel_x = 0
                    if evento.key == pygame.K_RIGHT and self.player.vel_x > 0:
                        self.player.vel_x = 0

    # ==================================================
    # UPDATE FÍSICA E LÓGICA
    # ==================================================
    def update(self):
        if self.estado != PLAYING:
            return

        self.player.update()

        for plataforma in self.plataformas:
            plataforma.update()

        # 1. Colisão
        if self.player.vel_y > 0:
            player_rect = self.player.get_rect()
            
            for plat in self.plataformas[:]:
                plat_rect = plat.get_rect()
                
                if player_rect.colliderect(plat_rect):
                    if self.player.y + PLAYER_ALTURA - self.player.vel_y <= plat.y + 5:
                        self.player.jump()

                        # Som de colisão
                        if self.som_colisao:
                            self.som_colisao.play()
                        
                        # Lógica das plataformas quebráveis
                        if plat.quebravel:
                            plat.dano += 1
                            limite = 2 if self.pontuacao >= 1500 else 3
                            if plat.dano >= limite:
                                self.plataformas.remove(plat)

        # 2. Câmera
        if self.player.y < ALTURA_JOGO // 2:
            deslocamento = ALTURA_JOGO // 2 - self.player.y
            self.player.y = ALTURA_JOGO // 2

            for plat in self.plataformas:
                plat.y += deslocamento

            self.pontuacao += int(deslocamento // 5)

        # 3. Remover plataformas velhas
        self.plataformas = [p for p in self.plataformas if p.y < ALTURA_JOGO]

        # 4. Gerar novas plataformas infinitas com dificuldade progressiva
        while len(self.plataformas) < 8:
            novo_x = random.randint(0, LARGURA_JOGO - PLAT_LARGURA)
            menor_y = min(p.y for p in self.plataformas)
            novo_y = menor_y - random.randint(80, 110)
            
            quebravel = random.choice([True, False]) if self.pontuacao >= 500 else False
            movendo = False
            velocidade = 0

            if self.pontuacao >= 1500:
                movendo = True
                velocidade = random.choice([-3, 3])
            elif self.pontuacao >= 1000:
                movendo = random.choice([True, False])
                if movendo:
                    velocidade = random.choice([-2, 2])
            
            self.plataformas.append(Platform(novo_x, novo_y, quebravel, movendo, velocidade))

        # 5. Game Over
        if self.player.y > ALTURA_JOGO:
            self.parar_musica()
            if self.ranking.eh_recorde(self.pontuacao):
                self.estado = ENTER_NAME
                self.nome_digitado = ""
            else:
                self.estado = MENU

    # ==================================================
    # FUNDOS
    # ==================================================
    def fundo_atual(self):
        if self.pontuacao < 500:
            return self.fundo_caverna
        elif self.pontuacao < 1000:
            return self.fundo_floresta
        elif self.pontuacao < 1500:
            return self.fundo_ceu
        return self.fundo_espaco

    # ==================================================
    # DESENHO
    # ==================================================
    def desenhar_menu(self):
        self.tela.blit(self.fundo_floresta, (0, 0))
        self.tela.blit(self.theo_menu, (LARGURA_TELA // 2 - 125, 80))

        titulo = self.fonte_titulo.render("ELF DOG JUMP", True, BRANCO)
        self.tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2, 350))

        opcoes = ["1 - Jogar", "2 - Recordes", "3 - Creditos", "ESC - Sair"]
        y = 450
        for texto in opcoes:
            render = self.fonte.render(texto, True, BRANCO)
            self.tela.blit(render, (LARGURA_TELA // 2 - render.get_width() // 2, y))
            y += 50

    def desenhar_recordes(self):
        self.tela.blit(self.fundo_caverna, (0, 0))
        titulo = self.fonte_titulo.render("RECORDES", True, BRANCO)
        self.tela.blit(titulo, (100, 80))

        ranking = self.ranking.carregar()
        y = 180
        for i, (nome, pontos) in enumerate(ranking[:10]):
            texto = self.fonte.render(f"{i+1}. {nome} - {pontos}", True, BRANCO)
            self.tela.blit(texto, (100, y))
            y += 40

    def desenhar_creditos(self):
        self.tela.blit(self.fundo_espaco, (0, 0))
        linhas = [
            "ELFO DOG JUMP", "",
            "Sistemas de Informação (SI)", "",
            "Turma de 2026 - IMMES", "",
            "Desenvolvido por Lucas, Eduardo e Leticia", "",
            "ENTER para voltar"
        ]
        y = 150
        for linha in linhas:
            render = self.fonte.render(linha, True, BRANCO)
            self.tela.blit(render, (LARGURA_TELA // 2 - render.get_width() // 2, y))
            y += 50

    def desenhar_enter_name(self):
        self.tela.blit(self.fundo_caverna, (0, 0))
        
        titulo = self.fonte_titulo.render("NOVO RECORDE!", True, BRANCO)
        self.tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2, 200))

        instrucao = self.fonte.render("Digite seu nome e aperte ENTER:", True, BRANCO)
        self.tela.blit(instrucao, (LARGURA_TELA // 2 - instrucao.get_width() // 2, 300))

        # Nome sendo digitado com um cursor no final
        nome_render = self.fonte_titulo.render(self.nome_digitado + "_", True, LARANJA)
        self.tela.blit(nome_render, (LARGURA_TELA // 2 - nome_render.get_width() // 2, 400))

    def desenhar_jogo(self):
        self.tela.blit(self.fundo_atual(), (0, 0))

        # Preenche a área do jogo (opcional, dependendo de como quer a transparência)
        self.superficie_jogo.fill(PRETO)
        self.superficie_jogo.blit(
            pygame.transform.scale(self.fundo_atual(), (LARGURA_JOGO, ALTURA_JOGO)),
            (0, 0)
        )

        for plataforma in self.plataformas:
            plataforma.draw(self.superficie_jogo)

        self.player.draw(self.superficie_jogo)

        texto = self.fonte.render(f"Pontos: {self.pontuacao}", True, BRANCO)
        self.superficie_jogo.blit(texto, (10, 10))

        jogo_escalado = pygame.transform.smoothscale(
            self.superficie_jogo,
            (self.largura_escalada, self.altura_escalada)
        )
        self.tela.blit(jogo_escalado, (self.x_jogo, self.y_jogo))

    def draw(self):
        if self.estado == MENU:
            self.desenhar_menu()
        elif self.estado == RECORDS:
            self.desenhar_recordes()
        elif self.estado == CREDITS:
            self.desenhar_creditos()
        elif self.estado == ENTER_NAME:
            self.desenhar_enter_name()
        elif self.estado == PLAYING:
            self.desenhar_jogo()

        pygame.display.flip()

    # ==================================================
    # LOOP PRINCIPAL
    # ==================================================
    def run(self):
        while True:
            self.relogio.tick(FPS)
            self.eventos()
            self.update()
            self.draw()