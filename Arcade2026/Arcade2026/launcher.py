# -*- coding: utf-8 -*-
"""
ARCADE 2026 - tela inicial dos jogos.

Como usar:   python launcher.py          (ou dê dois cliques em Iniciar.bat)
Diagnóstico: python launcher.py --check  (mostra o que está certo/errado, sem abrir janela)

Cada jogo roda como um processo separado (com a própria pasta como diretório de
trabalho). Ao escolher outro jogo, o anterior é encerrado por completo antes do
novo abrir, então nunca há dois jogos consumindo recursos ao mesmo tempo.
"""
import atexit
import re
import sys
import time
import traceback
from pathlib import Path

import core

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:                      # Python sem tkinter
    tk = None
    messagebox = None

# ----------------------------------------------------------------------------
# Aparência
# ----------------------------------------------------------------------------
FUNDO = "#07070f"
CARTAO = "#12121f"
RODAPE = "#0c0c18"
BORDA = "#26263a"
LINHA = "#2a2a40"
TEXTO = "#eceaff"
MUDO = "#8b8ba8"
CIANO = "#5ee7ff"
OURO = "#ffd23f"
PRATA = "#c9d1d9"
BRONZE = "#e0894b"
VERDE = "#39e07a"
VERMELHO = "#ff4d5e"
AVISO = "#ffb020"
FONTE = "Segoe UI"

TAM_ICONE = 160
LARG_TEXTO = 290
LARG_MIN_CARTAO = 340


def _rgb(hex_cor):
    h = hex_cor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def texto_legivel(fundo_hex):
    """Preto ou branco, o que ficar mais legível sobre a cor de fundo."""
    r, g, b = _rgb(fundo_hex)
    return "#000000" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"


def clarear(hex_cor, fator=0.25):
    r, g, b = _rgb(hex_cor)
    r, g, b = (int(c + (255 - c) * fator) for c in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def dica_do_log(log):
    """Traduz erros comuns do Python em instruções para o usuário."""
    m = re.search(r"No module named '([\w\.]+)'", log or "")
    if m:
        modulo = m.group(1).split(".")[0]
        return (f"Falta instalar o módulo '{modulo}'.\n"
                f"Abra o Prompt de Comando e rode:\n    python -m pip install {modulo}")
    return ""


def registrar_erro(texto):
    try:
        pasta = core.pasta_base() / "logs"
        pasta.mkdir(parents=True, exist_ok=True)
        with open(pasta / "launcher_erro.log", "a", encoding="utf-8") as f:
            f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{texto}\n")
    except OSError:
        pass


def erro_fatal(texto):
    """Mostra um erro mesmo quando tudo mais falhou."""
    try:
        if tk is None:
            raise RuntimeError("sem tkinter")
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("ARCADE 2026", texto)
        raiz.destroy()
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, texto, "ARCADE 2026", 0x10)
        except Exception:
            print(texto, file=sys.stderr)


# ----------------------------------------------------------------------------
# Cartão de um jogo
# ----------------------------------------------------------------------------
class Cartao:
    def __init__(self, app, pai, jogo):
        self.app = app
        self.jogo = jogo
        self.sig = None              # assinatura do arquivo de placar (detecta mudanças)
        self.melhor_valor = None
        self.unidade = ""

        self.frame = tk.Frame(pai, bg=CARTAO, bd=0, cursor="hand2",
                              highlightthickness=2, highlightbackground=BORDA,
                              highlightcolor=BORDA)

        imagem = app.icone_de(jogo)
        if imagem is not None:
            self.lbl_icone = tk.Label(self.frame, image=imagem, bg=CARTAO, bd=0)
            self.lbl_icone.image = imagem
        else:
            self.lbl_icone = self._icone_padrao()
        self.lbl_icone.pack(pady=(18, 8))

        self.lbl_nome = tk.Label(self.frame, text=jogo.nome, font=(FONTE, 15, "bold"),
                                 fg=jogo.cor, bg=CARTAO, wraplength=LARG_TEXTO)
        self.lbl_nome.pack(padx=16)

        self.lbl_desc = tk.Label(self.frame, text=jogo.descricao, font=(FONTE, 9),
                                 fg=MUDO, bg=CARTAO, wraplength=LARG_TEXTO,
                                 justify="center")
        self.lbl_desc.pack(padx=16, pady=(4, 8))

        tk.Frame(self.frame, bg=LINHA, height=1).pack(fill="x", padx=18, pady=(0, 8))

        self.area = tk.Frame(self.frame, bg=CARTAO)
        self.area.pack(fill="x", padx=18)

        # botão e estado ficam grudados na parte de baixo do cartão
        self.lbl_estado = tk.Label(self.frame, text="", font=(FONTE, 9, "bold"),
                                   fg=VERDE, bg=CARTAO, wraplength=LARG_TEXTO)
        self.lbl_estado.pack(side="bottom", pady=(0, 12))
        self.btn = tk.Button(self.frame, text="JOGAR", font=(FONTE, 12, "bold"),
                             relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                             highlightthickness=0, command=self._clicou_botao)
        self.btn.pack(side="bottom", fill="x", padx=18, pady=(12, 6))

        for w in (self.frame, self.lbl_icone, self.lbl_nome, self.lbl_desc, self.area):
            self._ligar_clique(w)

        self.atualizar_placar()
        self.definir_rodando(False)

    # -- utilidades -----------------------------------------------------------
    def _icone_padrao(self):
        c = tk.Canvas(self.frame, width=TAM_ICONE, height=TAM_ICONE, bg=CARTAO,
                      highlightthickness=0, bd=0)
        c.create_rectangle(8, 8, TAM_ICONE - 8, TAM_ICONE - 8, fill=self.jogo.cor, outline="")
        c.create_text(TAM_ICONE // 2, TAM_ICONE // 2, text=self.jogo.nome[:1].upper(),
                      font=(FONTE, 64, "bold"), fill=texto_legivel(self.jogo.cor))
        return c

    def _ligar_clique(self, widget):
        widget.bind("<Button-1>", self._clicou)

    def _clicou(self, _evento=None):
        self.app.acao(self.jogo, pelo_botao=False)

    def _clicou_botao(self):
        self.app.acao(self.jogo, pelo_botao=True)

    # -- placar ---------------------------------------------------------------
    def _rotulo(self, pai, texto, **opcoes):
        rotulo = tk.Label(pai, text=texto, bg=CARTAO, **opcoes)
        self._ligar_clique(rotulo)
        return rotulo

    def atualizar_placar(self):
        for w in self.area.winfo_children():
            w.destroy()
        placar = core.ler_placar(self.jogo)
        self.sig = core.assinatura_placar(self.jogo)
        melhor = placar.melhor
        self.melhor_valor = melhor.valor if melhor else None
        self.unidade = placar.unidade

        self._rotulo(self.area, "RECORDE", font=(FONTE, 8, "bold"), fg=MUDO).pack(anchor="w")

        if not placar.tem_config:
            self._rotulo(self.area, "Este jogo não tem placar configurado.",
                         font=(FONTE, 9, "italic"), fg=MUDO).pack(anchor="w", pady=(4, 8))
            return
        if melhor is None:
            self._rotulo(self.area, "Ainda sem pontuações. Seja o primeiro!",
                         font=(FONTE, 9, "italic"), fg=MUDO).pack(anchor="w", pady=(4, 8))
            return

        topo = tk.Frame(self.area, bg=CARTAO)
        self._ligar_clique(topo)
        topo.pack(fill="x")
        self._rotulo(topo, core.formatar_valor(melhor.valor),
                     font=(FONTE, 26, "bold"), fg=OURO).pack(side="left")
        self._rotulo(topo, " " + placar.unidade,
                     font=(FONTE, 11, "bold"), fg=OURO).pack(side="left", anchor="s", pady=(0, 7))

        if melhor.nome:
            quem = melhor.nome[:22]
            if melhor.detalhe:
                quem += f"  ({melhor.detalhe})"
        else:
            quem = f"Sobreviveu {melhor.detalhe}" if melhor.detalhe else ""
        if quem:
            self._rotulo(self.area, quem, font=(FONTE, 11, "bold"), fg=TEXTO).pack(anchor="w")

        for pos, reg in enumerate(placar.registros[1:3], start=2):
            cor = PRATA if pos == 2 else BRONZE
            linha = tk.Frame(self.area, bg=CARTAO)
            self._ligar_clique(linha)
            linha.pack(fill="x", pady=(3, 0))
            esquerda = reg.nome[:20] if reg.nome else (f"tempo {reg.detalhe}" if reg.detalhe else "")
            self._rotulo(linha, f"{pos}º  {esquerda}", font=(FONTE, 10), fg=cor).pack(side="left")
            self._rotulo(linha, core.formatar_valor(reg.valor),
                         font=(FONTE, 10, "bold"), fg=cor).pack(side="right")
        tk.Frame(self.area, bg=CARTAO, height=4).pack()

    # -- estado (jogando / parado) ------------------------------------------
    def definir_rodando(self, rodando):
        cor = self.jogo.cor
        problemas = self.jogo.problemas()
        if problemas:
            self.frame.configure(highlightbackground=BORDA, highlightcolor=BORDA)
            self.btn.configure(text="INDISPONÍVEL", state="disabled", bg=LINHA, fg=MUDO,
                               disabledforeground=MUDO)
            self.lbl_estado.configure(text=problemas[0], fg=AVISO)
            return
        borda = VERDE if rodando else BORDA
        self.frame.configure(highlightbackground=borda, highlightcolor=borda)
        if rodando:
            self.btn.configure(text="ENCERRAR", state="normal", bg=VERMELHO, fg="#ffffff",
                               activebackground=clarear(VERMELHO), activeforeground="#ffffff")
            self.lbl_estado.configure(text="● EM EXECUÇÃO", fg=VERDE)
        else:
            self.btn.configure(text="JOGAR", state="normal", bg=cor, fg=texto_legivel(cor),
                               activebackground=clarear(cor),
                               activeforeground=texto_legivel(cor))
            self.lbl_estado.configure(text="", fg=VERDE)


# ----------------------------------------------------------------------------
# Aplicação
# ----------------------------------------------------------------------------
class App:
    def __init__(self, cfg, gerenciador, pygame_ok, pygame_msg):
        self.cfg = cfg
        self.ger = gerenciador
        self.cartoes = []
        self._imagens = {}
        self._cols = 0
        self._ultimo_clique = 0.0

        self.root = tk.Tk()
        self.root.title(cfg.titulo)
        self.root.configure(bg=FUNDO)
        self._geometria_inicial()

        self._montar_topo(pygame_ok, pygame_msg)
        self._montar_rodape()          # antes do corpo, para o rodapé nunca sumir
        self._montar_corpo()
        self._construir_cartoes()

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)
        self.root.bind("<F5>", lambda _e: self.recarregar())
        self._atualizar_estados()
        self.root.after(400, self._tick)

    # -- janela -----------------------------------------------------------
    def _geometria_inicial(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = min(1120, sw - 80), min(800, sh - 120)
        x, y = max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 20)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(min(700, w), min(520, h))

    def _montar_topo(self, pygame_ok, pygame_msg):
        topo = tk.Frame(self.root, bg=FUNDO)
        topo.pack(side="top", fill="x")
        tk.Label(topo, text=self.cfg.titulo, font=(FONTE, 30, "bold"),
                 fg=CIANO, bg=FUNDO).pack(pady=(18, 0))
        tk.Label(topo, text="Clique em um jogo para começar. Ao trocar de jogo, "
                            "o anterior é fechado automaticamente.",
                 font=(FONTE, 10), fg=MUDO, bg=FUNDO).pack(pady=(2, 10))
        avisos = list(self.cfg.avisos)
        if not pygame_ok:
            avisos.insert(0, f"O pygame não foi encontrado neste Python ({pygame_msg}). "
                             "Execute Instalar_pygame.bat e abra o Arcade de novo.")
        for texto in avisos:
            tk.Label(topo, text=texto, font=(FONTE, 10, "bold"), fg="#000000", bg=AVISO,
                     padx=12, pady=6, wraplength=900).pack(fill="x", padx=14, pady=(0, 6))

    def _montar_rodape(self):
        rod = tk.Frame(self.root, bg=RODAPE)
        rod.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(rod, text="", font=(FONTE, 10), fg=MUDO,
                                   bg=RODAPE, anchor="w")
        self.lbl_status.pack(side="left", padx=16, pady=10)

        def botao(texto, comando):
            b = tk.Button(rod, text=texto, command=comando, font=(FONTE, 9, "bold"),
                          relief="flat", bd=0, padx=12, pady=5, bg=LINHA, fg=TEXTO,
                          activebackground=BORDA, activeforeground=TEXTO,
                          disabledforeground=MUDO, cursor="hand2", highlightthickness=0)
            b.pack(side="right", padx=(0, 8), pady=8)
            return b

        botao("Sair", self.fechar)
        botao("Recarregar (F5)", self.recarregar)
        self.btn_parar = botao("Encerrar jogo atual", self.parar)

    def _montar_corpo(self):
        corpo = tk.Frame(self.root, bg=FUNDO)
        corpo.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(corpo, bg=FUNDO, highlightthickness=0, bd=0)
        barra = tk.Scrollbar(corpo, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grade = tk.Frame(self.canvas, bg=FUNDO)
        self._janela = self.canvas.create_window((0, 0), window=self.grade, anchor="nw")
        self.grade.bind("<Configure>",
                        lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._ao_redimensionar)
        self.root.bind_all("<MouseWheel>", self._rolar)

    # -- cartões ----------------------------------------------------------
    def icone_de(self, jogo):
        if not jogo.icone or not jogo.icone.is_file():
            return None
        try:
            img = tk.PhotoImage(file=str(jogo.icone))
            fator = max(1, round(max(img.width(), img.height()) / TAM_ICONE))
            if fator > 1:
                img = img.subsample(fator, fator)
            self._imagens[jogo.id] = img      # mantém referência (senão o Tk apaga)
            return img
        except tk.TclError:
            return None

    def _construir_cartoes(self):
        for c in self.cartoes:
            c.frame.destroy()
        self.cartoes = []
        for w in self.grade.winfo_children():
            w.destroy()
        if not self.cfg.jogos:
            tk.Label(self.grade, font=(FONTE, 12), fg=MUDO, bg=FUNDO, justify="center",
                     text="Nenhum jogo encontrado.\nColoque uma pasta de jogo dentro de "
                          "'jogos' (ou edite o jogos.json) e clique em Recarregar.").pack(pady=60, padx=40)
            return
        for jogo in self.cfg.jogos:
            self.cartoes.append(Cartao(self, self.grade, jogo))
        self._cols = 0                        # força novo posicionamento
        self._posicionar(self._colunas(self.canvas.winfo_width()))

    def _colunas(self, largura):
        return max(1, min(max(1, len(self.cartoes)), largura // LARG_MIN_CARTAO))

    def _posicionar(self, cols):
        if not self.cartoes:
            return
        antigas = self._cols
        for c in self.cartoes:
            c.frame.grid_forget()
        for i, c in enumerate(self.cartoes):
            c.frame.grid(row=i // cols, column=i % cols, padx=14, pady=14, sticky="nsew")
        for col in range(max(cols, antigas)):
            if col < cols:
                self.grade.columnconfigure(col, weight=1, minsize=LARG_MIN_CARTAO - 10)
            else:
                self.grade.columnconfigure(col, weight=0, minsize=0)
        self._cols = cols

    def _ao_redimensionar(self, evento):
        self.canvas.itemconfigure(self._janela, width=evento.width)
        cols = self._colunas(evento.width)
        if cols != self._cols:
            self._posicionar(cols)

    def _rolar(self, evento):
        try:
            if self.grade.winfo_reqheight() > self.canvas.winfo_height():
                self.canvas.yview_scroll(int(-1 * (evento.delta / 120)), "units")
        except tk.TclError:
            pass

    # -- ações ------------------------------------------------------------
    def acao(self, jogo, pelo_botao):
        if self.ger.esta_rodando(jogo):
            if pelo_botao:
                self.parar()
            return
        self.iniciar(jogo)

    def iniciar(self, jogo):
        agora = time.time()
        if agora - self._ultimo_clique < 0.8:          # evita duplo clique acidental
            return
        self._ultimo_clique = agora

        problemas = jogo.problemas()
        if problemas:
            messagebox.showwarning("Jogo indisponível", "\n".join(problemas))
            return

        anterior = self.ger.jogo_atual
        self.status("Fechando o jogo anterior..." if anterior else f"Abrindo {jogo.nome}...", MUDO)
        self.root.update_idletasks()
        try:
            self.ger.iniciar(jogo)        # encerra o anterior por completo e abre o novo
        except OSError as e:
            self._atualizar_estados()
            messagebox.showerror("Não foi possível abrir o jogo",
                                 f"{jogo.nome}\n\n{e}\n\nPython usado: {' '.join(self.ger.comando_python)}")
            return
        self._atualizar_estados()
        if anterior:
            self.status(f"{anterior.nome} foi encerrado. Em execução: {jogo.nome}", jogo.cor)

    def parar(self):
        encerrado = self.ger.parar()
        self._atualizar_estados()
        if encerrado:
            self.status(f"{encerrado.nome} encerrado.", MUDO)

    def recarregar(self):
        try:
            nova = core.carregar_config(self.cfg.base)
        except core.ConfigErro as e:
            messagebox.showerror("Erro ao recarregar", str(e))
            return
        self.cfg = nova
        self._construir_cartoes()
        self._atualizar_estados()
        self.status(f"{len(nova.jogos)} jogo(s) carregado(s).", MUDO)

    def fechar(self):
        self.ger.encerrar_tudo()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # -- estado / status --------------------------------------------------
    def status(self, texto, cor=MUDO):
        self.lbl_status.configure(text=texto, fg=cor)

    def _atualizar_estados(self):
        for c in self.cartoes:
            c.definir_rodando(self.ger.esta_rodando(c.jogo))
        atual = self.ger.jogo_atual
        self.btn_parar.configure(state="normal" if atual else "disabled")
        if atual:
            self.status(f"Em execução: {atual.nome}", VERDE)
        else:
            self.status("Nenhum jogo em execução.", MUDO)

    def _trazer_para_frente(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(250, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except tk.TclError:
            pass

    # -- laço periódico ---------------------------------------------------
    def _tick(self):
        try:
            saida = self.ger.verificar()
            if saida is not None:
                self._ao_terminar(saida)
            self._checar_placares()
        except Exception:
            registrar_erro(traceback.format_exc())
        self.root.after(400, self._tick)

    def _checar_placares(self):
        for c in self.cartoes:
            if core.assinatura_placar(c.jogo) != c.sig:
                antes = c.melhor_valor
                c.atualizar_placar()
                if antes is not None and c.melhor_valor is not None and c.melhor_valor > antes:
                    self.status(f"Novo recorde em {c.jogo.nome}: "
                                f"{core.formatar_valor(c.melhor_valor)} {c.unidade}!", OURO)

    def _ao_terminar(self, saida):
        self._atualizar_estados()
        for c in self.cartoes:
            if c.jogo.id == saida.jogo.id:
                c.atualizar_placar()
        self.status(f"{saida.jogo.nome} foi fechado. Escolha outro jogo.", MUDO)
        self._trazer_para_frente()
        if saida.falhou:
            self._mostrar_erro(saida)

    def _mostrar_erro(self, saida):
        partes = [f"O jogo \"{saida.jogo.nome}\" foi encerrado com erro (código {saida.codigo})."]
        dica = dica_do_log(saida.log_final)
        if dica:
            partes.append(dica)
        if saida.log_final:
            partes.append("Últimas linhas do log:\n\n" + saida.log_final)
        partes.append(f"Log completo: logs/{saida.jogo.id}.log")
        messagebox.showerror("Erro no jogo", "\n\n".join(partes))

    def executar(self):
        self.root.mainloop()


# ----------------------------------------------------------------------------
# Início
# ----------------------------------------------------------------------------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" in argv or "--diagnostico" in argv:
        return core.diagnostico()

    if tk is None:
        erro_fatal("Este Python não tem o tkinter instalado.\n\n"
                   "Reinstale o Python (python.org) marcando a opção 'tcl/tk and IDLE'.")
        return 1
    try:
        base = core.pasta_base()
        try:
            cfg = core.carregar_config(base)
        except core.ConfigErro as e:
            erro_fatal(str(e))
            return 1

        py = core.achar_python(cfg.python)
        if not py:
            erro_fatal("Não encontrei o Python para executar os jogos.\n\n"
                       "Instale o Python ou informe o caminho no campo \"python\" do jogos.json.")
            return 1

        pygame_ok, pygame_msg = core.verificar_pygame(py)
        ger = core.Gerenciador(py, base / "logs")
        atexit.register(ger.encerrar_tudo)      # rede de segurança: nunca deixa jogo órfão

        App(cfg, ger, pygame_ok, pygame_msg).executar()
        return 0
    except Exception:
        texto = traceback.format_exc()
        registrar_erro(texto)
        erro_fatal("O Arcade encontrou um erro inesperado.\n\n"
                   "Os detalhes foram salvos em logs/launcher_erro.log\n\n" + texto[-600:])
        return 1


if __name__ == "__main__":
    sys.exit(main())
