# -*- coding: utf-8 -*-
"""
Monta o patcher dentro de um build do cliente.

    python patcher/montar.py                 usa o build mais recente
    python patcher/montar.py --versao 0.0.11 escolhe o build
    python patcher/montar.py --dry           so relata

O que ele poe no build, ao lado do RagnaBeat.exe:

    RagnaBeatPatcher.exe   o Thor.exe, renomeado
    config.ini             configuracao local (o IP do servidor esta AQUI)
    images/                fundo e botoes, de patcher/gerar-visual.py
    Scripts/main.js        obrigatorio - sem ele o Thor nem abre
    Languages/Default.ini  mensagens em PT-BR

O config.ini vai como ARQUIVO SOLTO, e nao embutido no exe pelo
ConfigGenerator.exe. E de proposito: o endereco da tailnet muda, e assim
trocar o IP e editar uma linha de texto na maquina do tester, em vez de
reembutir e redistribuir o executavel. O custo e que da para ler e alterar -
o que, num teste fechado, nao protege nada que ja nao esteja no clientinfo.xml
ao lado.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
BUILDS = CLIENTE / 'builds'
THOR = CLIENTE / 'DEVTOOLS/Thor Patcher/Patcher/Thor.exe'
NOME_FINAL = 'MidgardPatcher.exe'


def build_alvo(versao):
    if not BUILDS.exists():
        sys.exit('ERRO: %s nao existe - rode o build.py antes' % BUILDS)
    if versao:
        alvo = BUILDS / ('MidgardEternalProdV%s' % versao)
        if not alvo.exists():
            sys.exit('ERRO: %s nao existe' % alvo)
        return alvo
    # o mais recente por numero de versao, nao por data: build refeito por
    # cima teria data nova e versao velha
    def chave(p):
        m = re.search(r'V(\d+)\.(\d+)\.(\d+)$', p.name)
        return tuple(int(x) for x in m.groups()) if m else (-1, -1, -1)
    cands = [p for p in BUILDS.iterdir() if p.is_dir() and chave(p) != (-1, -1, -1)]
    if not cands:
        sys.exit('ERRO: nenhum build em %s' % BUILDS)
    return max(cands, key=chave)


def endereco(cfg):
    m = re.search(r"(?m)^RootURL\s*=\s*'([^']+)'", cfg.read_text(encoding='utf-8'))
    return m.group(1) if m else '(nao achei o RootURL)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--versao')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()

    if not THOR.exists():
        sys.exit('ERRO: nao achei o %s' % THOR)
    imagens = AQUI / 'images'
    if not (imagens / 'bg.bmp').exists():
        sys.exit('ERRO: falta patcher/images/bg.bmp - rode gerar-visual.py')

    destino = build_alvo(args.versao)
    cfg = AQUI / 'config.ini'
    print('build   : %s' % destino.name)
    print('servidor: %s' % endereco(cfg))
    print()

    tarefas = [(cfg, destino / 'config.ini'),
               (THOR, destino / NOME_FINAL),
               (AQUI / 'Scripts/main.js', destino / 'Scripts/main.js'),
               (AQUI / 'Languages/Default.ini', destino / 'Languages/Default.ini'),
               ]
    for p in sorted(imagens.iterdir()):
        if p.suffix.lower() in ('.png', '.bmp', '.jpg'):
            tarefas.append((p, destino / 'images' / p.name))

    for origem, alvo in tarefas:
        print('  %-34s <- %s' % (alvo.relative_to(destino), origem.name))
        if args.dry:
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(origem, alvo)
        except PermissionError:
            # Acontece toda vez que se testa o patcher e se esquece de fecha-lo:
            # o Windows nao deixa sobrescrever exe em uso. A mensagem crua do
            # shutil e um traceback que nao diz o que fazer.
            sys.exit('\nERRO: %s esta em uso e nao pode ser sobrescrito.\n'
                     'Feche o patcher e rode de novo:\n'
                     '  powershell -Command "Stop-Process -Name '
                     'MidgardPatcher -Force"' % alvo.name)

    if args.dry:
        print('\n>>> DRY RUN - nada foi escrito')
        return 0

    print('\n>>> pronto. %d arquivos em %s' % (len(tarefas), destino))
    print('    O tester abre o %s.' % NOME_FINAL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
