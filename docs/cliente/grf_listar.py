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

Entradas encriptadas (flags 0x02 e 0x04) sao decifradas na leitura - veja o
bloco "DES do GRF" abaixo.
"""
import sys, os, zlib, struct
from pathlib import Path


# ---------------------------------------------------------------- DES do GRF
#
# Porte direto de src/common/des.cpp e src/common/grfio.cpp do rAthena deste
# mesmo repositorio - a mesma logica que o servidor usa para ler GRF. Nao e
# DES de verdade: e uma versao mutilada, de uma rodada so e sem chave.
#
# Duas flags mandam no arquivo:
#   0x02  MIXED  - os 20 primeiros blocos decifrados, e dai em diante um a
#                  cada 'ciclo' decifrado e um a cada 7 desembaralhado
#   0x04  HEADER - so os 20 primeiros blocos de 8 bytes
#
# O bloco de 8 bytes vira um inteiro big-endian: o bit global 0 e o mais
# significativo do byte 0, que e como o C indexa com mask[] = {0x80, 0x40...}.

_IP = (
    58, 50, 42, 34, 26, 18, 10,  2,   60, 52, 44, 36, 28, 20, 12,  4,
    62, 54, 46, 38, 30, 22, 14,  6,   64, 56, 48, 40, 32, 24, 16,  8,
    57, 49, 41, 33, 25, 17,  9,  1,   59, 51, 43, 35, 27, 19, 11,  3,
    61, 53, 45, 37, 29, 21, 13,  5,   63, 55, 47, 39, 31, 23, 15,  7,
)

_FP = (
    40,  8, 48, 16, 56, 24, 64, 32,   39,  7, 47, 15, 55, 23, 63, 31,
    38,  6, 46, 14, 54, 22, 62, 30,   37,  5, 45, 13, 53, 21, 61, 29,
    36,  4, 44, 12, 52, 20, 60, 28,   35,  3, 43, 11, 51, 19, 59, 27,
    34,  2, 42, 10, 50, 18, 58, 26,   33,  1, 41,  9, 49, 17, 57, 25,
)

_TP = (
    16,  7, 20, 21,   29, 12, 28, 17,    1, 15, 23, 26,    5, 18, 31, 10,
     2,  8, 24, 14,   32, 27,  3,  9,   19, 13, 30,  6,   22, 11,  4, 25,
)

_SBOX = (
    (0xef, 0x03, 0x41, 0xfd, 0xd8, 0x74, 0x1e, 0x47, 0x26, 0xef, 0xfb, 0x22, 0xb3, 0xd8, 0x84, 0x1e,
     0x39, 0xac, 0xa7, 0x60, 0x62, 0xc1, 0xcd, 0xba, 0x5c, 0x96, 0x90, 0x59, 0x05, 0x3b, 0x7a, 0x85,
     0x40, 0xfd, 0x1e, 0xc8, 0xe7, 0x8a, 0x8b, 0x21, 0xda, 0x43, 0x64, 0x9f, 0x2d, 0x14, 0xb1, 0x72,
     0xf5, 0x5b, 0xc8, 0xb6, 0x9c, 0x37, 0x76, 0xec, 0x39, 0xa0, 0xa3, 0x05, 0x52, 0x6e, 0x0f, 0xd9),
    (0xa7, 0xdd, 0x0d, 0x78, 0x9e, 0x0b, 0xe3, 0x95, 0x60, 0x36, 0x36, 0x4f, 0xf9, 0x60, 0x5a, 0xa3,
     0x11, 0x24, 0xd2, 0x87, 0xc8, 0x52, 0x75, 0xec, 0xbb, 0xc1, 0x4c, 0xba, 0x24, 0xfe, 0x8f, 0x19,
     0xda, 0x13, 0x66, 0xaf, 0x49, 0xd0, 0x90, 0x06, 0x8c, 0x6a, 0xfb, 0x91, 0x37, 0x8d, 0x0d, 0x78,
     0xbf, 0x49, 0x11, 0xf4, 0x23, 0xe5, 0xce, 0x3b, 0x55, 0xbc, 0xa2, 0x57, 0xe8, 0x22, 0x74, 0xce),
    (0x2c, 0xea, 0xc1, 0xbf, 0x4a, 0x24, 0x1f, 0xc2, 0x79, 0x47, 0xa2, 0x7c, 0xb6, 0xd9, 0x68, 0x15,
     0x80, 0x56, 0x5d, 0x01, 0x33, 0xfd, 0xf4, 0xae, 0xde, 0x30, 0x07, 0x9b, 0xe5, 0x83, 0x9b, 0x68,
     0x49, 0xb4, 0x2e, 0x83, 0x1f, 0xc2, 0xb5, 0x7c, 0xa2, 0x19, 0xd8, 0xe5, 0x7c, 0x2f, 0x83, 0xda,
     0xf7, 0x6b, 0x90, 0xfe, 0xc4, 0x01, 0x5a, 0x97, 0x61, 0xa6, 0x3d, 0x40, 0x0b, 0x58, 0xe6, 0x3d),
    (0x4d, 0xd1, 0xb2, 0x0f, 0x28, 0xbd, 0xe4, 0x78, 0xf6, 0x4a, 0x0f, 0x93, 0x8b, 0x17, 0xd1, 0xa4,
     0x3a, 0xec, 0xc9, 0x35, 0x93, 0x56, 0x7e, 0xcb, 0x55, 0x20, 0xa0, 0xfe, 0x6c, 0x89, 0x17, 0x62,
     0x17, 0x62, 0x4b, 0xb1, 0xb4, 0xde, 0xd1, 0x87, 0xc9, 0x14, 0x3c, 0x4a, 0x7e, 0xa8, 0xe2, 0x7d,
     0xa0, 0x9f, 0xf6, 0x5c, 0x6a, 0x09, 0x8d, 0xf0, 0x0f, 0xe3, 0x53, 0x25, 0x95, 0x36, 0x28, 0xcb),
)

# grf_substitution: troca alguns valores por outros, o resto passa reto.
_SUB = bytearray(range(256))
for _a, _b in ((0x00, 0x2B), (0x6C, 0x80), (0x01, 0x68), (0x48, 0x77),
               (0x60, 0xFF), (0xB9, 0xC0), (0xFE, 0xEB)):
    _SUB[_a], _SUB[_b] = _b, _a


def _tabelar(pares):
    """Transforma uma permutacao de bits em 8 tabelas de 256, uma por byte de
    entrada. Assim cada bloco custa 8 buscas em vez de 64 testes de bit."""
    tabs = [[0] * 256 for _ in range(8)]
    for bit_saida, bit_entrada in pares:
        byte, desloc = bit_entrada >> 3, bit_entrada & 7
        alvo = 1 << (63 - bit_saida)
        for v in range(256):
            if v & (0x80 >> desloc):
                tabs[byte][v] |= alvo
    return tabs


_TAB_IP = _tabelar([(i, j - 1) for i, j in enumerate(_IP)])
_TAB_FP = _tabelar([(i, j - 1) for i, j in enumerate(_FP)])
# O TP le os bytes 0-3 e escreve nos bytes 4-7, ou seja, sai 32 bits deslocado.
_TAB_TP = _tabelar([(i + 32, j - 1) for i, j in enumerate(_TP)])


def _permutar(tabs, x):
    return (tabs[0][x >> 56] | tabs[1][(x >> 48) & 0xff] |
            tabs[2][(x >> 40) & 0xff] | tabs[3][(x >> 32) & 0xff] |
            tabs[4][(x >> 24) & 0xff] | tabs[5][(x >> 16) & 0xff] |
            tabs[6][(x >> 8) & 0xff] | tabs[7][x & 0xff])


def _des_bloco(x):
    """des_decrypt_block: IP, uma rodada, FP."""
    x = _permutar(_TAB_IP, x)

    # E: expande os bytes 4-7 (32 bits) em oito grupos de 6 bits
    b4, b5 = (x >> 24) & 0xff, (x >> 16) & 0xff
    b6, b7 = (x >> 8) & 0xff, x & 0xff
    s = _SBOX
    r = ((s[0][((b7 << 5) | (b4 >> 3)) & 0x3f] & 0xf0) |
         (s[0][((b4 << 1) | (b5 >> 7)) & 0x3f] & 0x0f)) << 56
    r |= ((s[1][((b4 << 5) | (b5 >> 3)) & 0x3f] & 0xf0) |
          (s[1][((b5 << 1) | (b6 >> 7)) & 0x3f] & 0x0f)) << 48
    r |= ((s[2][((b5 << 5) | (b6 >> 3)) & 0x3f] & 0xf0) |
          (s[2][((b6 << 1) | (b7 >> 7)) & 0x3f] & 0x0f)) << 40
    r |= ((s[3][((b6 << 5) | (b7 >> 3)) & 0x3f] & 0xf0) |
          (s[3][((b7 << 1) | (b4 >> 7)) & 0x3f] & 0x0f)) << 32

    x ^= (_permutar(_TAB_TP, r) & 0xffffffff) << 32
    return _permutar(_TAB_FP, x)


def _desembaralhar(x):
    """grf_shuffle_dec: reordena os bytes e substitui o ultimo."""
    b = x.to_bytes(8, 'big')
    return int.from_bytes(bytes((b[3], b[4], b[6], b[0],
                                 b[1], b[2], b[5], _SUB[b[7]])), 'big')


def decodificar(buf, flags, tam_origem):
    """Decifra no lugar (buf tem que ser bytearray). tam_origem e o tamanho
    comprimido NAO alinhado - e dele que sai o ciclo."""
    if not flags & 0x06:
        return buf

    nblocos = len(buf) // 8
    if flags & 0x02:
        # o ciclo sai da contagem de digitos do tamanho (grfio.cpp:206-217)
        digitos, lop = 1, 10
        while lop <= tam_origem:
            digitos += 1
            lop *= 10
        if digitos < 3:
            ciclo = 1
        elif digitos < 5:
            ciclo = digitos + 1
        elif digitos < 7:
            ciclo = digitos + 9
        else:
            ciclo = digitos + 15
    else:
        ciclo = None                       # 0x04: so o cabecalho

    for i in range(min(20, nblocos)):
        struct.pack_into('>Q', buf, i * 8,
                         _des_bloco(struct.unpack_from('>Q', buf, i * 8)[0]))

    if ciclo is None:
        return buf

    j = -1
    for i in range(20, nblocos):
        if i % ciclo == 0:
            struct.pack_into('>Q', buf, i * 8,
                             _des_bloco(struct.unpack_from('>Q', buf, i * 8)[0]))
            continue
        j += 1
        if j and j % 7 == 0:
            struct.pack_into('>Q', buf, i * 8,
                             _desembaralhar(struct.unpack_from('>Q', buf, i * 8)[0]))
    return buf


# ------------------------------------------------------------------- leitura

def achar_cliente():
    """Raiz do cliente.

    Subir a arvore so funciona quando o script vive DENTRO do cliente, que era
    o caso antes de ele ser movido para o repo do servidor. Mantida a subida
    para quem copiar o arquivo de volta, com os locais conhecidos como reserva.
    """
    for d in Path(__file__).resolve().parents:
        if (d / 'DATA.ini').exists() or (d / 'DATA.INI').exists():
            return d
    for base in (Path(r'C:/RagnaClient/RagnaBeat.Dev'), Path(r'C:/RagnaClient')):
        if (base / 'data.grf').exists():
            return base
    raise SystemExit('nao achei a pasta do cliente - passe --grf com caminho '
                     'absoluto e verifique C:/RagnaClient')


def ler_tabela(caminho):
    """Le a tabela de um GRF v0x200 (kRO, 'Master of Magic') ou v0x300 (RO LATAM,
    'Event Horizon').

    As duas versoes tem o MESMO cabecalho de 46 bytes. O v3 muda duas coisas:
      - o cabecalho da tabela tem 12 bytes (um campo extra) em vez de 8
      - cada entrada tem 21 bytes depois do nome em vez de 17 (mais 4 no fim)
    Descoberto em 11/ago/2026 comparando os dois arquivos byte a byte.

    Cada entrada sai como (nome, offset, tam_c_align, tam_real, flags, tam_c).
    O tam_c (comprimido, sem alinhamento) so serve para o ciclo do DES.
    """
    with open(caminho, 'rb') as f:
        cab = f.read(46)
        if cab[:15] not in (b'Master of Magic', b'Event Horizon\x00c'):
            raise SystemExit('%s nao parece um GRF' % caminho)
        off, seed, cnt, ver = struct.unpack('<IIII', cab[30:46])
        if ver not in (0x200, 0x300):
            raise SystemExit('versao 0x%X nao suportada' % ver)
        total = cnt - seed - 7
        f.seek(46 + off)
        if ver == 0x300:
            _extra, comp, real = struct.unpack('<III', f.read(12))
            passo = 21
        else:
            comp, real = struct.unpack('<II', f.read(8))
            passo = 17
        tabela = zlib.decompress(f.read(comp))

    arquivos, i = [], 0
    while i < len(tabela):
        fim = tabela.index(b'\x00', i)
        nome = tabela[i:fim]
        i = fim + 1
        tam_c, tam_c_align, tam_real, flags, offset = struct.unpack('<IIIBI', tabela[i:i + 17])
        i += passo
        if flags & 0x01:            # 0x01 = arquivo; sem isso e diretorio
            arquivos.append((nome, offset, tam_c_align, tam_real, flags, tam_c))
    return arquivos, total


def ler_arquivo(caminho_grf, entrada):
    """Devolve o conteudo de uma entrada, decifrando e descomprimindo."""
    nome, offset, tam_c_align, tam_real, flags = entrada[:5]
    tam_c = entrada[5] if len(entrada) > 5 else tam_c_align
    with open(caminho_grf, 'rb') as f:
        f.seek(46 + offset)
        bruto = bytearray(f.read(tam_c_align))
    decodificar(bruto, flags, tam_c)
    return zlib.decompress(bytes(bruto))


def extrair(caminho_grf, entrada, destino):
    dados = ler_arquivo(caminho_grf, entrada)
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
    for nome, off, tc, tr, fl, _ in achados[:400]:
        print('  %-72s %8d bytes' % (nome.decode('latin-1')[:72], tr))
    if len(achados) > 400:
        print('  ... e mais %d' % (len(achados) - 400))
    return 0


if __name__ == '__main__':
    sys.exit(main())
