# -*- coding: utf-8 -*-
"""Lista os alvos de tradução que existem no NOSSO data.grf.

Cuidado com o nome: a lista e o ALVO, nao a fonte. O achar_cliente() aponta
para RagnaBeat.Dev, entao quem e lido aqui e o data.grf do build - o do
C:\\Gravity\\Ragnarok so entra na hora de extrair.

Para as texturas de login e ESC isto foi superado pelo gen-texturas-ptbr.py,
que ja compara os dois GRFs e diz o que da para trocar.
"""
import sys, collections
sys.path.insert(0, '.')
from grf_listar import ler_tabela, achar_cliente

BS = chr(92).encode()                      # \
UI = b'\xc0\xaf\xc0\xfa\xc0\xce\xc5\xcd\xc6\xe4\xc0\xcc\xbd\xba'   # cp949, pasta de UI

raiz = achar_cliente()
arq, _ = ler_tabela(raiz / 'data.grf')

alvos = []
for n, off, tc, tr, fl, _ in arq:
    ln = n.lower()
    if ln == b'data' + BS + b'msgstringtable.csv':
        alvos.append(('msgstringtable', n, tr))
    elif UI.lower() in ln and (BS + b'esc_' in ln or b'login_interface' + BS in ln):
        alvos.append(('textura', n, tr))

print('%d arquivos a extrair' % len(alvos))
for k, v in collections.Counter(t for t, _, _ in alvos).items():
    print('  %-16s %d' % (k, v))

destino = raiz / 'DEVTOOLS' / 'PTBR' / '_extraido' / 'LISTA-PARA-EXTRAIR.txt'
destino.parent.mkdir(parents=True, exist_ok=True)
with open(destino, 'wb') as f:
    f.write('Alvos lidos do NOSSO data.grf; a versao PT-BR sai de\r\n'.encode('cp1252'))
    f.write('C:\\Gravity\\Ragnarok\\data.grf (GRF v3 "Event Horizon").\r\n\r\n'.encode('cp1252'))
    f.write('Colocar em C:\\RagnaClient\\RagnaBeat.Dev\\data\\ mantendo a estrutura de pastas.\r\n'.encode('cp1252'))
    f.write('A pasta data\\ vence o GRF por causa do patch DataFolderFirst.\r\n\r\n'.encode('cp1252'))
    for tipo, n, t in sorted(alvos):
        f.write(b'%-14s %-92s %8d bytes\r\n' % (tipo.encode(), n, t))
print()
print('lista salva em', destino)
