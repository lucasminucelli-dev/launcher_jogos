import pygame
import sys

from jogo import iniciar_jogo
from ranking import carregar_ranking

pygame.init()

# =========================
# JANELA
# =========================
LARGURA = 800
ALTURA = 700

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Breakout Arcade")

relogio = pygame.time.Clock()

# =========================
# CORES
# =========================
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AZUL = (50, 150, 255)
VERMELHO = (255, 60, 60)

# =========================
# FONTES
# =========================
fonte_titulo = pygame.font.SysFont("Arial", 60)
fonte_menu = pygame.font.SysFont("Arial", 35)

# =========================
# ESTADOS
# =========================
estado = "menu"

# =========================
# VARIÁVEIS
# =========================
dificuldade = "facil"

nome_jogador = ""

digitando_nome = True

# =========================
# BOTÕES
# =========================
botao_jogar = pygame.Rect(250, 220, 300, 50)
botao_facil = pygame.Rect(250, 290, 300, 50)
botao_dificil = pygame.Rect(250, 360, 300, 50)
botao_ranking = pygame.Rect(250, 430, 300, 50)
botao_creditos = pygame.Rect(250, 500, 300, 50)
botao_sair = pygame.Rect(250, 570, 300, 50)

# =========================
# LOOP PRINCIPAL
# =========================
rodando = True

# =========================
# IMAGEM DE FUNDO DO MENU
# =========================
try:
    background_menu = pygame.image.load("assets/fundoMENU.png").convert()
    background_menu = pygame.transform.scale(background_menu, (LARGURA, ALTURA))
except pygame.error:
    # Caso a imagem não exista, o jogo não quebra e usa o fundo preto padrão
    background_menu = None

while rodando:

    tela.fill(PRETO)

    # =========================
    # EVENTOS
    # =========================
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # =========================
        # MENU
        # =========================
        if estado == "menu":

            # DIGITAR NOME
            if evento.type == pygame.KEYDOWN:

                if digitando_nome:

                    if evento.key == pygame.K_BACKSPACE:
                        nome_jogador = nome_jogador[:-1]

                    elif evento.key == pygame.K_RETURN:
                        digitando_nome = False

                    else:

                        if len(nome_jogador) < 12:
                            nome_jogador += evento.unicode

            # CLIQUE DO MOUSE
            if evento.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()

                # JOGAR
                if botao_jogar.collidepoint(mouse_pos):

                    if nome_jogador.strip() != "":
                        iniciar_jogo(nome_jogador, dificuldade)

                # FÁCIL
                if botao_facil.collidepoint(mouse_pos):
                    dificuldade = "facil"

                # DIFÍCIL
                if botao_dificil.collidepoint(mouse_pos):
                    dificuldade = "dificil"

                # RANKING
                if botao_ranking.collidepoint(mouse_pos):
                    estado = "ranking"

                # CRÉDITOS
                if botao_creditos.collidepoint(mouse_pos):
                 estado = "creditos"
                
                # SAIR
                if botao_sair.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        # =========================
        # RANKING
        # =========================
        elif estado == "ranking":

            if evento.type == pygame.KEYDOWN:

                if evento.key == pygame.K_ESCAPE:
                    estado = "menu"

        elif estado == "creditos":

            if evento.type == pygame.KEYDOWN:

                if evento.key == pygame.K_ESCAPE:
                    estado = "menu"

    # =========================
    # MENU
    # =========================
    if estado == "menu":

        if background_menu:
            tela.blit(background_menu, (0, 0))
        else:
            tela.fill(PRETO)

        titulo = fonte_titulo.render(
            "BREAKOUT",
            True,
            BRANCO
        )

        texto_nome = fonte_menu.render(
            f"Nome: {nome_jogador}",
            True,
            BRANCO
        )

        dificuldade_texto = fonte_menu.render(
            f"Dificuldade: {dificuldade}",
            True,
            BRANCO
        )

        tela.blit(titulo, (220, 70))
        tela.blit(texto_nome, (250, 150))
        tela.blit(dificuldade_texto, (20, ALTURA - 50))

        # =========================
        # BOTÕES
        # =========================
        pygame.draw.rect(tela, AZUL, botao_jogar)
        pygame.draw.rect(tela, AZUL, botao_facil)
        pygame.draw.rect(tela, AZUL, botao_dificil)
        pygame.draw.rect(tela, AZUL, botao_ranking)
        pygame.draw.rect(tela, AZUL, botao_creditos)
        pygame.draw.rect(tela, VERMELHO, botao_sair)

        texto_jogar = fonte_menu.render(
            "JOGAR",
            True,
            BRANCO
        )

        texto_facil = fonte_menu.render(
            "FACIL",
            True,
            BRANCO
        )

        texto_dificil = fonte_menu.render(
            "DIFICIL",
            True,
            BRANCO
        )

        texto_ranking = fonte_menu.render(
            "RANKING",
            True,
            BRANCO
        )

        texto_creditos = fonte_menu.render(
            "CRÉDITOS",
            True,
            BRANCO
        )

        texto_sair = fonte_menu.render(
            "SAIR",
            True,
            BRANCO
        )

        tela.blit(texto_jogar, (340, 230))
        tela.blit(texto_facil, (340, 300))
        tela.blit(texto_dificil, (330, 370))
        tela.blit(texto_ranking, (320, 440))
        tela.blit(texto_creditos, (310, 510))
        tela.blit(texto_sair, (350, 580))

    # =========================
    # TELA RANKING
    # =========================
    elif estado == "ranking":

        titulo = fonte_titulo.render(
            "RANKING",
            True,
            BRANCO
        )

        tela.blit(titulo, (240, 60))

        ranking = carregar_ranking()

        y = 180

        if len(ranking) == 0:

            vazio = fonte_menu.render(
                "Nenhuma pontuacao salva",
                True,
                BRANCO
            )

            tela.blit(vazio, (180, 250))

        else:

            posicao = 1

            for jogador in ranking:

                texto = fonte_menu.render(
                    f"{posicao} - {jogador['nome']} : {jogador['pontos']}",
                    True,
                    BRANCO
                )

                tela.blit(texto, (180, y))

                y += 50
                posicao += 1

        voltar = fonte_menu.render(
            "ESC - Voltar",
            True,
            AZUL
        )

        tela.blit(voltar, (240, 540))
    
    if estado == "creditos":

        titulo = fonte_titulo.render(
            "CRÉDITOS",
            True,
            BRANCO
        )

        tela.blit(titulo, (220, 70))

        creditos = [
            "              ""Desenvolvedores:",
            "Murilo Gregorio e Matheus Molina",
            "",
            "Sistemas de Informação - Immes - 2026",
            "",
            "Imagens: Geradas por IA (ChatGPT e Gemini)",

        ]

        y = 200

        for credito in creditos:

            texto = fonte_menu.render(
                credito,
                True,
                BRANCO
            )

            tela.blit(texto, (150, y))

            y += 50

        voltar = fonte_menu.render(
            "ESC - Voltar",
            True,
            AZUL
        )

        tela.blit(voltar, (240, 540))
    # =========================
    # UPDATE
    # =========================
    pygame.display.flip()

    relogio.tick(60)