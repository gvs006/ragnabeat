# -*- coding: utf-8 -*-
"""
Lista os arquivos de dentro de um GRF, sem extrair nada.

    python grf_listar.py                      lista tudo do data.grf
    python grf_listar.py --filtro texture     so caminhos contendo 'texture'
    python grf_listar.py --grf en.grf         outro GRF
    python grf_listar.py --extrair <caminho>  grava um arquivo no disco

Le so o cabecalho e a tabela de arquivos - nao percorre os 4 GB.

Formato GRF v2 (0x200):
    0x00  "Master of Magic\0"   15+1 bytes
    0x10  chave de encriptacao  14 bytes
    0x1E  offset da tabela      4 bytes (relativo ao fim do cabecalho, 46)
    0x22  seed                  4 bytes
    0x26  filecount             4 bytes  (real = filecount - seed - 7)
    0x2A  versao                4 bytes
    46+offset: tam_comprimido(4) tam_real(4) + tabela zlib
"""
import sys, os, zlib, struct
from pathlib import Path


def achar_cliente():
    for d in Path(__file__).resolve().parents:
        if (d / 'DATA.ini').exists():
            return d
    raise SystemExit('nao achei a pasta do cliente')


def ler_tabela(caminho):
    with open(caminho, 'rb') as f:
        cab = f.read(46)
        if cab[:15] != b'Master of Magic':
            raise SystemExit('%s nao parece um GRF' % caminho)
        off, seed, cnt, ver = struct.unpack('<IIII', cab[30:46])
        if ver != 0x200:
            raise SystemExit('versao 0x%X nao suportada (so 0x200)' % ver)
        total = cnt - seed - 7
        f.seek(46 + off)
        comp, real = struct.unpack('<II', f.read(8))
        tabela = zlib.decompress(f.read(comp))

    arquivos, i = [], 0
    while i < len(tabela):
        fim = tabela.index(b'\x00', i)
        nome = tabela[i:fim]
        i = fim + 1
        tam_c, tam_c_align, tam_real, flags, offset = struct.unpack('<IIIBI', tabela[i:i + 17])
        i += 17
        if flags & 0x01:            # 0x01 = arquivo; sem isso e diretorio
            arquivos.append((nome, offset, tam_c_align, tam_real, flags))
    return arquivos, total


def extrair(caminho_grf, entrada, destino):
    nome, offset, tam_c_align, tam_real, flags = entrada
    with open(caminho_grf, 'rb') as f:
        f.seek(46 + offset)
        bruto = f.read(tam_c_align)
    if flags & 0x02 or flags & 0x04:
        raise SystemExit('arquivo encriptado (flags 0x%02X) - nao suportado' % flags)
    dados = zlib.decompress(bruto)
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    open(destino, 'wb').write(dados)
    return len(dados)


def main():
    args = sys.argv[1:]
    raiz = achar_cliente()
    grf = raiz / (args[args.index('--grf') + 1] if '--grf' in args else 'data.grf')
    filtro = args[args.index('--filtro') + 1].lower() if '--filtro' in args else None

    arquivos, total = ler_tabela(grf)
    print('%s: %d arquivos (cabecalho anuncia %d)' % (grf.name, len(arquivos), total))

    if '--extrair' in args:
        alvo = args[args.index('--extrair') + 1].lower().replace('/', '\\')
        for e in arquivos:
            if e[0].decode('latin-1').lower() == alvo:
                dest = raiz / 'DEVTOOLS' / 'PTBR' / '_extraido' / os.path.basename(alvo)
                n = extrair(grf, e, dest)
                print('extraido: %s (%d bytes)' % (dest, n))
                return 0
        print('nao encontrado:', alvo)
        return 1

    achados = [e for e in arquivos
               if filtro is None or filtro in e[0].decode('latin-1').lower()]
    print('%d correspondem ao filtro %r' % (len(achados), filtro))
    print()
    for nome, off, tc, tr, fl in achados[:400]:
        print('  %-72s %8d bytes' % (nome.decode('latin-1')[:72], tr))
    if len(achados) > 400:
        print('  ... e mais %d' % (len(achados) - 400))
    return 0


if __name__ == '__main__':
    sys.exit(main())
