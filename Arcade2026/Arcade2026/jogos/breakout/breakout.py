import pygame
import sys

# Inicializa o Pygame
pygame.init()

# Configurações da Janela
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Breakout - Quebra-Blocos")
relogio = pygame.time.Clock()

# Cores (RGB)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AZUL = (50, 150, 255)
VERMELHO = (255, 50, 50)
VERDE = (50, 255, 50)

# Raquete (Jogador)
raquete_largura, raquete_altura = 120, 15
raquete_x = (LARGURA - raquete_largura) // 2
raquete_y = ALTURA - 50
raquete_velocidade = 8

# Bola
bola_raio = 10
bola_x = LARGURA // 2
bola_y = ALTURA // 2
bola_vel_x = 5
bola_vel_y = -5

# Blocos (Matriz)
linhas, colunas = 4, 8
bloco_largura = 85
bloco_altura = 25
bloco_espacamento = 10
margem_topo = 60
margem_esquerda = 25

blocos = []
for l in range(linhas):
    for c in range(colunas):
        bx = margem_esquerda + c * (bloco_largura + bloco_espacamento)
        by = margem_topo + l * (bloco_altura + bloco_espacamento)
        # Cria o retângulo do bloco e define uma cor por linha
        cor = VERMELHO if l < 2 else VERDE
        blocos.append({"rect": pygame.Rect(bx, by, bloco_largura, bloco_altura), "cor": cor})

# Loop Principal do Jogo
jogando = True
while jogando:
    # 1. Eventos (Entradas do usuário)
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False
            pygame.quit()
            sys.exit()

    # Movimentação da raquete pelas teclas
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_LEFT] and raquete_x > 0:
        raquete_x -= raquete_velocidade
    if teclas[pygame.K_RIGHT] and raquete_x < LARGURA - raquete_largura:
        raquete_x += raquete_velocidade

    # 2. Lógica / Atualizações do Jogo
    # Move a bola
    bola_x += bola_vel_x
    bola_y += bola_vel_y

    # Cria objetos Rect virtuais para facilitar as colisões do Pygame
    rect_raquete = pygame.Rect(raquete_x, raquete_y, raquete_largura, raquete_altura)
    rect_bola = pygame.Rect(bola_x - bola_raio, bola_y - bola_raio, bola_raio * 2, bola_raio * 2)

    # Colisão com as paredes laterais e topo
    if bola_x - bola_raio <= 0 or bola_x + bola_raio >= LARGURA:
        bola_vel_x *= -1
    if bola_y - bola_raio <= 0:
        bola_vel_y *= -1

    # Colisão com o chão (Game Over básico: reinicia a bola)
    if bola_y + bola_raio >= ALTURA:
        bola_x, bola_y = LARGURA // 2, ALTURA // 2
        bola_vel_y = -5  # Reinicia subindo

    # Colisão com a Raquete
    if rect_bola.colliderect(rect_raquete):
        # Evita que a bola "grude" na raquete invertendo apenas se estiver descendo
        if bola_vel_y > 0:
            bola_vel_y *= -1

    # Colisão com os Blocos
    for bloco in blocos[:]:  # Copia da lista para poder remover itens com segurança
        if rect_bola.colliderect(bloco["rect"]):
            bola_vel_y *= -1   # Rebate a bola verticalmente
            blocos.remove(bloco)  # Destrói o bloco
            break              # Sai do loop para processar uma colisão por vez

    # 3. Desenho na Tela
    tela.fill(PRETO)  # Limpa a tela com fundo preto

    # Desenha a raquete
    pygame.draw.rect(tela, AZUL, rect_raquete)

    # Desenha a bola
    pygame.draw.circle(tela, BRANCO, (bola_x, bola_y), bola_raio)

    # Desenha os blocos restantes
    for bloco in blocos:
        pygame.draw.rect(tela, bloco["cor"], bloco["rect"])

    # Atualiza a tela e trava a taxa de quadros (FPS)
    pygame.display.flip()
    relogio.tick(60)