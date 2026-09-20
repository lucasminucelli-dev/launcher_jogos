import os

ARQUIVO = "ranking.txt"

# =========================
# SALVAR PONTUAÇÃO
# =========================
def salvar_pontuacao(nome, pontos):

    with open(ARQUIVO, "a", encoding="utf-8") as arquivo:

        arquivo.write(f"{nome};{pontos}\n")

# =========================
# CARREGAR RANKING
# =========================
def carregar_ranking():

    if not os.path.exists(ARQUIVO):
        return []

    ranking = []

    with open(ARQUIVO, "r", encoding="utf-8") as arquivo:

        linhas = arquivo.readlines()

    for linha in linhas:

        try:

            nome, pontos = linha.strip().split(";")

            ranking.append({
                "nome": nome,
                "pontos": int(pontos)
            })

        except:
            pass

    ranking.sort(
        key=lambda jogador: jogador["pontos"],
        reverse=True
    )

    return ranking[:10]

# =========================
# DESCOBRIR POSIÇÃO
# =========================
def descobrir_posicao(nome, pontos):

    ranking = carregar_ranking()

    posicao = 1

    for jogador in ranking:

        if pontos < jogador["pontos"]:
            posicao += 1

    return posicao