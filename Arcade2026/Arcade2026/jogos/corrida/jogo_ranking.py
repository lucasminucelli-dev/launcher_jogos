import pygame
import random
import os

# Inicializa o pygame
pygame.init()

# Inicializa o som
pygame.mixer.init()

# Pasta onde o jogo está salvo
PASTA_DO_JOGO = os.path.dirname(__file__)

# Carrega os sons do jogo
def carregar_som(nome_arquivo):
    caminho = os.path.join(PASTA_DO_JOGO, nome_arquivo)
    try:
        return pygame.mixer.Sound(caminho)
    except pygame.error:
        return None

som_motor = carregar_som("motor_formula1.wav")
som_batida = carregar_som("batida_explosao.wav")

if som_motor:
    som_motor.set_volume(0.35)

if som_batida:
    som_batida.set_volume(0.9)

# Tela
LARGURA = 800
ALTURA = 600

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Corrida Infinita - Ranking de Km")

# FPS
clock = pygame.time.Clock()
FPS = 60

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AZUL = (50, 150, 255)
CINZA = (100, 100, 100)
AMARELO = (255, 255, 0)
VERMELHO = (255, 0, 0)
VERDE = (0, 200, 80)
LARANJA = (255, 120, 0)

# Fontes
fonte = pygame.font.SysFont("Arial", 30)
fonte_media = pygame.font.SysFont("Arial", 24)
fonte_pequena = pygame.font.SysFont("Arial", 20)

# ==========================================
# CARRO DO JOGADOR
# ==========================================
carro_largura = 60
carro_altura = 100
carro_x = LARGURA // 2 - carro_largura // 2
carro_y = ALTURA - 130
velocidade_carro = 7

# ==========================================
# FUNDO ANIMADO
# ==========================================
linhas = []
for i in range(20):
    linhas.append(i * 40)

# ==========================================
# VARIÁVEIS DO JOGO
# ==========================================
obstaculos = []
Km = 0
nome_digitado = ""
nome_jogador = ""
# --- Ranking salvo em disco (para o Arcade 2026 mostrar os recordes) ---
ARQUIVO_RANKING = os.path.join(PASTA_DO_JOGO, "ranking.txt")


def carregar_ranking_do_arquivo():
    lista = []
    try:
        with open(ARQUIVO_RANKING, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                nome, separador, km = linha.strip().rpartition(";")
                if separador and km.isdigit():
                    lista.append({"nome": nome, "km": int(km)})
    except OSError:
        pass
    lista.sort(key=lambda jogador: jogador["km"], reverse=True)
    return lista


ranking = carregar_ranking_do_arquivo()
estado = "DIGITAR_NOME"  # DIGITAR_NOME, JOGANDO, GAME_OVER
pontuacao_salva = False
explosao_ativa = False
tempo_explosao = 0
som_batida_tocado = False

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def escrever_texto(texto, x, y, cor=BRANCO, fonte_usada=None):
    if fonte_usada is None:
        fonte_usada = fonte
    imagem = fonte_usada.render(texto, True, cor)
    tela.blit(imagem, (x, y))


def criar_obstaculos():
    obstaculos.clear()
    for i in range(5):
        x = random.randint(120, 630)
        y = random.randint(-600, -100)
        largura = 50
        altura = 80
        velocidade = random.randint(6, 12)
        cor = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )
        obstaculos.append([x, y, largura, altura, velocidade, cor])


def resetar_partida():
    global carro_x, Km, pontuacao_salva, explosao_ativa, tempo_explosao, som_batida_tocado
    carro_x = LARGURA // 2 - carro_largura // 2
    Km = 0
    pontuacao_salva = False
    explosao_ativa = False
    tempo_explosao = 0
    som_batida_tocado = False
    criar_obstaculos()


def salvar_no_ranking():
    global pontuacao_salva
    if not pontuacao_salva:
        nome_seguro = nome_jogador.replace(";", ",")
        ranking.append({"nome": nome_seguro, "km": Km})
        ranking.sort(key=lambda jogador: jogador["km"], reverse=True)
        try:
            with open(ARQUIVO_RANKING, "a", encoding="utf-8") as arquivo:
                arquivo.write(f"{nome_seguro};{Km}\n")
        except OSError:
            pass
        pontuacao_salva = True

# ==========================================
# DESENHOS DO JOGO
# ==========================================
def desenhar_carro(x, y):
    pygame.draw.rect(tela, AZUL, (x, y, carro_largura, carro_altura), border_radius=10)
    pygame.draw.rect(tela, BRANCO, (x + 10, y + 15, 40, 25), border_radius=5)

    pygame.draw.rect(tela, PRETO, (x - 5, y + 15, 10, 25))
    pygame.draw.rect(tela, PRETO, (x - 5, y + 60, 10, 25))
    pygame.draw.rect(tela, PRETO, (x + carro_largura - 5, y + 15, 10, 25))
    pygame.draw.rect(tela, PRETO, (x + carro_largura - 5, y + 60, 10, 25))


def desenhar_estrada():
    tela.fill(PRETO)

    for i in range(len(linhas)):
        pygame.draw.rect(tela, BRANCO, (LARGURA // 2 - 5, linhas[i], 10, 30))
        linhas[i] += 10
        if linhas[i] > ALTURA:
            linhas[i] = -40

    pygame.draw.line(tela, CINZA, (100, 0), (100, ALTURA), 5)
    pygame.draw.line(tela, CINZA, (700, 0), (700, ALTURA), 5)


def desenhar_obstaculos():
    global Km

    for obstaculo in obstaculos:
        x, y, largura, altura, velocidade, cor = obstaculo

        pygame.draw.rect(tela, cor, (x, y, largura, altura), border_radius=8)
        pygame.draw.rect(tela, BRANCO, (x + 8, y + 10, largura - 16, 15), border_radius=3)

        pygame.draw.rect(tela, PRETO, (x - 3, y + 10, 6, 15))
        pygame.draw.rect(tela, PRETO, (x - 3, y + 50, 6, 15))
        pygame.draw.rect(tela, PRETO, (x + largura - 3, y + 10, 6, 15))
        pygame.draw.rect(tela, PRETO, (x + largura - 3, y + 50, 6, 15))

        obstaculo[1] += velocidade

        if obstaculo[1] > ALTURA:
            obstaculo[0] = random.randint(120, 630)
            obstaculo[1] = random.randint(-300, -100)
            obstaculo[4] = random.randint(6, 12)
            obstaculo[5] = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            Km += 1


def verificar_colisao():
    carro_rect = pygame.Rect(carro_x, carro_y, carro_largura, carro_altura)

    for obstaculo in obstaculos:
        obst_rect = pygame.Rect(obstaculo[0], obstaculo[1], obstaculo[2], obstaculo[3])
        if carro_rect.colliderect(obst_rect):
            return True

    return False


def iniciar_motor():
    if som_motor:
        som_motor.play(-1)


def parar_motor():
    if som_motor:
        som_motor.stop()


def tocar_batida():
    if som_batida:
        som_batida.play()


def desenhar_explosao():
    # Efeito visual simples de explosão no local do carro
    centro_x = carro_x + carro_largura // 2
    centro_y = carro_y + carro_altura // 2
    tempo = pygame.time.get_ticks() - tempo_explosao

    if tempo < 1200:
        raio_base = 25 + tempo // 15
        pygame.draw.circle(tela, LARANJA, (centro_x, centro_y), raio_base)
        pygame.draw.circle(tela, AMARELO, (centro_x, centro_y), max(10, raio_base // 2))
        pygame.draw.circle(tela, VERMELHO, (centro_x, centro_y), raio_base + 18, 5)

        for i in range(18):
            angulo = i * 20
            distancia = raio_base + (i % 4) * 8
            px = centro_x + int(distancia * pygame.math.Vector2(1, 0).rotate(angulo).x)
            py = centro_y + int(distancia * pygame.math.Vector2(1, 0).rotate(angulo).y)
            pygame.draw.circle(tela, AMARELO if i % 2 == 0 else LARANJA, (px, py), 5)


def desenhar_creditos():
    # Créditos no canto inferior direito da tela de Game Over
    x = 485
    y = 455
    escrever_texto("Criadores:", x, y, AMARELO, fonte_pequena)
    escrever_texto("Matheus Augusto Rodrigues", x, y + 22, BRANCO, fonte_pequena)
    escrever_texto("João Pedro Lofrano da Silva", x, y + 44, BRANCO, fonte_pequena)
    escrever_texto("Faculdade: IMMES", x, y + 66, BRANCO, fonte_pequena)
    escrever_texto("Curso: Sistema de Informação (SI)", x, y + 88, BRANCO, fonte_pequena)
    escrever_texto("Professor: Sandro Graziosi", x, y + 110, BRANCO, fonte_pequena)

# ==========================================
# TELAS
# ==========================================
def tela_nome():
    tela.fill(PRETO)
    escrever_texto("CORRIDA INFINITA", 250, 110, AMARELO)
    escrever_texto("Digite o nome do jogador:", 230, 210, BRANCO, fonte_media)

    pygame.draw.rect(tela, BRANCO, (220, 260, 360, 45), 2, border_radius=8)
    escrever_texto(nome_digitado, 235, 268, VERDE, fonte_media)

    escrever_texto("ENTER = jogar", 310, 340, AMARELO, fonte_media)
    escrever_texto("Setas esquerda/direita para controlar o carro", 190, 390, BRANCO, fonte_pequena)

    desenhar_ranking(520, 430, pequeno=True)
    pygame.display.update()


def desenhar_ranking(x=500, y=20, pequeno=False):
    fonte_ranking = fonte_pequena if pequeno else fonte_media
    escrever_texto("RANKING", x, y, AMARELO, fonte_ranking)

    if len(ranking) == 0:
        escrever_texto("Sem jogadores ainda", x, y + 30, BRANCO, fonte_pequena)
        return

    limite = min(5, len(ranking))
    for i in range(limite):
        jogador = ranking[i]
        texto = f"{i + 1}º {jogador['nome']} - {jogador['km']} Km"
        escrever_texto(texto, x, y + 30 + i * 25, BRANCO, fonte_pequena)


def tela_game_over():
    salvar_no_ranking()

    tela.fill(PRETO)
    desenhar_explosao()
    escrever_texto("GAME OVER", 310, 70, VERMELHO)
    escrever_texto(f"Jogador: {nome_jogador}", 280, 130, BRANCO, fonte_media)
    escrever_texto(f"Km feito: {Km}", 320, 170, BRANCO, fonte_media)

    escrever_texto("Ranking dos jogadores:", 270, 230, AMARELO, fonte_media)

    for i, jogador in enumerate(ranking[:10]):
        texto = f"{i + 1}º lugar - {jogador['nome']} - {jogador['km']} Km"
        escrever_texto(texto, 260, 270 + i * 28, BRANCO, fonte_pequena)

    desenhar_creditos()

    escrever_texto("R = novo jogador", 40, 535, AMARELO, fonte_media)
    escrever_texto("ENTER = jogar novamente", 40, 565, AMARELO, fonte_pequena)
    pygame.display.update()

# Inicia os obstáculos
criar_obstaculos()

# ==========================================
# LOOP PRINCIPAL
# ==========================================
rodando = True

while rodando:
    clock.tick(FPS)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if estado == "DIGITAR_NOME":
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    if nome_digitado.strip() != "":
                        nome_jogador = nome_digitado.strip()
                        resetar_partida()
                        iniciar_motor()
                        estado = "JOGANDO"
                elif evento.key == pygame.K_BACKSPACE:
                    nome_digitado = nome_digitado[:-1]
                else:
                    if len(nome_digitado) < 15:
                        nome_digitado += evento.unicode

        elif estado == "GAME_OVER":
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_r:
                    nome_digitado = ""
                    estado = "DIGITAR_NOME"
                elif evento.key == pygame.K_RETURN:
                    resetar_partida()
                    iniciar_motor()
                    estado = "JOGANDO"

    if estado == "DIGITAR_NOME":
        tela_nome()

    elif estado == "JOGANDO":
        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_LEFT]:
            carro_x -= velocidade_carro

        if teclas[pygame.K_RIGHT]:
            carro_x += velocidade_carro

        if carro_x < 110:
            carro_x = 110

        if carro_x > 630:
            carro_x = 630

        desenhar_estrada()
        desenhar_obstaculos()
        desenhar_carro(carro_x, carro_y)

        escrever_texto(f"Jogador: {nome_jogador}", 20, 20, BRANCO, fonte_pequena)
        escrever_texto(f"Km: {Km}", 20, 50, BRANCO, fonte_media)
        desenhar_ranking(560, 20)

        if verificar_colisao():
            parar_motor()
            explosao_ativa = True
            tempo_explosao = pygame.time.get_ticks()
            if not som_batida_tocado:
                tocar_batida()
                som_batida_tocado = True
            estado = "GAME_OVER"

        pygame.display.update()

    elif estado == "GAME_OVER":
        tela_game_over()

pygame.quit()
