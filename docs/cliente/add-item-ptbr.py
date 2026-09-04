# -*- coding: utf-8 -*-
"""
Acrescenta itens ao SystemEN/itemInfo_C.lua, em PT-BR, puxando nome e descricao
do dump do RO LATAM.

    python add-item-ptbr.py 1746 5468        acrescenta esses IDs
    python add-item-ptbr.py --dry 1746       so mostra o que faria

POR QUE EXISTE
O itemInfo_C.lua cobre os itens que existem em db/pre-re. Todo item trazido do
renewal (db/ragnabeat_items.yml) fica de fora e aparece no cliente com o nome
coreano/ingles do GRF base - o servidor manda o nome certo para o @ii, mas o
tooltip do inventario vem do cliente.

E IDEMPOTENTE: ID que ja esta no arquivo e pulado. Pode rodar de novo sem medo.

ENCODINGS - a parte que da errado se for no automatico:
  - o texto PT-BR vai em cp1252, como o resto do arquivo (docs/encoding.md)
  - o identifiedResourceName vai em bytes cp949 CRUS, porque e com eles que o
    cliente monta o caminho do sprite. Nome em coreano Unicode nao funciona.
  - o LATAM guarda tudo como bytes UTF-8 escapados em decimal (\\195\\173),
    entao cada campo passa por desescapar() antes de ser reencodado.

Depois de rodar, confira o total em build.py (ITENS_ESPERADOS).
"""
import re
import sys
from pathlib import Path

BS = chr(92)
REPO = Path(__file__).resolve().parent.parent.parent
LATAM = Path(r'C:/RagnaClient/RagnaBeat.Dev/DEVTOOLS/PTBR/iteminfo_ptBR.lua')
ALVO = Path(r'C:/RagnaClient/RagnaBeat.Dev/SystemEN/itemInfo_C.lua')

RE_ESC = re.compile(re.escape(BS) + r'(\d{1,3})')
RE_BLOCO_LATAM = re.compile(r'\[(\d+)\]\s*=\s*\{(.*?)\n  \}', re.S)
# A regex ingenua '"([^"]*)"' nao conhece aspa escapada e PARTE a string no
# meio. Em 12/ago/2026 isso gerou 10 descricoes truncadas no itemInfo_C.lua -
# o texto entre as aspas sumia e sobrava uma string que nunca fecha, com o
# cliente abortando em "unfinished string near". Ver docs/traducao.md.
#
# Esta versao consome ou um caractere comum, ou uma barra invertida mais o
# que vier depois dela - que e como o Lua le.
RE_STR = r'"((?:[^"\\]|\\.)*)"'

# ---------------------------------------------------------------------------
# Correcoes de descricao, por item.
#
# O texto do LATAM descreve a versao de RENEWAL do item. Quando o item entra
# aqui com valor diferente (db/ragnabeat_items.yml), o tooltip passaria a
# mentir para o jogador - "Nivel necessario: 100" num servidor de nivel maximo
# 99, por exemplo. Cada troca abaixo tem um item alterado do outro lado.
#
# Formato: id -> [(de, para), ...]. Aplicado linha a linha na descricao.
# Se o texto do LATAM mudar e um "de" parar de casar, o script avisa.
# ---------------------------------------------------------------------------
AJUSTES = {
    # Arco Elfico: nivel 100 -> 90, e as classes de 3a nao existem aqui
    1746: [('Nível necessário: ^777777100^000000',
            'Nível necessário: ^77777790^000000'),
           ('Classes: ^777777Sentinelas, Musas e Trovadores^000000',
            'Classes: ^777777Caçadores, Bardos e Odaliscas^000000')],
    # Flecha Elfica: nivel 100 -> sem requisito
    1773: [('Nível necessário: ^777777100^000000',
            'Nível necessário: ^7777771^000000')],
    # Mochila da Aventura: DEF 20 -> 10 (teto do pre-re e 10)
    2576: [('DEF: ^77777720^000000 DEFM: ^7777770^000000',
            'DEF: ^77777710^000000 DEFM: ^7777770^000000')],
    # Boina Charmosa: o LATAM e de um episodio em que ela tem DEF 5; o
    # db/re de onde copiamos tem 3. Vale o do servidor.
    5468: [('DEF: ^7777775^000000', 'DEF: ^7777773^000000')],
    # Amplificador de Som: o efeito foi inteiramente reescrito, porque o
    # original usa Ruido Estridente (skill de 3a classe) e conjuracao
    # variavel (conceito de renewal)
    2899: [('^0000ffConjuração variável -50%.^000000',
            '^0000ffPós-conjuração de [Tiro Preciso] -0,5s.^000000'),
           ('^0000ffDano de [Ruído Estridente] +150%.^000000', None),
           ('^0000ffCusto de SP de [Ruído Estridente] ^ff0000+60.^000000', None)],
}


def desescapar(s):
    """Bytes UTF-8 escapados em decimal -> texto."""
    s = RE_ESC.sub(lambda m: chr(int(m.group(1))), s)
    return s.encode('latin-1', 'replace').decode('utf-8', 'replace')


def campo(bloco, nome):
    m = re.search(r'(?<!un)' + nome + r'\s*=\s*' + RE_STR, bloco) if not nome.startswith('un') \
        else re.search(nome + r'\s*=\s*' + RE_STR, bloco)
    return desescapar(m.group(1)) if m else ''


def lista(bloco, nome):
    lookbehind = '' if nome.startswith('un') else '(?<!un)'
    m = re.search(lookbehind + nome + r'\s*=\s*\{(.*?)\n\s*\}', bloco, re.S)
    if not m:
        return []
    return [desescapar(x) for x in re.findall(RE_STR, m.group(1))]


def numero(bloco, nome, padrao=0):
    m = re.search(nome + r'\s*=\s*(-?\d+)', bloco)
    return int(m.group(1)) if m else padrao


def aplicar_ajustes(oid, linhas):
    """Aplica AJUSTES[oid]. 'para' None remove a linha. Avisa o que nao casou."""
    trocas = AJUSTES.get(oid)
    if not trocas:
        return linhas, []
    pendentes = {de: para for de, para in trocas}
    saida = []
    for l in linhas:
        if l in pendentes:
            para = pendentes.pop(l)
            if para is not None:
                saida.append(para)
        else:
            saida.append(l)
    return saida, list(pendentes)


RE_ID = r'(?m)^  - Id: %d\s*$'


def eh_traje(oid):
    """O item ocupa slot de traje? Descobre olhando o Locations no db.

    Ate 12/ago/2026 este campo saia "false" fixo, o que marcava traje como
    equipamento comum no cliente - os tres primeiros visuais entraram errados
    assim. Com uma leva de mais de mil visuais pela frente, o campo passa a ser
    derivado do db em vez de chutado.
    """
    for rel in ('db/ragnabeat_items.yml', 'db/ragnabeat_visuais.yml',
                'db/pre-re/item_db_equip.yml', 'db/re/item_db_equip.yml'):
        arq = REPO / rel
        if not arq.exists():
            continue
        txt = arq.read_bytes().decode('latin-1')
        m = re.search(RE_ID % oid, txt)
        if not m:
            continue
        # o bloco vai ate o proximo "  - Id:"
        fim = txt.find('\n  - Id: ', m.end())
        bloco = txt[m.start():fim if fim > 0 else len(txt)]
        return 'Costume_' in bloco
    return False


def montar(oid, bloco):
    """Devolve a entrada pronta, em bytes, no formato do itemInfo_C."""
    def cp(s):
        return s.encode('cp1252', 'replace')

    def kr(s):
        # o cliente procura o sprite por estes bytes; cp949 e obrigatorio
        return s.encode('cp949', 'replace')

    def bloco_desc(itens):
        if not itens:
            itens = ['']
        corpo = (',' + chr(10)).join(b'\t\t\t"'.decode() + i + '"' for i in itens)
        return corpo

    nome_i = campo(bloco, 'identifiedDisplayName')
    nome_u = campo(bloco, 'unidentifiedDisplayName')
    res_i = campo(bloco, 'identifiedResourceName')
    res_u = campo(bloco, 'unidentifiedResourceName')
    desc_i, faltou_i = aplicar_ajustes(oid, lista(bloco, 'identifiedDescriptionName'))
    desc_u, faltou_u = aplicar_ajustes(oid, lista(bloco, 'unidentifiedDescriptionName'))
    for de in set(faltou_i) & set(faltou_u):
        print('  AVISO %d: o ajuste %r nao casou com nenhuma linha' % (oid, de[:50]))

    out = bytearray()
    out += b'\t[%d] = {\n' % oid
    out += b'\t\tunidentifiedDisplayName = "' + cp(nome_u) + b'",\n'
    out += b'\t\tunidentifiedResourceName = "' + kr(res_u) + b'",\n'
    out += b'\t\tunidentifiedDescriptionName = {\n'
    out += cp(bloco_desc(desc_u)) + b'\n'
    out += b'\t\t},\n'
    out += b'\t\tidentifiedDisplayName = "' + cp(nome_i) + b'",\n'
    out += b'\t\tidentifiedResourceName = "' + kr(res_i) + b'",\n'
    out += b'\t\tidentifiedDescriptionName = {\n'
    out += cp(bloco_desc(desc_i)) + b'\n'
    out += b'\t\t},\n'
    out += b'\t\tslotCount = %d,\n' % numero(bloco, 'slotCount')
    out += b'\t\tClassNum = %d,\n' % numero(bloco, 'ClassNum')
    out += b'\t\tcostume = ' + (b'true' if eh_traje(oid) else b'false') + b'\n'
    out += b'\t},\n'
    return bytes(out), nome_i


def main():
    seco = '--dry' in sys.argv
    ids = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if not ids:
        raise SystemExit(__doc__)

    if not LATAM.exists():
        raise SystemExit('nao achei %s' % LATAM)
    if not ALVO.exists():
        raise SystemExit('nao achei %s' % ALVO)

    atual = ALVO.read_bytes()
    ja_tem = set(int(x) for x in re.findall(rb'\[(\d+)\]\s*=\s*\{', atual))
    print('itemInfo_C.lua: %d itens hoje' % len(ja_tem))

    fonte = LATAM.read_bytes().decode('cp1252', 'replace')
    blocos = {}
    for m in RE_BLOCO_LATAM.finditer(fonte):
        oid = int(m.group(1))
        if oid in ids:
            blocos[oid] = m.group(2)

    novas = bytearray()
    add = 0
    for oid in ids:
        if oid in ja_tem:
            print('  %-7d ja estava, pulado' % oid)
            continue
        if oid not in blocos:
            print('  %-7d NAO EXISTE no LATAM - entraria sem nome, pulado' % oid)
            continue
        entrada, nome = montar(oid, blocos[oid])
        novas += entrada
        add += 1
        print('  %-7d + %s' % (oid, ascii(nome)[1:-1]))

    if not add:
        print('nada a fazer')
        return 0
    if seco:
        print()
        print('--- DRY RUN, nada gravado. Entradas: ---')
        print(bytes(novas).decode('cp1252', 'replace'))
        return 0

    # o arquivo termina com "\t},\n}\n" - injeta antes do fecho da tabela
    fim = atual.rfind(b'}')
    if fim < 0:
        raise SystemExit('nao achei o fecho da tabela')
    novo = atual[:fim] + bytes(novas) + atual[fim:]

    ALVO.with_suffix('.lua.bak').write_bytes(atual)
    ALVO.write_bytes(novo)
    total = len(ja_tem) + add
    print()
    print('gravado: %s' % ALVO)
    print('%d itens agora (%d novos). Backup em %s' % (total, add, ALVO.name + '.bak'))
    print('ATUALIZE ITENS_ESPERADOS em docs/cliente/build.py para %d' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
