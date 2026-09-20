import os


class RankingManager:

    def __init__(self):

        self.arquivo = "ranking.txt"

        if not os.path.exists(self.arquivo):

            with open(
                self.arquivo,
                "w",
                encoding="utf-8"
            ):
                pass

    def carregar(self):

        ranking = []

        try:

            with open(
                self.arquivo,
                "r",
                encoding="utf-8"
            ) as arquivo:

                for linha in arquivo:

                    linha = linha.strip()

                    if ";" not in linha:
                        continue

                    nome, pontos = linha.split(";")

                    ranking.append(
                        (
                            nome,
                            int(pontos)
                        )
                    )

        except:

            pass

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return ranking

    def salvar_score(
        self,
        nome,
        pontos
    ):

        ranking = self.carregar()

        ranking.append(
            (
                nome,
                pontos
            )
        )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        ranking = ranking[:10]

        with open(
            self.arquivo,
            "w",
            encoding="utf-8"
        ) as arquivo:

            for nome, pontos in ranking:

                arquivo.write(
                    f"{nome};{pontos}\n"
                )

    def eh_recorde(self, pontos):

        ranking = self.carregar()

        if len(ranking) < 10:
            return True

        return pontos > ranking[-1][1]