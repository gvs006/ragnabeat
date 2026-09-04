# -*- coding: utf-8 -*-
"""
Descobre em QUAL codificacao o cliente espera o texto do msgstringtable.

    python docs/cliente/sonda-acento.py           instala a sonda
    python docs/cliente/sonda-acento.py --tirar   desfaz

POR QUE PRECISA DE SONDA
O msgstringtable.csv guarda cada texto em base64, entao o arquivo nao denuncia
a codificacao de dentro. E o sintoma na tela nao distingue os casos sozinho:

    acento SUMIU   ("publico")   -> conversao descartou o byte
    acento VIROU LIXO ("pAoblico") -> os bytes foram lidos com o codepage errado
    acento VIROU "?"             -> conversao nao mapeou (foi o que deu com
                                    cp1252 na tela de login, ver traducao.md)

Adivinhar custou duas quebras neste projeto. Entao, em vez de trocar a
codificacao do arquivo inteiro e torcer, a sonda escreve UMA mensagem contendo
a MESMA palavra nas tres codificacoes ao mesmo tempo. So uma vai sair legivel,
e ela responde a pergunta.

A mensagem escolhida aparece no bloco que o cliente exibe ao entrar no jogo -
a mesma do print onde o problema foi visto. Nao precisa de pet, grupo nem nada.

COMO LER O RESULTADO
Entre no jogo e olhe a linha. O trecho que aparecer como "acao" com cedilha e
til e o que vale:

    U=acao  legivel  -> o cliente quer UTF-8   (o arquivo ja esta certo)
    C=acao  legivel  -> o cliente quer cp1252  (converter o arquivo)
    A=acao  legivel  -> so ASCII passa; acento nao e possivel por aqui

Guarde o resultado em docs/traducao.md antes de tirar a sonda.
"""
import base64
import csv
import shutil
import sys
from pathlib import Path

CSV = Path(r'C:/RagnaClient/RagnaBeat.Dev/data/msgstringtable.csv')
BACKUP = CSV.with_suffix('.csv.antes-sonda')

# Aparece no bloco de status ao entrar no jogo - foi uma das linhas do print.
CHAVE = 'MSI_INVITE_PARTY_ACCEPT'

PALAVRA = 'a\u00e7\u00e3o'          # "acao" com cedilha e til


def montar_sonda():
    """Bytes com a mesma palavra em UTF-8, cp1252 e ASCII, lado a lado."""
    return (b'SONDA U=' + PALAVRA.encode('utf-8')
            + b' C=' + PALAVRA.encode('cp1252')
            + b' A=acao')


def b64(b):
    return base64.b64encode(b).decode('ascii')


def carregar():
    linhas = CSV.read_bytes().decode('utf-8', 'replace').splitlines()
    return list(csv.reader(linhas))


def gravar(linhas):
    # o arquivo original usa CRLF; preservar para nao mudar nada alem do texto
    saida = '\r\n'.join(','.join(l) for l in linhas) + '\r\n'
    CSV.write_bytes(saida.encode('utf-8'))


def main():
    if not CSV.exists():
        raise SystemExit('nao achei %s' % CSV)

    if '--tirar' in sys.argv:
        if not BACKUP.exists():
            raise SystemExit('nao ha backup em %s - a sonda nao foi instalada?'
                             % BACKUP.name)
        shutil.copy(BACKUP, CSV)
        BACKUP.unlink()
        print('sonda removida, arquivo restaurado de %s' % BACKUP.name)
        return 0

    if not BACKUP.exists():
        shutil.copy(CSV, BACKUP)
        print('backup: %s' % BACKUP.name)

    chave_b64 = b64(CHAVE.encode('ascii'))
    linhas = carregar()
    achou = False
    for l in linhas:
        if len(l) > 1 and l[0] == chave_b64:
            original = base64.b64decode(l[1] + '=' * (-len(l[1]) % 4))
            l[1] = b64(montar_sonda())
            achou = True
            print('trocado %s' % CHAVE)
            print('   antes: %s' % original.decode('utf-8', 'replace'))
            print('   agora: SONDA U=<utf8> C=<cp1252> A=acao')
            break
    if not achou:
        raise SystemExit('nao achei a chave %s no csv' % CHAVE)

    gravar(linhas)
    print()
    print('Pronto. Entre no jogo e olhe o bloco de mensagens da entrada.')
    print('Depois: python docs/cliente/sonda-acento.py --tirar')
    return 0


if __name__ == '__main__':
    sys.exit(main())
