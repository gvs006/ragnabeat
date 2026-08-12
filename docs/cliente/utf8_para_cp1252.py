# -*- coding: utf-8 -*-
"""
Converte escapes \\ddd de UTF-8 para cp1252 num fonte Lua decompilado.

Por que existe: os arquivos PT-BR do RO LATAM NAO tem encoding uniforme. O
skilldescript.lub vem em cp1252 (o "a" acentuado e um byte, \\225), mas o
stateiconinfo.lub vem em UTF-8 (o "a" com til sao dois bytes, \\195\\163).
Instalar o segundo como esta produz mojibake, do mesmo tipo que a curandeira
mostrava antes.

Como o .lub e bytecode com strings de tamanho prefixado, nao da para trocar os
bytes no lugar - encolher a string quebra o formato. O caminho e decompilar,
converter aqui, e gravar como texto (o cliente aceita os dois).

    python _utf8_para_cp1252.py entrada.lua saida.lub
"""
import re, sys
from pathlib import Path

ESCAPES = re.compile(r'(?:\\(\d{1,3}))+')
UM = re.compile(r'\\(\d{1,3})')


def converte(txt):
    trocas = [0]
    perdidos = []

    def sub(m):
        crus = bytes(int(x) for x in UM.findall(m.group(0)))
        try:
            texto = crus.decode('utf-8')
        except UnicodeDecodeError:
            return m.group(0)          # nao era UTF-8, deixa como esta
        if all(ord(c) < 128 for c in texto):
            return m.group(0)          # nada a fazer
        try:
            novos = texto.encode('cp1252')
        except UnicodeEncodeError:
            perdidos.append(texto)
            return m.group(0)
        trocas[0] += 1
        return ''.join('\\%d' % b for b in novos)

    return ESCAPES.sub(sub, txt), trocas[0], perdidos


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    entrada, saida = Path(sys.argv[1]), Path(sys.argv[2])
    txt = entrada.read_bytes().decode('latin-1')

    novo, n, perdidos = converte(txt)

    if txt.count('{') != novo.count('{') or txt.count('}') != novo.count('}'):
        raise SystemExit('ERRO: contagem de chaves mudou - abortado')

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_bytes(novo.encode('latin-1'))
    print('%d sequencias convertidas de UTF-8 para cp1252' % n)
    if perdidos:
        print('sem equivalente em cp1252 (mantidos como estavam): %d' % len(perdidos))
        for p in perdidos[:5]:
            print('   ', repr(p))
    print('gravado: %s (%d bytes)' % (saida, saida.stat().st_size))


if __name__ == '__main__':
    main()
