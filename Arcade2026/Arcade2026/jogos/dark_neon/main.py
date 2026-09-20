# =========================================================
#                    DARK NEON - OMEGA
# =========================================================
#
# Desenvolvido por:
# Kauã Ferrari & Felipe Melo
#
# Engine:
# Python + Pygame
#
# =========================================================
# RECURSOS ULTRA FUTURISTAS
# =========================================================
#
# ✔ Interface Neon
# ✔ Glow Dinâmico
# ✔ Partículas Futuristas
# ✔ Inimigos Inteligentes
# ✔ Dash Cyberpunk
# ✔ Efeito de velocidade
# ✔ Sistema de sobrevivência
# ✔ Créditos cinematográficos
# ✔ Fundo animado
# ✔ Efeito holográfico
# ✔ HUD profissional
# ✔ Sons do próprio Python
# ✔ Estilo AAA
#
# =========================================================

import pygame
import random
import math
import winsound
import time

pygame.init()

# =========================================================
# CONFIG
# =========================================================
LARGURA = 1920
ALTURA = 1080

tela = pygame.display.set_mode((LARGURA, ALTURA))

pygame.display.set_caption("DARK NEON - OMEGA")

clock = pygame.time.Clock()

FPS = 60

# =========================================================
# CORES
# =========================================================
PRETO = (5, 5, 10)

AZUL = (0, 180, 255)

AZUL_CLARO = (120, 240, 255)

ROXO = (170, 0, 255)

ROSA = (255, 0, 180)

VERMELHO = (255, 70, 70)

VERDE = (0, 255, 120)

AMARELO = (255, 220, 0)

BRANCO = (255, 255, 255)

CINZA = (40, 40, 60)

# =========================================================
# FONTES
# =========================================================
fonte = pygame.font.SysFont("consolas", 32, bold=True)

fonte_media = pygame.font.SysFont("consolas", 60, bold=True)

fonte_grande = pygame.font.SysFont("consolas", 120, bold=True)

# =========================================================
# PLAYER
# =========================================================
player = pygame.Rect(500, 400, 70, 70)

velocidade = 8

vida = 100

energia = 100

dash = False

dash_timer = 0

# =========================================================
# SCORE
# =========================================================
pontos = 0

combo = 0

tempo_inicio = time.time()

# =========================================================
# EFEITOS
# =========================================================
shake = 0

trilhas = []

particulas = []

# =========================================================
# ORBE
# =========================================================
orbe = pygame.Rect(

    random.randint(100, 1800),
    random.randint(100, 980),

    40,
    40
)

# =========================================================
# INIMIGOS
# =========================================================
inimigos = []

# =========================================================
# ESTADOS
# =========================================================
menu = True

game_over = False

rodando = True

# =========================================================
# SONS
# =========================================================
def som_coleta():

    winsound.Beep(1000, 40)
    winsound.Beep(1400, 20)

def som_dano():

    winsound.Beep(250, 70)

def som_dash():

    winsound.Beep(1600, 40)

def som_gameover():

    winsound.Beep(200, 200)
    winsound.Beep(100, 400)

# =========================================================
# PARTÍCULAS
# =========================================================
def criar_particulas(x, y, cor):

    for i in range(40):

        particulas.append({

            "x": x,
            "y": y,

            "dx": random.uniform(-6, 6),
            "dy": random.uniform(-6, 6),

            "vida": random.randint(20, 60),

            "cor": cor
        })

# =========================================================
# CRIAR INIMIGO
# =========================================================
def criar_inimigo():

    lado = random.choice([
        "topo",
        "baixo",
        "esquerda",
        "direita"
    ])

    if lado == "topo":

        x = random.randint(0, LARGURA)
        y = -100

    elif lado == "baixo":

        x = random.randint(0, LARGURA)
        y = ALTURA + 100

    elif lado == "esquerda":

        x = -100
        y = random.randint(0, ALTURA)

    else:

        x = LARGURA + 100
        y = random.randint(0, ALTURA)

    tamanho = random.randint(60, 90)

    inimigos.append({

        "rect": pygame.Rect(x, y, tamanho, tamanho),

        "vel": random.uniform(2, 4),

        "cor": random.choice([
            ROSA,
            ROXO,
            VERMELHO
        ])
    })

# =========================================================
# START
# =========================================================
for i in range(5):
    criar_inimigo()

# =========================================================
# LOOP PRINCIPAL
# =========================================================
while rodando:

    clock.tick(FPS)

    # =====================================================
    # EVENTOS
    # =====================================================
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            rodando = False

        if event.type == pygame.KEYDOWN:

            if menu:

                if event.key == pygame.K_SPACE:
                    menu = False

            if not menu and not game_over:

                if event.key == pygame.K_LSHIFT:

                    if energia >= 20:

                        dash = True

                        dash_timer = 12

                        energia -= 20

                        som_dash()

            if game_over:

                if event.key == pygame.K_r:

                    pontos = 0

                    combo = 0

                    vida = 100

                    energia = 100

                    inimigos.clear()

                    particulas.clear()

                    trilhas.clear()

                    player.x = 500
                    player.y = 400

                    for i in range(5):
                        criar_inimigo()

                    tempo_inicio = time.time()

                    game_over = False

    # =====================================================
    # MENU
    # =====================================================
    if menu:

        tela.fill(PRETO)

        brilho = abs(math.sin(time.time() * 3)) * 255

        titulo = fonte_grande.render(
            "DARK NEON",
            True,
            (255, brilho, 255)
        )

        subtitulo = fonte_media.render(
            "OMEGA",
            True,
            AZUL_CLARO
        )

        start = fonte.render(
            "PRESSIONE ESPAÇO",
            True,
            BRANCO
        )

        tela.blit(titulo, (430, 280))

        tela.blit(subtitulo, (780, 470))

        tela.blit(start, (760, 700))

        pygame.display.update()

        continue

    # =====================================================
    # GAME
    # =====================================================
    if not game_over:

        teclas = pygame.key.get_pressed()

        vel = velocidade

        if dash:

            vel = 20

            dash_timer -= 1

            if dash_timer <= 0:
                dash = False

        if teclas[pygame.K_a]:
            player.x -= vel

        if teclas[pygame.K_d]:
            player.x += vel

        if teclas[pygame.K_w]:
            player.y -= vel

        if teclas[pygame.K_s]:
            player.y += vel

        # LIMITES
        player.x = max(0, min(LARGURA - player.width, player.x))

        player.y = max(0, min(ALTURA - player.height, player.y))

        # ENERGIA
        energia += 0.2

        if energia > 100:
            energia = 100

        # =================================================
        # TRILHA FUTURISTA
        # =================================================
        trilhas.append((player.centerx, player.centery))

        if len(trilhas) > 20:
            trilhas.pop(0)

        # =================================================
        # ORBE
        # =================================================
        if player.colliderect(orbe):

            pontos += 1

            combo += 1

            shake = 8

            som_coleta()

            criar_particulas(
                orbe.centerx,
                orbe.centery,
                AMARELO
            )

            criar_inimigo()

            orbe.x = random.randint(100, 1800)
            orbe.y = random.randint(100, 980)

        # =================================================
        # INIMIGOS
        # =================================================
        for inimigo in inimigos:

            rect = inimigo["rect"]

            dx = player.x - rect.x
            dy = player.y - rect.y

            dist = math.hypot(dx, dy)

            if dist != 0:

                rect.x += int((dx / dist) * inimigo["vel"])
                rect.y += int((dy / dist) * inimigo["vel"])

            # COLISÃO
            if player.colliderect(rect):

                vida -= 0.8

                combo = 0

                shake = 18

                som_dano()

                criar_particulas(
                    player.centerx,
                    player.centery,
                    VERMELHO
                )

        # =================================================
        # GAME OVER
        # =================================================
        if vida <= 0:

            vida = 0

            game_over = True

            som_gameover()

    # =====================================================
    # SHAKE
    # =====================================================
    offset_x = random.randint(-shake, shake)

    offset_y = random.randint(-shake, shake)

    if shake > 0:
        shake -= 1

    # =====================================================
    # FUNDO
    # =====================================================
    tela.fill(PRETO)

    # GRID FUTURISTA
    for x in range(0, LARGURA, 60):

        pygame.draw.line(
            tela,
            (20, 20, 40),
            (x + offset_x, 0),
            (x + offset_x, ALTURA)
        )

    for y in range(0, ALTURA, 60):

        pygame.draw.line(
            tela,
            (20, 20, 40),
            (0, y + offset_y),
            (LARGURA, y + offset_y)
        )

    # =====================================================
    # ESTRELAS
    # =====================================================
    for i in range(150):

        pygame.draw.circle(
            tela,
            (60, 60, 90),
            (
                random.randint(0, LARGURA),
                random.randint(0, ALTURA)
            ),
            1
        )

    # =====================================================
    # TRILHA
    # =====================================================
    for i, pos in enumerate(trilhas):

        pygame.draw.circle(
            tela,
            AZUL,
            pos,
            max(1, i // 2)
        )

    # =====================================================
    # ORBE
    # =====================================================
    pygame.draw.circle(
        tela,
        (255, 255, 180),
        (orbe.centerx, orbe.centery),
        55
    )

    pygame.draw.circle(
        tela,
        AMARELO,
        (orbe.centerx, orbe.centery),
        20
    )

    # =====================================================
    # PLAYER
    # =====================================================
    pygame.draw.circle(
        tela,
        AZUL_CLARO,
        (player.centerx, player.centery),
        70
    )

    pygame.draw.rect(
        tela,
        ROXO,
        player,
        border_radius=20
    )

    # OLHOS
    pygame.draw.circle(
        tela,
        BRANCO,
        (player.x + 18, player.y + 20),
        7
    )

    pygame.draw.circle(
        tela,
        BRANCO,
        (player.x + 50, player.y + 20),
        7
    )

    # =====================================================
    # INIMIGOS
    # =====================================================
    for inimigo in inimigos:

        rect = inimigo["rect"]

        cor = inimigo["cor"]

        pygame.draw.circle(
            tela,
            cor,
            (rect.centerx, rect.centery),
            rect.width
        )

        pygame.draw.rect(
            tela,
            cor,
            rect,
            border_radius=25
        )

        # OLHOS
        pygame.draw.circle(
            tela,
            BRANCO,
            (rect.x + 18, rect.y + 22),
            9
        )

        pygame.draw.circle(
            tela,
            BRANCO,
            (rect.x + rect.width - 18, rect.y + 22),
            9
        )

    # =====================================================
    # PARTÍCULAS
    # =====================================================
    for p in particulas[:]:

        p["x"] += p["dx"]

        p["y"] += p["dy"]

        p["vida"] -= 1

        pygame.draw.circle(
            tela,
            p["cor"],
            (
                int(p["x"]),
                int(p["y"])
            ),
            4
        )

        if p["vida"] <= 0:
            particulas.remove(p)

    # =====================================================
    # HUD
    # =====================================================
    texto_pontos = fonte.render(
        f"PONTOS: {pontos}",
        True,
        BRANCO
    )

    texto_combo = fonte.render(
        f"COMBO: {combo}",
        True,
        ROSA
    )

    tela.blit(texto_pontos, (30, 20))

    tela.blit(texto_combo, (30, 70))

    # VIDA
    pygame.draw.rect(
        tela,
        CINZA,
        (30, 150, 400, 35),
        border_radius=20
    )

    pygame.draw.rect(
        tela,
        VERDE if vida > 40 else VERMELHO,
        (30, 150, vida * 4, 35),
        border_radius=20
    )

    # ENERGIA
    pygame.draw.rect(
        tela,
        CINZA,
        (30, 210, 400, 25),
        border_radius=20
    )

    pygame.draw.rect(
        tela,
        AZUL,
        (30, 210, energia * 4, 25),
        border_radius=20
    )

    # =====================================================
    # GAME OVER
    # =====================================================
    if game_over:

        overlay = pygame.Surface((LARGURA, ALTURA))

        overlay.set_alpha(230)

        overlay.fill((0, 0, 0))

        tela.blit(overlay, (0, 0))

        tempo_total = int(time.time() - tempo_inicio)

        minutos = tempo_total // 60

        segundos = tempo_total % 60

        texto_go = fonte_grande.render(
            "GAME OVER",
            True,
            ROSA
        )

        texto_pontos_final = fonte_media.render(
            f"PONTUAÇÃO FINAL: {pontos}",
            True,
            BRANCO
        )

        texto_tempo = fonte.render(
            f"TEMPO SOBREVIVIDO: {minutos}m {segundos}s",
            True,
            AZUL_CLARO
        )

        credito1 = fonte.render(
            "CRIADORES: Kauã Ferrari & Felipe Melo",
            True,
            AMARELO
        )

        credito2 = fonte.render(
            "ENGINE: Python + Pygame",
            True,
            BRANCO
        )

        credito3 = fonte.render(
            "Sistema futurista com IA e efeitos neon",
            True,
            ROSA
        )

        credito4 = fonte.render(
            "OBRIGADO POR JOGAR DARK NEON OMEGA",
            True,
            AMARELO
        )

        restart = fonte.render(
            "PRESSIONE R PARA RECOMEÇAR",
            True,
            BRANCO
        )

        tela.blit(texto_go, (520, 120))

        tela.blit(texto_pontos_final, (600, 320))

        tela.blit(texto_tempo, (720, 420))

        tela.blit(credito1, (520, 620))

        tela.blit(credito2, (700, 700))

        tela.blit(credito3, (470, 780))

        tela.blit(credito4, (430, 920))

        tela.blit(restart, (590, 1000))

    pygame.display.update()

pygame.quit()