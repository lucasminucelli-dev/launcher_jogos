import pygame
import random
import math
import time
import sys
import winsound

pygame.init()

# =========================================================
# TELA CHEIA
# =========================================================

info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h

tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)
pygame.display.set_caption("DARK NEON - OMEGA")

clock = pygame.time.Clock()
FPS = 60

# =========================================================
# ARQUIVO
# =========================================================

def salvar(tempo, kills):
    with open("ranking.txt", "a", encoding="utf-8") as f:
        f.write(f"TEMPO:{tempo}s | KILLS:{kills}\n")

# =========================================================
# SONS
# =========================================================

def s_tiro(): winsound.Beep(1200, 25)
def s_dano(): winsound.Beep(400, 50)
def s_kill(): winsound.Beep(900, 40)
def s_morte():
    winsound.Beep(200, 200)
    winsound.Beep(80, 400)

# =========================================================
# CORES
# =========================================================

PRETO = (5, 5, 10)
AZUL = (0, 200, 255)
ROXO = (170, 0, 255)
ROSA = (255, 0, 180)
VERMELHO = (255, 60, 60)
AMARELO = (255, 220, 0)
BRANCO = (255, 255, 255)

# =========================================================
# FONTES
# =========================================================

font = pygame.font.SysFont("consolas", 22, True)
font_m = pygame.font.SysFont("consolas", 40, True)
font_g = pygame.font.SysFont("consolas", 100, True)

# =========================================================
# PLAYER
# =========================================================

player = pygame.Rect(LARGURA//2, ALTURA//2, 50, 50)
vida = 60
vel = 8
dano_fx = 0

# =========================================================
# GAME STATE
# =========================================================

menu = True
game_over = False

inicio = time.time()
tempo = 0
kills = 0

inimigos = []
projeteis = []

# =========================================================
# INIMIGO
# =========================================================

def spawn():
    side = random.choice(["t","b","l","r"])

    if side=="t": x,y=random.randint(0,LARGURA),-50
    elif side=="b": x,y=random.randint(0,LARGURA),ALTURA+50
    elif side=="l": x,y=-50,random.randint(0,ALTURA)
    else: x,y=LARGURA+50,random.randint(0,ALTURA)

    inimigos.append({
        "r": pygame.Rect(x,y,40,40),
        "v": random.uniform(2.2,3.5),
        "c": random.choice([ROSA,ROXO,VERMELHO])
    })

# =========================================================
# TIRO
# =========================================================

def shoot(mx,my):
    dx=mx-player.centerx
    dy=my-player.centery
    d=math.hypot(dx,dy)
    if d==0:return

    projeteis.append({
        "x":player.centerx,
        "y":player.centery,
        "dx":dx/d,
        "dy":dy/d
    })
    s_tiro()

# =========================================================
# START
# =========================================================

for i in range(6):
    spawn()

# =========================================================
# LOOP
# =========================================================

while True:
    clock.tick(FPS)
    mx,my=pygame.mouse.get_pos()

    # =====================================================
    # EVENTOS
    # =====================================================

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit();sys.exit()

        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE:
                pygame.quit();sys.exit()

            if menu and e.key==pygame.K_SPACE:
                menu=False

            if game_over and e.key==pygame.K_r:
                vida=60
                kills=0
                tempo=0
                inicio=time.time()
                inimigos.clear()
                projeteis.clear()
                player.center=(LARGURA//2,ALTURA//2)
                game_over=False

        if e.type==pygame.MOUSEBUTTONDOWN:
            if e.button==1 and not menu and not game_over:
                shoot(mx,my)

    # =====================================================
    # MENU
    # =====================================================

    if menu:
        tela.fill(PRETO)

        title = font_g.render("DARK NEON", True, ROXO)
        tela.blit(title,(LARGURA//2-title.get_width()//2,200))

        sub = font_m.render("OMEGA", True, AZUL)
        tela.blit(sub,(LARGURA//2-sub.get_width()//2,320))

        for i,t in enumerate([
            "WASD MOVE | MOUSE MIRA | CLICK ATIRA",
            "CRIADORES: Kauã Ferrari & Felipe Melo",
            "PRESSIONE ESPACO"
        ]):
            txt = font.render(t, True, BRANCO)
            tela.blit(txt,(LARGURA//2-300,450+i*30))

        pygame.display.update()
        continue

    # =====================================================
    # GAME LOGIC
    # =====================================================

    if not game_over:

        k=pygame.key.get_pressed()

        if k[pygame.K_w]: player.y-=vel
        if k[pygame.K_s]: player.y+=vel
        if k[pygame.K_a]: player.x-=vel
        if k[pygame.K_d]: player.x+=vel

        player.x=max(0,min(LARGURA-player.w,player.x))
        player.y=max(0,min(ALTURA-player.h,player.y))

        tempo=int(time.time()-inicio)

        if len(inimigos)<6+tempo//8:
            spawn()

        # INIMIGOS
        for i in inimigos:
            r=i["r"]

            dx=player.x-r.x
            dy=player.y-r.y
            d=math.hypot(dx,dy)

            if d!=0:
                r.x+=dx/d*i["v"]
                r.y+=dy/d*i["v"]

            if player.colliderect(r):
                vida-=1
                dano_fx=10
                s_dano()

        # PROJETEIS
        for p in projeteis[:]:
            p["x"]+=p["dx"]*12
            p["y"]+=p["dy"]*12

            for i in inimigos[:]:
                if i["r"].collidepoint(p["x"],p["y"]):
                    inimigos.remove(i)
                    projeteis.remove(p)
                    kills+=1
                    s_kill()
                    break

        if vida<=0:
            game_over=True
            s_morte()
            salvar(tempo,kills)

    # =====================================================
    # FUNDO NEON
    # =====================================================

    tela.fill(PRETO)

    for x in range(0,LARGURA,60):
        pygame.draw.line(tela,(20,20,40),(x,0),(x,ALTURA))

    for y in range(0,ALTURA,60):
        pygame.draw.line(tela,(20,20,40),(0,y),(LARGURA,y))

    # =====================================================
    # PLAYER
    # =====================================================

    cor = VERMELHO if dano_fx>0 else ROXO
    if dano_fx>0: dano_fx-=1

    pygame.draw.circle(tela,(0,200,255),player.center,35)
    pygame.draw.rect(tela,cor,player,border_radius=10)

    pygame.draw.circle(tela,BRANCO,(player.x+15,player.y+15),5)
    pygame.draw.circle(tela,BRANCO,(player.x+35,player.y+15),5)

    pygame.draw.line(tela,VERMELHO,player.center,(mx,my),2)
    pygame.draw.circle(tela,VERMELHO,(mx,my),5)

    # =====================================================
    # INIMIGOS
    # =====================================================

    for i in inimigos:
        pygame.draw.rect(tela,i["c"],i["r"],border_radius=8)

    # =====================================================
    # PROJETEIS
    # =====================================================

    for p in projeteis:
        pygame.draw.circle(tela,AMARELO,(int(p["x"]),int(p["y"])),4)

    # =====================================================
    # HUD
    # =====================================================

    tela.blit(font.render(f"T:{tempo}s",True,BRANCO),(20,20))
    tela.blit(font.render(f"K:{kills}",True,BRANCO),(20,45))
    tela.blit(font.render(f"HP:{vida}",True,BRANCO),(20,70))

    # =====================================================
    # GAME OVER + CRÉDITOS (PERFEITO NA TELA)
    # =====================================================

    if game_over:

        overlay=pygame.Surface((LARGURA,ALTURA))
        overlay.set_alpha(240)
        overlay.fill((0,0,0))
        tela.blit(overlay,(0,0))

        title = font_g.render("GAME OVER",True,VERMELHO)
        tela.blit(title,(LARGURA//2-title.get_width()//2,40))

        box = [
            f"TEMPO: {tempo}s | KILLS: {kills}",
            "",
            "CURSO: Sistemas de Informação",
            "ANO: 2026 | INSTITUICAO: IMMES",
            "",
            "CRIADORES: Kauã Ferrari & Felipe Melo",
            "",
            "PRESSIONE R PARA REINICIAR"
        ]

        y=200
        for b in box:
            txt=font.render(b,True,BRANCO)
            tela.blit(txt,(LARGURA//2-txt.get_width()//2,y))
            y+=28

    pygame.display.update()