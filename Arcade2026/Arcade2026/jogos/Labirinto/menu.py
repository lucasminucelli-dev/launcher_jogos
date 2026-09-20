class Menu:

    MENU = 0
    RANKING = 1
    CREDITOS = 2
    JOGO = 3

    def __init__(self):

        self.opcoes = [
            "JOGAR",
            "RANKING",
            "CREDITOS",
            "SAIR"
        ]

        self.selecionado = 0

    def subir(self):

        self.selecionado = (
            self.selecionado - 1
        ) % len(self.opcoes)

    def descer(self):

        self.selecionado = (
            self.selecionado + 1
        ) % len(self.opcoes)

    def opcao_atual(self):

        return self.opcoes[self.selecionado]