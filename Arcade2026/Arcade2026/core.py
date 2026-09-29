# -*- coding: utf-8 -*-
"""
ARCADE 2026 - núcleo (sem interface gráfica)

Tudo que NÃO depende de tkinter fica aqui:
  * leitura do jogos.json e descoberta automática de jogos novos
  * leitura dos placares (ranking.txt) de cada jogo
  * iniciar / encerrar o processo de cada jogo (um de cada vez)

Só usa a biblioteca padrão do Python.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

EH_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000        # só existe no Windows
CREATE_NEW_PROCESS_GROUP = 0x00000200

CORES_PADRAO = ["#00b4ff", "#ff3fa4", "#ffb020", "#39e07a", "#b36bff", "#ff6b4a"]
LINHAS_LOG_ERRO = 14


# ----------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------
def pasta_base() -> Path:
    """Pasta onde estão launcher.py / jogos.json (funciona também como .exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# ----------------------------------------------------------------------------
# Modelos
# ----------------------------------------------------------------------------
@dataclass
class ConfigPontuacao:
    arquivo: str = "ranking.txt"     # relativo à pasta do jogo
    formato: str = "auto"            # "nome;pontos" | "tempo_kills" | "auto"
    unidade: str = "pts"             # texto exibido depois do valor


@dataclass
class Jogo:
    id: str
    nome: str
    descricao: str
    pasta: Path                      # diretório de trabalho do jogo
    entrada: Path                    # script .py que inicia o jogo
    icone: Optional[Path] = None
    cor: str = "#00b4ff"
    pontuacao: Optional[ConfigPontuacao] = None
    automatico: bool = False         # True = descoberto sozinho na pasta jogos/

    def problemas(self) -> List[str]:
        achados = []
        if not self.pasta.is_dir():
            achados.append(f"Pasta não encontrada: {self.pasta}")
        if not self.entrada.is_file():
            achados.append(f"Arquivo principal não encontrado: {self.entrada.name}")
        return achados


@dataclass
class Config:
    titulo: str
    jogos: List[Jogo]
    python: Optional[str] = None
    base: Path = field(default_factory=pasta_base)
    avisos: List[str] = field(default_factory=list)


@dataclass
class Registro:
    valor: int
    nome: str = ""
    detalhe: str = ""      # ex.: "3:10" (tempo) no Dark Neon
    desempate: int = 0


@dataclass
class Placar:
    registros: List[Registro]
    unidade: str = ""
    tem_config: bool = False       # o jogo declara um arquivo de placar?
    arquivo_existe: bool = False

    @property
    def melhor(self) -> Optional[Registro]:
        return self.registros[0] if self.registros else None


class ConfigErro(Exception):
    """Erro amigável para mostrar ao usuário."""


# ----------------------------------------------------------------------------
# Configuração (jogos.json) e descoberta automática
# ----------------------------------------------------------------------------
def carregar_config(base: Optional[Path] = None) -> Config:
    base = Path(base) if base else pasta_base()
    arquivo = base / "jogos.json"
    if not arquivo.is_file():
        raise ConfigErro(f"Não encontrei o arquivo jogos.json em:\n{base}")
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise ConfigErro(
            f"O jogos.json tem um erro de sintaxe na linha {e.lineno}, coluna {e.colno}:\n"
            f"{e.msg}\n\nDica: confira vírgulas e aspas."
        ) from e

    cfg = Config(titulo=str(dados.get("titulo", "ARCADE 2026")),
                 jogos=[], python=dados.get("python") or None, base=base)

    usados = set()
    for i, item in enumerate(dados.get("jogos", [])):
        try:
            jogo = _jogo_de_dict(item, base, i)
        except (KeyError, TypeError, ValueError) as e:
            cfg.avisos.append(f"Jogo #{i + 1} ignorado no jogos.json (campo faltando/inválido: {e}).")
            continue
        if jogo.id in usados:
            cfg.avisos.append(f"Id repetido no jogos.json: '{jogo.id}'. Só o primeiro será usado.")
            continue
        usados.add(jogo.id)
        cfg.jogos.append(jogo)

    if dados.get("descobrir_automaticamente", True):
        pasta_jogos = base / str(dados.get("pasta_jogos", "jogos"))
        cfg.jogos.extend(descobrir_jogos(pasta_jogos, base, cfg.jogos, usados))

    return cfg


def _jogo_de_dict(item: dict, base: Path, indice: int) -> Jogo:
    pasta = (base / item["pasta"]).resolve()
    entrada = (pasta / item["entrada"]).resolve()
    jogo_id = str(item.get("id") or pasta.name)
    icone = None
    if item.get("icone"):
        icone = (base / item["icone"]).resolve()

    pont = None
    if item.get("pontuacao"):
        p = item["pontuacao"]
        pont = ConfigPontuacao(
            arquivo=str(p.get("arquivo", "ranking.txt")),
            formato=str(p.get("formato", "auto")),
            unidade=str(p.get("unidade", "pts")),
        )
    return Jogo(
        id=jogo_id,
        nome=str(item.get("nome") or jogo_id),
        descricao=str(item.get("descricao", "")),
        pasta=pasta,
        entrada=entrada,
        icone=icone,
        cor=str(item.get("cor") or CORES_PADRAO[indice % len(CORES_PADRAO)]),
        pontuacao=pont,
    )


def descobrir_entrada(pasta: Path) -> Optional[Path]:
    """Acha o .py principal de uma pasta de jogo.

    Desce até 3 níveis quando a pasta só contém outra pasta (comum ao extrair
    .zip/.rar, que geram 'jogo/jogo/main.py').
    """
    atual = pasta
    for _ in range(4):
        pys = sorted(p for p in atual.glob("*.py") if p.is_file())
        if pys:
            for preferido in ("main.py", "jogo.py"):
                for p in pys:
                    if p.name.lower() == preferido:
                        return p
            return pys[0] if len(pys) == 1 else None
        subs = [d for d in atual.iterdir()
                if d.is_dir() and not d.name.startswith((".", "_"))]
        if len(subs) == 1:
            atual = subs[0]
            continue
        return None
    return None


def descobrir_jogos(pasta_jogos: Path, base: Path, ja_conhecidos: List[Jogo],
                    ids_usados: set) -> List[Jogo]:
    """Qualquer pasta nova dentro de jogos/ aparece sozinha na tela inicial."""
    if not pasta_jogos.is_dir():
        return []
    declaradas = [j.pasta.resolve() for j in ja_conhecidos]

    def ja_declarada(d: Path) -> bool:
        d = d.resolve()
        return any(p == d or d in p.parents for p in declaradas)

    novos = []
    for d in sorted(pasta_jogos.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir() or d.name.startswith((".", "_")):
            continue
        if d.name in ids_usados or ja_declarada(d):
            continue
        entrada = descobrir_entrada(d)
        pasta_trab = entrada.parent if entrada else d
        icone = None
        for cand in (base / "icones" / f"{d.name}.png", pasta_trab / "icone.png",
                     pasta_trab / "icon.png"):
            if cand.is_file():
                icone = cand
                break
        nome = re.sub(r"[_\-]+", " ", d.name).strip().title()
        novos.append(Jogo(
            id=d.name, nome=nome,
            descricao="Jogo adicionado automaticamente.",
            pasta=pasta_trab.resolve(),
            entrada=(entrada or (pasta_trab / "main.py")).resolve(),
            icone=icone,
            cor=CORES_PADRAO[(len(ja_conhecidos) + len(novos)) % len(CORES_PADRAO)],
            pontuacao=ConfigPontuacao(),   # tenta ler ranking.txt em modo 'auto'
            automatico=True,
        ))
        ids_usados.add(d.name)
    return novos


# ----------------------------------------------------------------------------
# Placares
# ----------------------------------------------------------------------------
_RE_TEMPO_KILLS = re.compile(r"TEMPO\s*:\s*(\d+)\s*s?\s*\|\s*KILLS\s*:\s*(\d+)", re.IGNORECASE)


def formatar_valor(n: int) -> str:
    """2307 -> '2.307' (padrão brasileiro)."""
    return f"{n:,}".replace(",", ".")


def formatar_tempo(segundos: int) -> str:
    return f"{segundos // 60}:{segundos % 60:02d}"


def _parse_nome_pontos(linhas: List[str]) -> List[Registro]:
    regs = []
    for linha in linhas:
        linha = linha.strip()
        if ";" not in linha:
            continue
        nome, _, pontos = linha.rpartition(";")   # rpartition: nomes com ';' não quebram
        try:
            regs.append(Registro(valor=int(pontos.strip()), nome=nome.strip()))
        except ValueError:
            continue
    regs.sort(key=lambda r: r.valor, reverse=True)
    return regs


def _parse_tab_nome_pontos(linhas: List[str]) -> List[Registro]:
    regs = []
    for linha in linhas:
        campos = linha.rstrip("\r\n").split("\t")
        if len(campos) < 2:
            continue
        try:
            regs.append(Registro(valor=int(campos[1].strip()), nome=campos[0].strip()))
        except ValueError:
            continue
    regs.sort(key=lambda r: r.valor, reverse=True)
    return regs


def _parse_tempo_kills(linhas: List[str]) -> List[Registro]:
    regs = []
    for linha in linhas:
        m = _RE_TEMPO_KILLS.search(linha)
        if m:
            tempo, kills = int(m.group(1)), int(m.group(2))
            regs.append(Registro(valor=kills, detalhe=formatar_tempo(tempo), desempate=tempo))
    regs.sort(key=lambda r: (r.valor, r.desempate), reverse=True)
    return regs


def _ler_linhas(caminho: Path) -> List[str]:
    with open(caminho, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def caminho_placar(jogo: Jogo) -> Optional[Path]:
    if jogo.pontuacao is None:
        return None
    return jogo.pasta / jogo.pontuacao.arquivo


def assinatura_placar(jogo: Jogo):
    """(mtime, tamanho) do arquivo de placar — barato, serve p/ detectar mudança."""
    caminho = caminho_placar(jogo)
    if caminho is None:
        return None
    try:
        st = caminho.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def ler_placar(jogo: Jogo) -> Placar:
    cfg = jogo.pontuacao
    if cfg is None:
        return Placar([], tem_config=False)
    caminho = caminho_placar(jogo)
    if caminho is None or not caminho.is_file():
        return Placar([], unidade=cfg.unidade, tem_config=True, arquivo_existe=False)
    try:
        linhas = _ler_linhas(caminho)
    except OSError:
        return Placar([], unidade=cfg.unidade, tem_config=True, arquivo_existe=False)

    formato = cfg.formato.lower()
    unidade = cfg.unidade
    if formato == "auto":
        if any(_RE_TEMPO_KILLS.search(l) for l in linhas):
            formato, unidade = "tempo_kills", ("kills" if unidade == "pts" else unidade)
        elif any("\t" in l for l in linhas):
            formato = "tab_nome_pontos"
        else:
            formato = "nome;pontos"
    if formato == "tempo_kills":
        regs = _parse_tempo_kills(linhas)
    elif formato == "tab_nome_pontos":
        regs = _parse_tab_nome_pontos(linhas)
    else:
        regs = _parse_nome_pontos(linhas)
    return Placar(regs, unidade=unidade, tem_config=True, arquivo_existe=True)


# ----------------------------------------------------------------------------
# Python que executa os jogos
# ----------------------------------------------------------------------------
def achar_python(preferido: Optional[str] = None) -> Optional[List[str]]:
    """Devolve o comando (lista) do interpretador que roda os jogos."""
    if preferido:
        if Path(preferido).is_file():
            return [preferido]
        achado = shutil.which(preferido)
        return [achado] if achado else None

    if not getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        # pythonw.exe não tem console -> usar python.exe (com janela oculta) p/ ter log
        if EH_WINDOWS and exe.name.lower() == "pythonw.exe" and (exe.parent / "python.exe").is_file():
            exe = exe.parent / "python.exe"
        return [str(exe)]

    # Rodando como .exe: procurar Python instalado no sistema
    for cand in ("python", "python3"):
        achado = shutil.which(cand)
        if achado:
            return [achado]
    py = shutil.which("py")
    return [py, "-3"] if py else None


def _env_jogo() -> dict:
    env = os.environ.copy()
    env["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _flags_windows(novo_grupo: bool = True) -> int:
    if not EH_WINDOWS:
        return 0
    return CREATE_NO_WINDOW | (CREATE_NEW_PROCESS_GROUP if novo_grupo else 0)


def verificar_pygame(comando_python: List[str]) -> tuple:
    """(ok, mensagem). Confere se o Python que roda os jogos enxerga o pygame."""
    try:
        r = subprocess.run(
            comando_python + ["-c", "import pygame; print(pygame.version.ver)"],
            capture_output=True, text=True, timeout=30, env=_env_jogo(),
            creationflags=_flags_windows(False),
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Não consegui executar o Python: {e}"
    if r.returncode == 0:
        return True, (r.stdout.strip().splitlines() or ["?"])[-1]
    ultima = (r.stderr.strip().splitlines() or ["erro desconhecido"])[-1]
    return False, ultima


# ----------------------------------------------------------------------------
# Execução dos jogos (um por vez)
# ----------------------------------------------------------------------------
@dataclass
class Saida:
    jogo: Jogo
    codigo: int
    duracao: float
    log_final: str

    @property
    def falhou(self) -> bool:
        return self.codigo != 0


class Execucao:
    def __init__(self, jogo: Jogo, proc: subprocess.Popen, log_path: Path):
        self.jogo = jogo
        self.proc = proc
        self.log_path = log_path
        self.inicio = time.time()


def _matar_arvore(proc: subprocess.Popen, espera: float = 3.0) -> None:
    """Encerra o processo E todos os filhos, e espera ele realmente morrer."""
    if proc.poll() is not None:
        return
    if EH_WINDOWS:
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, timeout=8,
                           creationflags=CREATE_NO_WINDOW)
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
    try:
        proc.wait(timeout=espera)
    except subprocess.TimeoutExpired:
        try:
            if EH_WINDOWS:
                proc.kill()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
        try:
            proc.wait(timeout=espera)
        except subprocess.TimeoutExpired:
            pass


def _ler_final_do_log(caminho: Path) -> str:
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            linhas = [l.rstrip() for l in f.read().splitlines() if l.strip()]
    except OSError:
        return ""
    return "\n".join(linhas[-LINHAS_LOG_ERRO:])


class Gerenciador:
    """Garante que exista no máximo UM jogo rodando."""

    def __init__(self, comando_python: List[str], pasta_logs: Path):
        self.comando_python = comando_python
        self.pasta_logs = Path(pasta_logs)
        self.atual: Optional[Execucao] = None

    @property
    def jogo_atual(self) -> Optional[Jogo]:
        return self.atual.jogo if self.atual else None

    def esta_rodando(self, jogo: Jogo) -> bool:
        return self.atual is not None and self.atual.jogo.id == jogo.id

    def iniciar(self, jogo: Jogo) -> Execucao:
        # 1) mata o jogo anterior (e espera ele sumir) ANTES de abrir o novo
        self.parar()

        self.pasta_logs.mkdir(parents=True, exist_ok=True)
        log_path = self.pasta_logs / f"{jogo.id}.log"
        log = open(log_path, "w", encoding="utf-8", errors="replace")
        kwargs = {}
        if EH_WINDOWS:
            kwargs["creationflags"] = _flags_windows(True)
        else:
            kwargs["start_new_session"] = True
        try:
            proc = subprocess.Popen(
                self.comando_python + ["-u", str(jogo.entrada)],
                cwd=str(jogo.pasta),            # OBRIGATÓRIO: os jogos usam caminhos relativos
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env=_env_jogo(), **kwargs,
            )
        finally:
            log.close()                          # o processo filho mantém sua própria cópia
        self.atual = Execucao(jogo, proc, log_path)
        return self.atual

    def parar(self) -> Optional[Jogo]:
        """Encerra o jogo atual (se houver). Devolve qual foi encerrado."""
        if self.atual is None:
            return None
        exe = self.atual
        _matar_arvore(exe.proc)
        self.atual = None
        return exe.jogo

    def verificar(self) -> Optional[Saida]:
        """Chame periodicamente: avisa se o jogo terminou sozinho (usuário fechou/crash)."""
        if self.atual is None:
            return None
        codigo = self.atual.proc.poll()
        if codigo is None:
            return None
        exe = self.atual
        self.atual = None
        _matar_arvore(exe.proc)                  # limpa eventuais filhos que sobraram
        return Saida(exe.jogo, codigo, time.time() - exe.inicio,
                     _ler_final_do_log(exe.log_path))

    def encerrar_tudo(self) -> None:
        try:
            self.parar()
        except Exception:
            pass


# ----------------------------------------------------------------------------
# Diagnóstico por linha de comando:  python launcher.py --check
# ----------------------------------------------------------------------------
def diagnostico(base: Optional[Path] = None) -> int:
    print("=== ARCADE 2026 - diagnóstico ===")
    try:
        cfg = carregar_config(base)
    except ConfigErro as e:
        print("ERRO:", e)
        return 1
    print(f"Pasta base : {cfg.base}")
    py = achar_python(cfg.python)
    print(f"Python     : {' '.join(py) if py else 'NÃO ENCONTRADO'}")
    if py:
        ok, msg = verificar_pygame(py)
        print(f"pygame     : {'OK ' + msg if ok else 'PROBLEMA -> ' + msg}")
        if not ok:
            print("             Instale com:  python -m pip install pygame")
    for aviso in cfg.avisos:
        print("AVISO:", aviso)
    print(f"\n{len(cfg.jogos)} jogo(s):")
    for j in cfg.jogos:
        prob = j.problemas()
        print(f"\n- {j.nome}  [{j.id}]{'  (automático)' if j.automatico else ''}")
        print(f"    entrada: {j.entrada}")
        print(f"    ícone  : {j.icone if j.icone and j.icone.is_file() else '(usa ícone padrão)'}")
        if prob:
            for p in prob:
                print("    PROBLEMA:", p)
            continue
        pl = ler_placar(j)
        if not pl.tem_config:
            print("    placar : não configurado")
        elif not pl.registros:
            print("    placar : ainda sem registros")
        else:
            for i, r in enumerate(pl.registros[:3], 1):
                extra = f" ({r.detalhe})" if r.detalhe else ""
                quem = f"{r.nome} - " if r.nome else ""
                print(f"    {i}º {quem}{formatar_valor(r.valor)} {pl.unidade}{extra}")
    return 0
