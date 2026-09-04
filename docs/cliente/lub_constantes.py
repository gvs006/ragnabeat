# -*- coding: utf-8 -*-
"""Le o pool de constantes de um .lub (Lua 5.1 bytecode).

Usado pelo docs/gerar-visuais.py para ler as tabelas do cliente:
  hateffectids.lub   nome do hat effect -> numero
  accessoryid.lub    ACCESSORY_* -> View id
  accname.lub        ACCESSORY_* -> nome do sprite

Nao ha decompilador aqui: o parser le so o POOL DE CONSTANTES de cada funcao,
que e onde ficam os pares (nome, valor) dessas tabelas. Basta para o que
precisamos e evita depender do unluac.

O hateffectids.lub e uma tabela HAT_EF_xxx = N. Ate agora eu vinha assumindo
que a ORDEM das strings no arquivo era a ordem do enum do rAthena. Isso pode
estar certo por acaso e errado de fato - o que decide e o NUMERO que o cliente
guarda. Este script le o numero.

Formato do cabecalho Lua 5.1:
  4 signature | 1 version | 1 format | 1 endian | 1 int | 1 size_t
  1 instruction | 1 lua_Number | 1 integral
Depois cada Function: source, linedefined, lastlined, nups, numparams,
is_vararg, maxstack, code[], constants[], protos[], debug...
"""
import struct
import sys
from pathlib import Path


class Leitor:
    def __init__(self, d):
        self.d = d
        self.i = 0

    def b(self, n):
        v = self.d[self.i:self.i + n]
        self.i += n
        return v

    def u8(self):
        return self.b(1)[0]

    def u32(self):
        return struct.unpack('<I', self.b(4))[0]

    def size_t(self, tam):
        return struct.unpack('<Q' if tam == 8 else '<I', self.b(tam))[0]

    def num(self):
        return struct.unpack('<d', self.b(8))[0]

    def string(self, tam_size_t):
        n = self.size_t(tam_size_t)
        if n == 0:
            return None
        return self.b(n)[:-1].decode('latin-1')


def ler_funcao(r, tam_size_t, saida):
    r.string(tam_size_t)                 # source
    r.u32(); r.u32()                     # linedefined, lastlinedefined
    r.u8(); r.u8(); r.u8(); r.u8()       # nups, numparams, is_vararg, maxstack
    n = r.u32()
    r.b(n * 4)                           # code
    nk = r.u32()
    consts = []
    for _ in range(nk):
        t = r.u8()
        if t == 0:
            consts.append(None)
        elif t == 1:
            consts.append(bool(r.u8()))
        elif t == 3:
            consts.append(r.num())
        elif t == 4:
            consts.append(r.string(tam_size_t))
        else:
            raise ValueError('tipo de constante %d' % t)
    saida.append(consts)
    np = r.u32()
    for _ in range(np):
        ler_funcao(r, tam_size_t, saida)
    # debug
    n = r.u32(); r.b(n * 4)              # lineinfo
    n = r.u32()
    for _ in range(n):
        r.string(tam_size_t); r.u32(); r.u32()
    n = r.u32()
    for _ in range(n):
        r.string(tam_size_t)


def constantes(caminho):
    d = Path(caminho).read_bytes()
    r = Leitor(d)
    assert r.b(4) == b'\x1bLua', 'nao e Lua bytecode'
    r.u8(); r.u8(); r.u8()               # version, format, endian
    r.u8()                               # sizeof(int)
    tam_size_t = r.u8()
    r.u8(); r.u8(); r.u8()               # instruction, lua_Number, integral
    saida = []
    ler_funcao(r, tam_size_t, saida)
    return saida
