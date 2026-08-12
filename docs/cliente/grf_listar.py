# -*- coding: utf-8 -*-
"""
Lista os arquivos de dentro de um GRF, sem extrair nada.

    python grf_listar.py                      lista tudo do data.grf
    python grf_listar.py --filtro texture     so caminhos contendo 'texture'
    python grf_listar.py --grf en.grf         outro GRF
    python grf_listar.py --extrair <caminho>  grava um arquivo no disco

Le so o cabecalho e a tabela de arquivos - nao percorre os 4 GB.

Formato GRF v2 (0x200) - o kRO normal:
    0x00  "Master of Magic\0"   15+1 bytes
    0x10  chave de encriptacao  14 bytes
    0x1E  offset da tabela      4 bytes (relativo ao fim do cabecalho, 46)
    0x22  seed                  4 bytes
    0x26  filecount             4 bytes  (real = filecount - seed - 7)
    0x2A  versao                4 bytes
    46+offset: tam_comprimido(4) tam_real(4) + tabela zlib
    entrada: nome + \\0 + tam_c(4) tam_c_align(4) tam_real(4) flags(1) offset(4)

Formato GRF v3 (0x300) - magic "Event Horizon", usado quando o GRF passa de
4 GB. Descoberto em 11/ago/2026 lendo o C:/RagnaClient/data.grf (4,2 GB):
    - o filecount do cabecalho ja e o numero real (nao subtrai seed nem 7)
    - o bloco da tabela e (0, tam)(8 bytes) e depois tam_real(4) + zlib
    - a entrada tem 21 bytes de metadado em vez de 17: o offset e de 8 bytes,
      que e justamente o que permite passar de 4 GB
"""
import sys, os, zlib, struct
from pathlib import Path

# ---------------------------------------------------------------------------
# Decriptacao das entradas encriptadas do GRF.
#
# Porte direto de src/common/des.cpp e src/common/grfio.cpp do proprio rAthena
# deste repo - a mesma logica que o servidor usa para ler GRF. Nao e o DES de
# verdade: e uma versao mutilada, com uma unica rodada e sem chave.
#
# Entradas com flag 0x04 tem so os 20 primeiros blocos cifrados; com 0x02, alem
# disso, um bloco a cada 'cycle' e cifrado e um a cada 7 e embaralhado.
# ---------------------------------------------------------------------------

_MASK = (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)

_IP_TABLE = (
    58, 50, 42, 34, 26, 18, 10,  2, 60, 52, 44, 36, 28, 20, 12,  4,
    62, 54, 46, 38, 30, 22, 14,  6, 64, 56, 48, 40, 32, 24, 16,  8,
    57, 49, 41, 33, 25, 17,  9,  1, 59, 51, 43, 35, 27, 19, 11,  3,
    61, 53, 45, 37, 29, 21, 13,  5, 63, 55, 47, 39, 31, 23, 15,  7,
)
_FP_TABLE = (
    40,  8, 48, 16, 56, 24, 64, 32, 39,  7, 47, 15, 55, 23, 63, 31,
    38,  6, 46, 14, 54, 22, 62, 30, 37,  5, 45, 13, 53, 21, 61, 29,
    36,  4, 44, 12, 52, 20, 60, 28, 35,  3, 43, 11, 51, 19, 59, 27,
    34,  2, 42, 10, 50, 18, 58, 26, 33,  1, 41,  9, 49, 17, 57, 25,
)
_TP_TABLE = (
    16,  7, 20, 21, 29, 12, 28, 17,  1, 15, 23, 26,  5, 18, 31, 10,
     2,  8, 24, 14, 32, 27,  3,  9, 19, 13, 30,  6, 22, 11,  4, 25,
)
_S_TABLE = (
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
# grf_substitution: troca alguns valores por outros. E simetrica.
_SUBST = {0x00: 0x2B, 0x2B: 0x00, 0x6C: 0x80, 0x01: 0x68, 0x68: 0x01,
          0x48: 0x77, 0x60: 0xFF, 0x77: 0x48, 0xB9: 0xC0, 0xC0: 0xB9,
          0xFE: 0xEB, 0xEB: 0xFE, 0x80: 0x6C, 0xFF: 0x60}


def _permutar(b, tabela, desloc_destino):
    saida = bytearray(8)
    for i, t in enumerate(tabela):
        j = t - 1
        if b[(j >> 3) & 7] & _MASK[j & 7]:
            saida[((i >> 3) + desloc_destino) & 7] |= _MASK[i & 7]
    return saida


def _des_bloco(b):
    """Decifra 8 bytes, in-place. IP -> uma rodada -> FP."""
    b[:] = _permutar(b, _IP_TABLE, 0)

    # RoundFunction: XOR de b[0..3] com TP(SBOX(E(b[4..7])))
    e = bytearray(8)
    e[0] = ((b[7] << 5) | (b[4] >> 3)) & 0x3f
    e[1] = ((b[4] << 1) | (b[5] >> 7)) & 0x3f
    e[2] = ((b[4] << 5) | (b[5] >> 3)) & 0x3f
    e[3] = ((b[5] << 1) | (b[6] >> 7)) & 0x3f
    e[4] = ((b[5] << 5) | (b[6] >> 3)) & 0x3f
    e[5] = ((b[6] << 1) | (b[7] >> 7)) & 0x3f
    e[6] = ((b[6] << 5) | (b[7] >> 3)) & 0x3f
    e[7] = ((b[7] << 1) | (b[4] >> 7)) & 0x3f

    s = bytearray(8)
    for i in range(4):
        s[i] = (_S_TABLE[i][e[i * 2]] & 0xf0) | (_S_TABLE[i][e[i * 2 + 1]] & 0x0f)

    t = bytearray(8)
    for i, v in enumerate(_TP_TABLE):
        j = v - 1
        if s[j >> 3] & _MASK[j & 7]:
            t[(i >> 3) + 4] |= _MASK[i & 7]

    for i in range(4):
        b[i] ^= t[i + 4]

    b[:] = _permutar(b, _FP_TABLE, 0)


def _desembaralhar(b):
    b[:] = bytes((b[3], b[4], b[6], b[0], b[1], b[2], b[5],
                  _SUBST.get(b[7], b[7])))


def grf_decode(buf, tam_real):
    """buf: bytearray com o dado cru do GRF. tam_real: tamanho comprimido nao
    alinhado (entra no calculo do 'cycle')."""
    nblocos = len(buf) // 8

    # os 20 primeiros blocos sao sempre cifrados
    for i in range(min(20, nblocos)):
        bloco = bytearray(buf[i * 8:i * 8 + 8])
        _des_bloco(bloco)
        buf[i * 8:i * 8 + 8] = bloco
    return nblocos


def grf_decode_full(buf, tam_real):
    nblocos = grf_decode(buf, tam_real)

    # o intervalo entre blocos cifrados depende do numero de digitos do tamanho
    digitos = 1
    n = 10
    while n <= tam_real:
        digitos += 1
        n *= 10
    if digitos < 3:
        ciclo = 1
    elif digitos < 5:
        ciclo = digitos + 1
    elif digitos < 7:
        ciclo = digitos + 9
    else:
        ciclo = digitos + 15

    j = -1
    for i in range(20, nblocos):
        bloco = bytearray(buf[i * 8:i * 8 + 8])
        if i % ciclo == 0:
            _des_bloco(bloco)
            buf[i * 8:i * 8 + 8] = bloco
            continue
        j += 1
        if j % 7 == 0 and j != 0:
            _desembaralhar(bloco)
            buf[i * 8:i * 8 + 8] = bloco


def achar_cliente():
    # Este script agora vive no repo do servidor, entao subir a arvore nao
    # encontra mais o cliente. Mantem a subida (caso alguem copie de volta)
    # e cai nos locais conhecidos. Mesmo conserto do gen-nomes-servidor.py.
    for d in Path(__file__).resolve().parents:
        if (d / 'DATA.ini').exists():
            return d
    for base in (Path(r'C:/RagnaClient/RagnaBeat.Dev'), Path(r'C:/RagnaClient')):
        if (base / 'data.grf').exists():
            return base
    raise SystemExit('nao achei a pasta do cliente')


MAGICOS = (b'Master of Magic', b'Event Horizon\x00c')


def ler_tabela(caminho):
    with open(caminho, 'rb') as f:
        cab = f.read(46)
        if cab[:15] not in MAGICOS:
            raise SystemExit('%s nao parece um GRF' % caminho)
        off, seed, cnt, ver = struct.unpack('<IIII', cab[30:46])
        if ver not in (0x200, 0x300):
            raise SystemExit('versao 0x%X nao suportada (so 0x200 e 0x300)' % ver)
        v3 = (ver == 0x300)
        total = cnt if v3 else cnt - seed - 7
        f.seek(46 + off)
        comp, _real = struct.unpack('<II', f.read(8))
        if v3:
            # no v3 o comp vem zerado; o bloco e tam_real(4) + zlib, e o zlib
            # nao diz onde acaba - por isso le com folga e deixa o
            # decompressobj parar sozinho.
            bloco = f.read(_real + 64 * 1024 * 1024)
            tabela = zlib.decompressobj().decompress(bloco[4:])
        else:
            tabela = zlib.decompress(f.read(comp))

    # v3 usa offset de 8 bytes (o que permite passar de 4 GB); v2 usa 4.
    formato = '<IIIBQ' if v3 else '<IIIBI'
    passo = struct.calcsize(formato)
    arquivos, i = [], 0
    while i < len(tabela):
        fim = tabela.find(b'\x00', i)
        if fim < 0 or fim + 1 + passo > len(tabela):
            break
        nome = tabela[i:fim]
        i = fim + 1
        tam_c, tam_c_align, tam_real, flags, offset = struct.unpack(formato, tabela[i:i + passo])
        i += passo
        if flags & 0x01:            # 0x01 = arquivo; sem isso e diretorio
            arquivos.append((nome, offset, tam_c_align, tam_real, flags, tam_c))
    return arquivos, total


def extrair(caminho_grf, entrada, destino):
    nome, offset, tam_c_align, tam_real, flags, tam_c = entrada
    with open(caminho_grf, 'rb') as f:
        f.seek(46 + offset)
        bruto = bytearray(f.read(tam_c_align))

    # 0x02 = corpo inteiro cifrado; 0x04 = so o cabecalho.
    # O tam_c (nao alinhado) e o que entra no calculo do ciclo - e assim que o
    # rAthena faz em grfio.cpp:433.
    if flags & 0x02:
        grf_decode_full(bruto, tam_c)
    elif flags & 0x04:
        grf_decode(bruto, tam_c)

    dados = zlib.decompress(bytes(bruto))
    if len(dados) != tam_real:
        raise SystemExit('tamanho descomprimido %d, esperado %d' % (len(dados), tam_real))
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
    for nome, _off, _tca, tam_real, flags, _tc in achados[:400]:
        cifra = '' if not (flags & 0x06) else '  [cifrado 0x%02X]' % flags
        print('  %-66s %8d bytes%s' % (nome.decode('latin-1')[:66], tam_real, cifra))
    if len(achados) > 400:
        print('  ... e mais %d' % (len(achados) - 400))
    return 0


if __name__ == '__main__':
    sys.exit(main())
