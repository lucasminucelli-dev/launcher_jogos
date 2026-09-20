import os


class RankingManager:

    def __init__(self):
        pasta_projeto = os.path.dirname(os.path.abspath(__file__))
        self.arquivo = os.path.join(pasta_projeto, "ranking.txt")
        arquivo_antigo = os.path.join(pasta_projeto, "save", "ranking.txt")

        if not os.path.exists(self.arquivo) and os.path.exists(arquivo_antigo):
            os.replace(arquivo_antigo, self.arquivo)

        if not os.path.exists(self.arquivo):
            with open(self.arquivo, "w", encoding="utf8") as arquivo:
                arquivo.write("")

    def salvar(self, nome, pontos):

        with open(self.arquivo, "a", encoding="utf8") as arquivo:
            arquivo.write(f"{nome};{pontos}\n")

    def carregar(self):

        ranking = []

        with open(self.arquivo, "r", encoding="utf8") as arquivo:

            for linha in arquivo:

                linha = linha.strip()

                if not linha:
                    continue

                nome, pontos = linha.split(";")

                ranking.append(
                    (nome, int(pontos))
                )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return ranking[:10]