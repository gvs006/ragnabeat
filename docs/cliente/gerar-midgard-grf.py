# -*- coding: utf-8 -*-
"""Monta a midgard.grf a partir de uma pasta, e confere lendo de volta.

POR QUE ESTA GRF EXISTE

Arquivo solto em data/ so e achado quando NAO existe na data.grf. Para
SOBRESCREVER algo que ja esta na GRF, a pasta solta nao serve - o patch
DataFolderFirst, que deveria inverter isso, nao funciona neste cliente 2025
(ver o bloco no pos-warp.py). A saida e uma GRF propria carregada ANTES da
data.grf no DATA.ini, que e como o ThanatosRO faz.

    [Data]
    0=midgard.grf      <- ganha
    1=en.grf
    2=data.grf
    3=palette.grf

O QUE PODE E O QUE NAO PODE ENTRAR

Entra o que SOBRESCREVE arquivo da data.grf: msgstringtable.csv, BMP de UI
traduzido, icone de status proprio.

NAO entra .lub de outra versao do cliente. Numa GRF prioritaria eles tem o
mesmo poder que teriam com o DataFolderFirst ligado, e o mesmo resultado:
"JOBID nil", "SKID nil", "getTableSize nil". Ja aconteceu em 04/set/2026.

    python gerar-midgard-grf.py <pasta> [saida.grf]

A <pasta> tem que conter a arvore como o cliente a enxerga, comecando em
data\\. Ex.: <pasta>/data/msgstringtable.csv

FORMATO (GRF v0x200, o mesmo da data.grf do kRO)

    0..15   "Master of Magic\\0"
    16..29  chave (14 bytes, zeros - nao usamos cifragem)
    30..33  offset da tabela, RELATIVO a 46
    34..37  seed
    38..41  filecount + seed + 7
    42..45  versao (0x200)
    46..    blocos de dados, cada um zlib
    tabela  int32 tam_comprimido, int32 tam_real, e o zlib da tabela

Cada entrada da tabela: nome + nul + <IIIBI> com
tam_comprimido, tam_comprimido_alinhado, tam_real, flags, offset.
flags = 1 (arquivo, sem cifra). Sem cifra, alinhado == comprimido.
"""
import os
import struct
import sys
import zlib

BS = chr(92)


def montar(pasta, saida):
    arquivos = []
    for raiz, _, nomes in os.walk(pasta):
        for n in nomes:
            p = os.path.join(raiz, n)
            rel = os.path.relpath(p, pasta).replace('/', BS).replace(os.sep, BS)
            arquivos.append((rel, p))
    if not arquivos:
        sys.exit('ERRO: nenhum arquivo em %s' % pasta)
    arquivos.sort()

    dados = bytearray()
    entradas = []
    for rel, p in arquivos:
        bruto = open(p, 'rb').read()
        comp = zlib.compress(bruto, 9)
        off = len(dados)
        dados += comp
        entradas.append((rel, len(comp), len(comp), len(bruto), 1, off))
        print('  + %-46s %8d -> %8d bytes' % (rel, len(bruto), len(comp)))

    tabela = bytearray()
    for rel, c, ca, r, fl, off in entradas:
        tabela += rel.encode('latin-1') + b'\x00'
        tabela += struct.pack('<IIIBI', c, ca, r, fl, off)
    tab_comp = zlib.compress(bytes(tabela), 9)

    cab = bytearray(46)
    cab[0:16] = b'Master of Magic\x00'
    # 16..29 ficam zerados: e a chave, e nao ciframos nada
    # O offset aponta PARA o par de tamanhos, nao para depois dele: o leitor
    # faz seek(46 + off) e le 8 bytes ali. Somar esses 8 aqui foi o erro da
    # primeira versao, e o sintoma e "incorrect header check" no zlib.
    struct.pack_into('<IIII', cab, 30,
                     len(dados),              # offset da tabela, relativo a 46
                     0,                       # seed
                     len(entradas) + 7,       # o leitor faz cnt - seed - 7
                     0x200)                   # versao

    with open(saida, 'wb') as f:
        f.write(bytes(cab))
        f.write(bytes(dados))
        f.write(struct.pack('<II', len(tab_comp), len(tabela)))
        f.write(tab_comp)
    return len(entradas)


def conferir(saida, esperados):
    """Le de volta com o NOSSO leitor - se ele abrir, o cliente abre."""
    import importlib.util
    import pathlib
    aqui = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location('grf', aqui / 'grf_listar.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    idx, _ = m.ler_tabela(pathlib.Path(saida))
    print()
    print('  === conferencia: lendo a GRF de volta ===')
    if len(idx) != esperados:
        sys.exit('  ERRO: tabela tem %d entradas, esperava %d' % (len(idx), esperados))
    for e in idx:
        d = m.ler_arquivo(pathlib.Path(saida), e)
        if len(d) != e[3]:
            sys.exit('  ERRO: %s saiu com %d bytes, esperava %d'
                     % (e[0], len(d), e[3]))
        print('    %-46s %8d bytes  descomprime OK' % (e[0].decode('latin-1'), len(d)))
    print('  tudo certo: %d arquivo(s)' % len(idx))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pasta = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else 'midgard.grf'
    n = montar(pasta, saida)
    conferir(saida, n)
    print()
    print('  %s: %d bytes' % (saida, os.path.getsize(saida)))
