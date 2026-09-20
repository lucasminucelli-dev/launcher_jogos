
import pygame
import random

from config import *
from powerups import criar_powerup
from ranking import salvar_pontuacao, descobrir_posicao

pygame.init()
pygame.mixer.init()  # Inicializa o mixer para sons

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Breakout Arcade")

raquete_largura = 140
raquete_altura = 32
bola_raio = 15

som_impacto = pygame.mixer.Sound("assets/sons/impacto.mp3")
som_quebrar = pygame.mixer.Sound("assets/sons/quebrar.mp3")
som_gameover = pygame.mixer.Sound("assets/sons/gameover.mp3")

background = pygame.image.load("assets/background.png").convert()
background = pygame.transform.scale(background, (LARGURA, ALTURA))

paddle_img = pygame.image.load("assets/raquete.png").convert_alpha()
paddle_img = pygame.transform.scale(
    paddle_img,
    (raquete_largura, raquete_altura)
)

ball_img = pygame.image.load("assets/bola.png").convert_alpha()
ball_img = pygame.transform.scale(
    ball_img,
    (bola_raio * 2, bola_raio * 2)
)
bloco_verde_img = pygame.image.load(
    "assets/blocos/bloco1.png"
).convert_alpha()

bloco_amarelo_img = pygame.image.load(
    "assets/blocos/bloco2.png"
).convert_alpha()

bloco_vermelho_img = pygame.image.load(
    "assets/blocos/bloco3.png"
).convert_alpha()

bloco_verde_img = pygame.transform.scale(bloco_verde_img, (85, 25))
bloco_amarelo_img = pygame.transform.scale(bloco_amarelo_img, (85, 25))
bloco_vermelho_img = pygame.transform.scale(bloco_vermelho_img, (85, 25))


relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("Arial", 28)

raquete_largura = 140
raquete_altura = 32

bola_raio = 15

dificuldade = "facil"


def criar_blocos():


    blocos = []

    linhas = 5
    colunas = 8

    bloco_largura = 85
    bloco_altura = 25

    espacamento = 10

    margem_topo = 60
    margem_esquerda = 25

    for l in range(linhas):
        for c in range(colunas):

            x = margem_esquerda + c * (bloco_largura + espacamento)
            y = margem_topo + l * (bloco_altura + espacamento)

            resistencia = random.randint(1,3)

            if dificuldade == "facil":
                resistencia = random.randint(1, 3)
            else:
                resistencia = random.randint(2, 5)

            if resistencia == 1:
                cor = VERDE
            elif resistencia == 2:
                cor = AMARELO
            else:
                cor = VERMELHO

            bloco = {
                "rect": pygame.Rect(x,y,bloco_largura,bloco_altura),
                "vida": resistencia,
                "cor": cor
            }

            blocos.append(bloco)

    return blocos

# =========================
# TELA GAME OVER
# =========================
def tela_game_over(nome, pontos, posicao):

    fonte_titulo = pygame.font.SysFont("Arial", 60)
    fonte_texto = pygame.font.SysFont("Arial", 35)

    tempo_inicio = pygame.time.get_ticks()

    mostrando = True

    while mostrando:

        tela.fill((0,0,0))

        titulo = fonte_titulo.render(
            "GAME OVER",
            True,
            (255,0,0)
        )

        jogador = fonte_texto.render(
            f"Jogador: {nome}",
            True,
            (255,255,255)
        )

        pontos_texto = fonte_texto.render(
            f"Pontuacao: {pontos}",
            True,
            (255,255,255)
        )

        ranking_texto = fonte_texto.render(
            f"Posicao Ranking: {posicao}",
            True,
            (255,255,255)
        )

        voltar = fonte_texto.render(
            "Voltando ao menu...",
            True,
            (50,150,255)
        )

        tela.blit(titulo, (220,120))
        tela.blit(jogador, (240,240))
        tela.blit(pontos_texto, (240,300))
        tela.blit(ranking_texto, (240,360))
        tela.blit(voltar, (220,470))

        pygame.display.flip()

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        tempo_atual = pygame.time.get_ticks()

        # Espera 5 segundos
        if tempo_atual - tempo_inicio > 5000:
            mostrando = False
def tela_tempo_esgotado(nome, pontos, posicao):
    
    fonte_titulo = pygame.font.SysFont("Arial", 60)
    fonte_texto = pygame.font.SysFont("Arial", 35)

    tempo_inicio = pygame.time.get_ticks()

    mostrando = True

    while mostrando:

        tela.fill((0,0,0))

        titulo = fonte_titulo.render(
            "TEMPO ESGOTADO",
            True,
            (255,215,0)
        )

        jogador = fonte_texto.render(
            f"Jogador: {nome}",
            True,
            (255,255,255)
        )

        pontos_texto = fonte_texto.render(
            f"Pontuacao: {pontos}",
            True,
            (255,255,255)
        )

        ranking_texto = fonte_texto.render(
            f"Posicao Ranking: {posicao}",
            True,
            (255,255,255)
        )

        voltar = fonte_texto.render(
            "Voltando ao menu...",
            True,
            (50,150,255)
        )

        tela.blit(titulo, (150,120))
        tela.blit(jogador, (240,240))
        tela.blit(pontos_texto, (240,300))
        tela.blit(ranking_texto, (240,360))
        tela.blit(voltar, (220,470))

        pygame.display.flip()

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        tempo_atual = pygame.time.get_ticks()

        # Espera 5 segundos
        if tempo_atual - tempo_inicio > 5000:
            mostrando = False
    
def iniciar_jogo(nome_jogador, dificuldade_escolhida):

    global dificuldade
    dificuldade = dificuldade_escolhida
    
    vidas = 3
    pontos = 0

    tempo_limite = 80  # segundos
    inicio_tempo = pygame.time.get_ticks()

    raquete_x = (LARGURA - raquete_largura) // 2
    raquete_y = ALTURA - 50

    bola_x = LARGURA // 2
    bola_y = ALTURA // 2

    bola_vel_x = 5
    bola_vel_y = -5

    dano = 1

    blocos = criar_blocos()

    powerups = []

    tempo_forca = 0
    tempo_velocidade = 0

    jogando = True

    pygame.mixer.music.load("assets/sons/musica.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # toca em loop 

    while jogando:

        tempo_restante = max(
    0,
    tempo_limite - (pygame.time.get_ticks() - inicio_tempo) // 1000
        )
        if tempo_restante <= 0:
            salvar_pontuacao(nome_jogador, pontos)
            posicao = descobrir_posicao(nome_jogador, pontos)
            tela_tempo_esgotado(nome_jogador, pontos, posicao) 
            return

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()

        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_LEFT] and raquete_x > 0:
            raquete_x -= 8

        if teclas[pygame.K_RIGHT] and raquete_x < LARGURA - raquete_largura:
            raquete_x += 8

        bola_x += bola_vel_x
        bola_y += bola_vel_y

        rect_raquete = pygame.Rect(
            raquete_x,
            raquete_y,
            raquete_largura,
            raquete_altura
        )

        rect_bola = pygame.Rect(
            bola_x - bola_raio,
            bola_y - bola_raio,
            bola_raio * 2,
            bola_raio * 2
        )

        if bola_x - bola_raio <= 0 or bola_x + bola_raio >= LARGURA:
            bola_vel_x *= -1

        if bola_y - bola_raio <= 0:
            bola_vel_y *= -1

        if bola_y + bola_raio >= ALTURA:

            vidas -= 1
            
            
            if vidas <= 0:

                pygame.mixer.music.stop()   # Para a música de fundo
                som_gameover.play() # Toca o efeito sonoro de fim de jogo
                pygame.time.wait(1000)  # espera 1 segundo
                
                salvar_pontuacao(nome_jogador, pontos)
                posicao = descobrir_posicao(nome_jogador,pontos)
                tela_game_over(nome_jogador,pontos,posicao)
                return
            # Reinicia a bola para a próxima vida
            bola_x = LARGURA // 2
            bola_y = ALTURA // 2
            bola_vel_x = 5
            bola_vel_y = -5
            som_gameover.play()

        if rect_bola.colliderect(rect_raquete):

            if bola_vel_y > 0:
                bola_vel_y *= -1

        for bloco in blocos[:]:

            if rect_bola.colliderect(bloco["rect"]):

                bola_vel_y *= -1
                som_impacto.play()

                bloco["vida"] -= dano
                som_quebrar.play()
            
            if bloco["vida"] ==2:
                    bloco["cor"] = AMARELO
            elif bloco["vida"] ==1:
                    bloco["cor"] = VERDE   

            if bloco["vida"] <= 0: 
                blocos.remove(bloco)
                pontos += 10

                # 30% de chance de gerar um power-up ao destruir o bloco
                if random.random() < 0.3:
                    powerups.append(
                        criar_powerup(
                            bloco["rect"].centerx,
                            bloco["rect"].centery
                        )
                    )

                break

        for poder in powerups[:]:

            poder.mover()

            if poder.rect.top > ALTURA:
                powerups.remove(poder)
                continue

            if poder.rect.colliderect(rect_raquete):

                if poder.tipo == "forca":
                    dano = 2
                    tempo_forca = pygame.time.get_ticks()

                if poder.tipo == "velocidade":
                    bola_vel_x *= 1.5
                    bola_vel_y *= 1.5
                    tempo_velocidade = pygame.time.get_ticks()

                powerups.remove(poder)

        tempo_atual = pygame.time.get_ticks()

        if tempo_atual - tempo_forca > 5000:
            dano = 1

        if tempo_atual - tempo_velocidade > 3500:
            if abs(bola_vel_x) > 5:
                bola_vel_x /= 1.5
                bola_vel_y /= 1.5

        tela.blit(background, (0, 0))

        tela.blit(paddle_img, (raquete_x, raquete_y))

        tela.blit(
    ball_img,
    (bola_x - bola_raio, bola_y - bola_raio)
    )
        
        for bloco in blocos:
            if bloco["cor"] == VERDE:
                tela.blit(bloco_verde_img, bloco["rect"])
            elif bloco["cor"] == AMARELO:
                tela.blit(bloco_amarelo_img, bloco["rect"])
            elif bloco["cor"] == VERMELHO:
                tela.blit(bloco_vermelho_img, bloco["rect"])

        for poder in powerups:
            poder.desenhar(tela)

        texto_vidas = fonte.render(
            f"Vidas: {vidas}",
            True,
            BRANCO
        )

        texto_pontos = fonte.render(
            f"Pontos: {pontos}",
            True,
            BRANCO
        )

        texto_tempo = fonte.render(
    f"Tempo: {tempo_restante}s",
    True,
    BRANCO
)
        tela.blit(texto_tempo, (LARGURA//2 - texto_tempo.get_width()//2, 20))

        tela.blit(texto_vidas, (20,20))
        tela.blit(texto_pontos, (600,20))

        pygame.display.flip()
        relogio.tick(FPS)
