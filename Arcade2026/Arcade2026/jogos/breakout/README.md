
# Breakout Arcade - Projeto Completo

## Descrição
Projeto de jogo estilo Breakout desenvolvido em Python utilizando a biblioteca Pygame.

## Funcionalidades Implementadas

### Sistema Base
- Movimentação da raquete
- Bola com colisão
- Sistema de blocos destrutíveis
- Pontuação
- Sistema de vidas

### Melhorias Implementadas
- 3 vidas por partida
- Blocos resistentes (1, 2 ou 3 vidas)
- Sistema de dificuldade
- Sistema de poderes
- HUD
- Ranking simples
- Estrutura organizada em arquivos

## Estrutura da Pasta

- main.py -> arquivo principal
- config.py -> configurações do jogo
- jogo.py -> lógica principal
- powerups.py -> sistema de poderes
- ranking.py -> sistema de ranking
- README.md -> documentação

## Como executar

1. Instale o pygame:

pip install pygame

2. Execute:

python main.py

## Controles

- SETA ESQUERDA -> mover raquete
- SETA DIREITA -> mover raquete

## Poderes

### Superforça
- Dano dobrado
- Duração: 5 segundos

### Supervelocidade
- Bola 1.5x mais rápida
- Duração: 3.5 segundos

## Dificuldades

### Fácil
- Blocos normais
- Mais chance de poderes

### Difícil
- Blocos 3x mais resistentes
- Menos poderes
