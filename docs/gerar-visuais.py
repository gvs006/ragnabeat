# -*- coding: utf-8 -*-
"""
Cruza os itens VISUAIS (traje) do renewal com o que o nosso cliente e o nosso
servidor conseguem usar, e gera a lista de validacao + o db.

    python docs/gerar-visuais.py --dry      so relata
    python docs/gerar-visuais.py            gera
    python docs/gerar-visuais.py --kro      inclui tambem os kRO-only

O PROBLEMA
db/re tem 3.220 trajes. O servidor tem 9. Trazer um por vez, como foi feito com
o Amplificador de Som, nao escala. Mas nem todo traje PODE entrar: tres camadas
precisam existir ao mesmo tempo, e a falta de qualquer uma quebra de um jeito
diferente.

    servidor   entrada no db          sem isso: o item nao existe
    cliente    nome/descricao PT-BR   sem isso: nome coreano no tooltip
    GRF        sprite VESTIDO         sem isso: o traje nao aparece no corpo

SAO DUAS CHECAGENS DE SPRITE, nao uma:

    chao     data/sprite/<item>/<res>.spr
             E o que o cliente carrega ao passar o mouse no inventario. Foi a
             falta DELE que abriu caixa de erro no caso 5376.

    vestido  o que aparece no corpo, e o lugar muda com o slot:
               capa    data/sprite/<robe>/<res>/<sexo>/...  pasta por item
               cabeca  data/sprite/<acessorio>/<sexo>/<sexo>_<res>.spr

             A pasta da capa e o identifiedResourceName, NAO o AegisName - o
             AegisName do traje quase sempre ganha um "C_" que a pasta nao tem.

Faltando o de chao o cliente quebra; faltando o vestido o traje nao aparece.
Os dois sao obrigatorios para o veredito PRONTO.

O TRAJE DE EFEITO e a excecao a tudo isso. Ele nao tem View e nao veste sprite
nenhum: o bloco no db/re traz hateffect(HAT_EF_*), e quem desenha e o cliente,
a partir de data/texture/effect/. Para ele so o sprite de chao importa. Sao 50
no db/re - entre eles a Aura Astrologica, o Circulo de Conjuracao e as auras
160LV - e cobrar View deles reprovava todos.

Este script confere as camadas que se aplicam a cada tipo e classifica cada
item num veredito. So o que for PRONTO entra no db.

VEREDITOS
    PRONTO           as camadas que se aplicam estao ok - entra
    JA TEM           ja esta em db/pre-re, nos nossos arquivos ou no itemInfo
    SEM VIEW         sem View: e sem hateffect; nao veste em ninguem
    SEM SPRITE       o GRF do build nao tem o sprite; quebraria o cliente
    SEM TEXTO PTBR   nao esta no dump LATAM (kRO-only). Entra so com --kro
    SEM EFEITO       traje de efeito cujo hat effect este cliente nao conhece
    SEM ARTE DE EFEITO  o cliente conhece o numero do efeito mas nao tem o .str
                     da animacao. Equipa e nao aparece nada - ver indice_grf()
    EFEITO DESALINHADO  o indice do efeito difere entre rAthena e cliente;
                     entraria mostrando OUTRO efeito. Ver limite_alinhado()

SAIDAS
    docs/_visuais.tsv            a lista, para abrir no Excel e validar
    db/ragnabeat_visuais.yml     so os PRONTO
    db/import/item_db.yml        ganha o import no rodape, sem perder o que ja
                                 estiver la
    npc/custom/testar_visuais.txt  NPC so-GM que veste um por um, para a
                                 validacao de olho que a planilha nao cobre
"""
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
LATAM = CLIENTE / 'DEVTOOLS/PTBR/iteminfo_ptBR.lua'
ITEMINFO = CLIENTE / 'SystemEN/itemInfo_C.lua'
GRF_BUILD = CLIENTE / 'data.grf'

DB_RE = REPO / 'db/re/item_db_equip.yml'
DB_PRE = REPO / 'db/pre-re/item_db_equip.yml'
NOSSOS = (REPO / 'db/ragnabeat_items.yml',)

SAIDA_TSV = REPO / 'docs/_visuais.tsv'
SAIDA_DB = REPO / 'db/ragnabeat_visuais.yml'
SAIDA_IMPORT = REPO / 'db/import/item_db.yml'
SAIDA_NPC = REPO / 'npc/custom/testar_visuais.txt'

BS = chr(92)
PREFIXO_NOME = '[Visual] '
ITEM_NAME_LENGTH = 49          # limite do rAthena, menos o terminador

SLOTS = {
    'Costume_Head_Top': 'topo',
    'Costume_Head_Mid': 'meio',
    'Costume_Head_Low': 'baixo',
    'Costume_Garment': 'capa',
}

NPC_MODELO = """//===== rAthena Script =======================================
//= Testador de Visuais - SO GM
//===== Descricao: ===========================================
//= GERADO por docs/gerar-visuais.py. NAO EDITE A MAO.
//=
//= A planilha docs/_visuais.tsv diz se o traje PODE entrar
//= (db + texto + sprite). So o olho diz se ficou bom - e para
//= isso que este NPC existe: pagina a lista, entrega o item e
//= veste na hora.
//=
//= Sao %(total)d visuais, os de veredito PRONTO.
//=
//= Fica no ar so enquanto a validacao estiver rolando. Depois
//= e so comentar a linha em npc/scripts_custom.conf.
//============================================================

prontera,144,187,4\tscript\tTestador de Visuais\t123,{
\tif (getgroupid() < 99) {
\t\tmes "[Testador de Visuais]";
\t\tmes "Isto e ferramenta de administracao.";
\t\tclose;
\t}
\t.@por_pagina = 10;
\t.@total = getarraysize(.Ids);

L_Pagina:
\t.@ini = @visual_pag * .@por_pagina;
\tif (.@ini >= .@total) {
\t\t@visual_pag = 0;
\t\t.@ini = 0;
\t}
\tmes "[Testador de Visuais]";
\tmes "Pagina ^0000FF" + (@visual_pag + 1) + "^000000 de ^0000FF"
\t\t+ ((.@total - 1) / .@por_pagina + 1) + "^000000  ("
\t\t+ .@total + " visuais)";
\tmes " ";

\t.@menu$ = "";
\t.@n = 0;
\tfor (.@i = .@ini; .@i < .@ini + .@por_pagina && .@i < .@total; .@i++) {
\t\tmes "  " + (.@i + 1) + ". " + mesitemlink(.Ids[.@i]);
\t\t.@menu$ += getitemname(.Ids[.@i]) + ":";
\t\t.@lista[.@n] = .Ids[.@i];
\t\t.@n++;
\t}
\tnext;

\t.@sel = select(.@menu$ + "^777777Proxima pagina^000000:"
\t\t+ "^777777Pagina anterior^000000:"
\t\t+ "^777777Ir para a pagina...^000000:Sair") - 1;

\tif (.@sel == .@n) {\t\t\t// proxima
\t\t@visual_pag++;
\t\tgoto L_Pagina;
\t}
\tif (.@sel == .@n + 1) {\t\t// anterior
\t\tif (@visual_pag > 0)
\t\t\t@visual_pag--;
\t\tgoto L_Pagina;
\t}
\tif (.@sel == .@n + 2) {\t\t// ir para
\t\tmes "[Testador de Visuais]";
\t\tmes "Qual pagina?";
\t\tinput .@p, 1, ((.@total - 1) / .@por_pagina + 1);
\t\t@visual_pag = .@p - 1;
\t\tgoto L_Pagina;
\t}
\tif (.@sel < 0 || .@sel >= .@n) {
\t\tclose;
\t}

\t.@id = .@lista[.@sel];
\tif (countitem(.@id) < 1)
\t\tgetitem .@id, 1;
\tequip .@id;
\tmes "[Testador de Visuais]";
\tmes "Vestido: " + mesitemlink(.@id) + "  (ID " + .@id + ")";
\tmes "Se ficou errado, anote o ID na coluna veredito do";
\tmes "docs/_visuais.tsv.";
\tnext;
\tgoto L_Pagina;

OnInit:
%(arrays)s
\tend;
}
"""


RE_ESC = re.compile(re.escape(BS) + r'(\d{1,3})')


def desescapar(s):
    s = RE_ESC.sub(lambda m: chr(int(m.group(1))), s)
    return s.encode('latin-1', 'replace').decode('utf-8', 'replace')


def blocos_item(caminho):
    """Id -> texto do bloco, para um item_db*.yml."""
    t = caminho.read_bytes().decode('latin-1')
    fora = {}
    for b in re.split(r'(?m)^(?=  - Id: )', t):
        m = re.match(r'  - Id: (\d+)\s*$', b.split('\n')[0])
        if m:
            fora[int(m.group(1))] = b.rstrip('\n')
    return fora


def indice_grf():
    """Devolve (nomes, pastas_de_capa, efeitos) do GRF, tudo minusculo.

    Montado UMA vez. O checar-sprite.py varre a lista inteira por item
    (O(n*m)); com 3 mil itens isso nao termina. Aqui a consulta e O(1).

    pastas_de_capa: os nomes de subpasta sob <robe>/. ATENCAO: a pasta e o
    identifiedResourceName do LATAM, NAO o AegisName. Sao quase sempre iguais,
    mas o traje costuma ganhar um prefixo "C_" no AegisName que a pasta nao
    tem - foi por isso que 19 capas boas (Thanatos, Asas de Lucifer, Asas de
    Raguel...) sairam como SEM SPRITE ate 03/set/2026.

    efeitos: nome do hat effect -> indice, lido do hateffectids.lub de dentro
    do GRF. Traje de efeito nao tem View nem sprite vestido; ver e_hat_effects.
    """
    if not GRF_BUILD.exists():
        print('AVISO: %s nao existe - checagem de sprite pulada' % GRF_BUILD)
        return None, None, None, None, None, None
    spec = importlib.util.spec_from_file_location(
        'grf', REPO / 'docs/cliente/grf_listar.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    arquivos, _ = mod.ler_tabela(GRF_BUILD)
    nomes = set(n.decode('latin-1').lower() for n, *_ in arquivos)

    # A pasta data/ solta VENCE o GRF - e o patch DataFolderFirst. Sem contar
    # com ela, todo sprite trazido pelo importar-sprites-latam.py continuaria
    # sendo julgado ausente, e o item ficaria de fora do db mesmo com o arquivo
    # ja instalado no cliente.
    pasta = CLIENTE / 'data'
    if pasta.is_dir():
        antes = len(nomes)
        for p in pasta.rglob('*'):
            if p.is_file():
                rel = p.relative_to(pasta.parent)
                nomes.add(str(rel).replace('/', BS).lower())
        print('data/ solta: %d arquivos (%d novos sobre o GRF)'
              % (sum(1 for _ in pasta.rglob('*')), len(nomes) - antes))

    pref = ('data' + BS + 'sprite' + BS + cru('로브') + BS)
    capas = set()
    for n in nomes:
        if n.startswith(pref):
            capas.add(n[len(pref):].split(BS)[0])

    # hateffectinfo.lub: efeito -> arquivo .str da animacao. Ter o NUMERO do
    # efeito nao basta - sem a arte o item equipa e nao aparece nada. Foi assim
    # que as sete auras 160LV e o Holograma Futurista entraram na 0.0.11
    # quebrados: os numeros batiam com o enum do rAthena, e o cliente
    # simplesmente nao tem animacao para eles. Nem o GRF do LATAM tem.
    arte = {}
    alvo_info = ('data' + BS + 'luafiles514' + BS + 'lua files' + BS
                 + 'hateffectinfo' + BS + 'hateffectinfo.lub')
    for e in arquivos:
        if e[0].decode('latin-1').lower() == alvo_info:
            bruto = mod.ler_arquivo(GRF_BUILD, e)
            atual = None
            pref_str = 'data' + BS + 'texture' + BS + 'effect' + BS
            for s in re.findall(rb'[ -~]{3,}', bruto):
                s = s.decode('latin-1')
                if s.upper().startswith('HAT_EF'):
                    atual = s.upper()
                elif atual and s.lower().endswith('.str'):
                    arte.setdefault(
                        atual, (pref_str + s.replace('/', BS)).lower())
            break

    # SPRITE DE CHAPEU: o cliente NAO usa o resourceName.
    #
    # Ele pega o View do item, procura em accessoryid.lub qual ACCESSORY_* tem
    # aquele numero, e usa accname.lub para achar o NOME DO SPRITE. Os dois
    # nomes coincidem na maioria dos itens - por isso a checagem por
    # resourceName passava por boa - mas quando divergem o traje equipa e nao
    # aparece nada. Foram 28 assim na 0.0.11.
    #
    # As tabelas que valem sao as de datainfo/ (2.670 entradas). Existe uma
    # copia em luafiles514/ com pouco mais da metade; usar a errada reprova
    # 564 itens bons.
    acc_view, acc_nome = {}, {}
    base_di = ('data' + BS + 'luafiles514' + BS + 'lua files' + BS
               + 'datainfo' + BS)
    spec2 = importlib.util.spec_from_file_location(
        'lub', REPO / 'docs/cliente/lub_constantes.py')
    lub = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(lub)
    import tempfile

    def _pares(caminho_grf, tipo):
        # A pasta data/ solta VENCE o GRF (DataFolderFirst), e e la que o
        # importar-acessorios-latam.py deixa a tabela nova. Ler so do GRF fazia
        # o gerador julgar por uma tabela que o cliente nem usa mais.
        solto = pasta / caminho_grf[len('data' + BS):].replace(BS, '/')
        if solto.is_file():
            with tempfile.NamedTemporaryFile(suffix='.lub', delete=False) as f:
                f.write(solto.read_bytes())
                tmp = f.name
            fora = {}
            try:
                for c in lub.constantes(tmp):
                    for a, b in zip(c, c[1:]):
                        if (isinstance(a, str) and a.startswith('ACCESSORY_')
                                and isinstance(b, tipo)):
                            fora.setdefault(a, b)
            finally:
                Path(tmp).unlink(missing_ok=True)
            return fora
        for e in arquivos:
            if e[0].decode('latin-1').lower() != caminho_grf:
                continue
            with tempfile.NamedTemporaryFile(suffix='.lub', delete=False) as f:
                f.write(mod.ler_arquivo(GRF_BUILD, e))
                tmp = f.name
            fora = {}
            try:
                for c in lub.constantes(tmp):
                    for a, b in zip(c, c[1:]):
                        if (isinstance(a, str) and a.startswith('ACCESSORY_')
                                and isinstance(b, tipo)):
                            fora.setdefault(a, b)
            finally:
                Path(tmp).unlink(missing_ok=True)
            return fora
        return {}

    for chave, valor in _pares(base_di + 'accessoryid.lub', float).items():
        acc_view[int(valor)] = chave
    acc_nome = _pares(base_di + 'accname.lub', str)

    efeitos = []
    alvo = ('data' + BS + 'luafiles514' + BS + 'lua files' + BS
            + 'hateffectinfo' + BS + 'hateffectids.lub')
    for e in arquivos:
        if e[0].decode('latin-1').lower() == alvo:
            bruto = mod.ler_arquivo(GRF_BUILD, e)
            # .lub e bytecode Lua 5.1; nao ha parser aqui. As constantes de
            # string saem na ordem de declaracao, que e a ordem do enum - e
            # so isso que precisamos. Fica LISTA, nao dict: o cliente tem dois
            # efeitos diferentes que so diferem na caixa (HAT_EF_Black_Thunder
            # no 158 e HAT_EF_black_thunder no 218), e um dict os fundiria.
            efeitos = [s.decode('ascii') for s in
                       re.findall(rb'[ -~]{4,}', bruto)
                       if s.decode('ascii').upper().startswith('HAT_EF')]
            break
    return nomes, capas, efeitos, arte, acc_view, acc_nome


def efeitos_servidor():
    """Nome do hat effect -> indice, na ordem do enum e_hat_effects."""
    t = (REPO / 'src/map/script.hpp').read_text(encoding='latin-1')
    m = re.search(r'HAT_EF_MIN = 0,(.*?)\n\};', t, re.S)
    if not m:
        return {}
    fora, i = {}, 0
    for linha in m.group(1).split('\n'):
        linha = linha.split('//')[0].strip().rstrip(',')
        if linha.startswith('HAT_EF'):
            fora[linha.split('=')[0].strip().upper()] = i
            i += 1
    return fora


def limite_alinhado(srv, cli):
    """Ate que indice servidor e cliente concordam sobre qual efeito e qual.

    O rAthena e o nosso cliente numeram os hat effects pela POSICAO no enum -
    nao ha id no protocolo, so o indice. Basta uma constante a mais de um lado
    para todo o resto deslizar e o jogador ver outro efeito. So entra efeito
    abaixo deste limite.

    Hoje as duas listas batem inteiras: o cliente conhece 248 e o rAthena 266,
    entao o limite e 248 - o resto e novo demais para este cliente. A unica
    diferenca de grafia e o HAT_EF_BLACK_THUNDER_ do rAthena, com _ no fim so
    para nao colidir com o HAT_EF_BLACK_THUNDER que ja existe (em C nao daria
    para ter os dois); e o mesmo efeito, na mesma posicao.
    """
    if not srv or not cli:
        return 0
    por_nome = {}
    for nome, i in srv.items():
        por_nome[i] = nome
    for i, nome in enumerate(cli):
        esperado = por_nome.get(i, '')
        if esperado.rstrip('_') != nome.upper().rstrip('_'):
            return i
    return len(cli)


def cru(s):
    """Coreano -> os bytes exatos que estao dentro do GRF."""
    return s.encode('cp949', 'replace').decode('latin-1').lower()


def dados_latam():
    """Id -> (nome PT-BR, identifiedResourceName)."""
    txt = LATAM.read_bytes().decode('cp1252', 'replace')
    fora = {}
    for m in re.finditer(r'\[(\d+)\]\s*=\s*\{(.*?)\n  \}', txt, re.S):
        bloco = m.group(2)
        n = re.search(r'(?<!un)identifiedDisplayName\s*=\s*"([^"]*)"', bloco)
        r = re.search(r'(?<!un)identifiedResourceName\s*=\s*"([^"]*)"', bloco)
        if n:
            fora[int(m.group(1))] = (desescapar(n.group(1)),
                                     desescapar(r.group(1)) if r else '')
    return fora


def main():
    seco = '--dry' in sys.argv
    com_kro = '--kro' in sys.argv

    re_itens = blocos_item(DB_RE)
    pre_itens = blocos_item(DB_PRE)
    ja_nossos = set()
    for arq in NOSSOS:
        if arq.exists():
            ja_nossos |= set(blocos_item(arq))
    # SO informativo. "Esta no itemInfo do cliente" NAO e "esta registrado no
    # servidor" - confundir os dois zerou a saida na segunda rodada, porque
    # todo item que acabara de ser cadastrado no cliente virava JA TEM.
    no_cliente = set()
    if ITEMINFO.exists():
        no_cliente = set(int(x) for x in re.findall(
            rb'\[(\d+)\]\s*=\s*\{', ITEMINFO.read_bytes()))

    latam = dados_latam()
    (nomes_grf, capas_grf, efeitos_cli, arte_efeito,
     acc_view, acc_nome) = indice_grf()
    efeitos_srv = efeitos_servidor()
    lim_efeito = limite_alinhado(efeitos_srv, efeitos_cli)
    if efeitos_cli:
        print('hat effects: cliente %d, rAthena %d, alinhados ate o indice %d'
              % (len(efeitos_cli), len(efeitos_srv), lim_efeito - 1))
    dir_acc = 'data' + BS + 'sprite' + BS + cru('악세사리') + BS
    dir_item = 'data' + BS + 'sprite' + BS + cru('아이템') + BS

    print('db/re: %d itens | db/pre-re: %d | LATAM: %d | ja nossos: %d'
          % (len(re_itens), len(pre_itens), len(latam), len(ja_nossos)))

    linhas, prontos = [], []
    contagem = {}
    for oid in sorted(re_itens):
        bloco = re_itens[oid]
        slots = [v for k, v in SLOTS.items()
                 if re.search(r'(?m)^      %s: true\s*$' % k, bloco)]
        if not slots:
            continue

        m = re.search(r'(?m)^    AegisName: (\S+)\s*$', bloco)
        aegis = m.group(1) if m else '?'
        m = re.search(r'(?m)^    View: (\d+)\s*$', bloco)
        view = int(m.group(1)) if m else None
        nome_pt, res = latam.get(oid, ('', ''))

        # Traje de EFEITO: nao veste sprite nenhum, dispara um hat effect. Nao
        # ter View e o normal dele, nao defeito - cobrar View aqui reprovava 50
        # itens bons (Aura Astrologica, Circulo de Conjuracao, as auras 160LV).
        # O indice vem do enum do SERVIDOR, nao de procurar o nome na lista do
        # cliente: e o servidor que manda o numero no pacote. O cliente so
        # precisa ter aquele indice, e e isso que lim_efeito responde.
        m = re.search(r'hateffect\((\w+)', bloco)
        efeito = m.group(1).upper() if m else None
        i_efeito = efeitos_srv.get(efeito) if efeito else None

        tem_chao = tem_vestido = None
        if nomes_grf is not None and res:
            tem_chao = (dir_item + cru(res) + '.spr') in nomes_grf
            if efeito and view is None:
                # so o icone de inventario importa; o resto e o efeito
                tem_vestido = i_efeito is not None and i_efeito < lim_efeito
            elif 'capa' in slots:
                # a pasta e o resourceName, nao o AegisName - ver indice_grf()
                tem_vestido = res.lower() in capas_grf
            else:
                # Pelo caminho que o CLIENTE usa: View -> accessoryid ->
                # accname -> nome do sprite. Ver o bloco em indice_grf().
                chave = acc_view.get(view) if view else None
                spr = acc_nome.get(chave) if chave else None
                if spr:
                    # basta um dos sexos; alguns trajes so tem um
                    tem_vestido = any(
                        (dir_acc + cru(sx) + BS + cru(sx) + spr.lower() + '.spr')
                        in nomes_grf for sx in ('남', '여'))
                else:
                    tem_vestido = False
        tem_sprite = (None if tem_chao is None
                      else (tem_chao and tem_vestido))

        if oid in pre_itens or oid in ja_nossos:
            veredito = 'JA TEM'
        elif efeito and view is None:
            if not nome_pt:
                veredito = 'SEM TEXTO PTBR'
            elif i_efeito is None:
                veredito = 'SEM EFEITO'
            elif i_efeito >= lim_efeito:
                veredito = 'EFEITO DESALINHADO'
            elif nomes_grf is not None and (
                    efeito not in arte_efeito
                    or arte_efeito[efeito] not in nomes_grf):
                # o cliente conhece o numero mas nao tem a animacao
                veredito = 'SEM ARTE DE EFEITO'
            elif not tem_chao:
                veredito = 'SEM SPRITE'
            else:
                veredito = 'PRONTO'
        elif view is None:
            veredito = 'SEM VIEW'
        elif not nome_pt:
            veredito = 'SEM TEXTO PTBR'
        elif tem_sprite is False:
            veredito = 'SEM SPRITE'
        else:
            veredito = 'PRONTO'

        contagem[veredito] = contagem.get(veredito, 0) + 1
        # o LATAM ja marca traje com "[Visual] " no nome; so acrescenta em
        # quem nao tiver, senao sai "[Visual] [Visual] Penas Encantadas"
        if nome_pt:
            nome_final = (nome_pt if nome_pt.startswith(PREFIXO_NOME.strip())
                          else PREFIXO_NOME + nome_pt)[:ITEM_NAME_LENGTH]
        else:
            nome_final = ''
        # A coluna view mostra 'ef<N>' no traje de efeito, e a coluna vestido
        # vira 'efeito' - as duas nao se aplicam a ele, e deixar em branco
        # confundiria com dado faltando.
        col_view = ('ef%d' % i_efeito if (efeito and view is None
                                          and i_efeito is not None)
                    else str(view or ''))
        col_vest = ('efeito' if (efeito and view is None and tem_vestido)
                    else {True: 'ok', False: 'falta', None: '?'}[tem_vestido])
        linhas.append('\t'.join([
            str(oid), aegis, '+'.join(slots), col_view, nome_final,
            'sim' if nome_pt else 'nao',
            'sim' if oid in no_cliente else 'nao',
            {True: 'ok', False: 'falta', None: '?'}[tem_chao],
            col_vest, veredito]))
        if veredito == 'PRONTO' or (com_kro and veredito == 'SEM TEXTO PTBR'
                                    and view is not None and tem_sprite is not False):
            prontos.append((oid, aegis, slots, view,
                            nome_final or (PREFIXO_NOME + aegis),
                            efeito if view is None else None))

    print()
    for v in sorted(contagem, key=lambda x: -contagem[x]):
        print('  %-16s %d' % (v, contagem[v]))
    print()
    print('entrariam no db: %d' % len(prontos))

    if seco:
        print()
        print('>>> DRY RUN - nada gravado. Amostra:')
        for l in linhas[:8]:
            print('   ' + l.replace('\t', ' | '))
        return 0

    cab_tsv = ('# Visuais - GERADO por docs/gerar-visuais.py\n'
               '# id\taegis\tslot\tview\tnome_ptbr\tlatam\tno_cliente\tchao\tvestido\tveredito\n')
    SAIDA_TSV.write_bytes((cab_tsv + '\n'.join(linhas) + '\n')
                          .encode('cp1252', 'replace'))

    cab_db = '''# Visuais (trajes) do RagnaBeat - GERADO, NAO EDITE A MAO
#
# Fonte: docs/gerar-visuais.py. So entra item que passou nas tres camadas:
# existe em db/re, tem nome PT-BR no dump LATAM, e tem sprite no GRF do build.
# A lista completa, com o motivo de cada exclusao, esta em docs/_visuais.tsv.
#
# Traje nunca recebe bonus aleatorio - e regra do proprio rAthena.
#
# Encoding: cp1252, sem BOM. Ver docs/encoding.md.

Header:
  Type: ITEM_DB
  Version: 3

Body:
'''
    corpo = []
    for oid, aegis, slots, view, nome, efeito in prontos:
        corpo.append('  - Id: %d' % oid)
        corpo.append('    AegisName: %s' % aegis)
        corpo.append('    Name: "%s"' % nome.replace('"', "'"))
        corpo.append('    Type: Armor')
        if view is not None:
            corpo.append('    View: %d' % view)
        corpo.append('    Locations:')
        for k, v in SLOTS.items():
            if v in slots:
                corpo.append('      %s: true' % k)
        corpo.append('    ArmorLevel: 1')
        # Traje de efeito: sem View, o visual sai do hateffect. Liga ao vestir
        # e desliga ao tirar - sem o UnEquipScript o efeito fica preso no
        # personagem ate a proxima troca de mapa.
        if efeito:
            corpo.append('    Script: |')
            corpo.append('      hateffect(%s,true);' % efeito)
            corpo.append('    UnEquipScript: |')
            corpo.append('      hateffect(%s,false);' % efeito)
    SAIDA_DB.write_bytes((cab_db + '\n'.join(corpo) + '\n')
                         .encode('cp1252', 'replace'))

    # o rodape do item_db de import precisa puxar o nosso arquivo. O
    # gen-nomes-servidor.py preserva o bloco Footer inteiro, entao basta
    # acrescentar a linha uma vez.
    if SAIDA_IMPORT.exists():
        t = SAIDA_IMPORT.read_bytes().decode('cp1252')
        if 'ragnabeat_visuais.yml' not in t:
            if '\nFooter:' in t:
                t = t.rstrip('\n') + '\n  - Path: db/ragnabeat_visuais.yml\n'
            else:
                t = t.rstrip('\n') + ('\n\nFooter:\n  Imports:\n'
                                      '  - Path: db/ragnabeat_visuais.yml\n')
            SAIDA_IMPORT.write_bytes(t.encode('cp1252'))
            print('rodape de %s atualizado' % SAIDA_IMPORT.name)


    # --- NPC de teste, so-GM ---------------------------------------------
    # A planilha diz se o item PODE entrar; so o olho diz se ficou bom. Este
    # NPC pagina a lista e veste o traje na hora.
    ids = [str(o) for o, _a, _s, _v, _n, _e in prontos]
    linhas_arr = []
    for i in range(0, len(ids), 100):
        linhas_arr.append('	setarray .Ids[%d],%s;'
                          % (i, ','.join(ids[i:i + 100])))
    npc = NPC_MODELO % {'arrays': chr(10).join(linhas_arr),
                       'total': len(ids)}
    SAIDA_NPC.write_bytes(npc.encode('cp1252', 'replace'))

    print()
    for p in (SAIDA_TSV, SAIDA_DB, SAIDA_NPC):
        print('gravado: %-32s %d bytes' % (p.relative_to(REPO), p.stat().st_size))
    print()
    print('Proximo: python docs/cliente/add-item-ptbr.py <ids do TSV>')
    return 0


if __name__ == '__main__':
    sys.exit(main())
