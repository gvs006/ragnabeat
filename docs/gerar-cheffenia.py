# -*- coding: utf-8 -*-
"""Gera npc/custom/cheffenia.txt - a sala de MVP com entrada paga.

Por que isto e um gerador e nao um arquivo escrito a mao:

  1. O elenco de MVPs sai do proprio db/pre-re/mob_db.yml (campo Mvp: true).
     Ninguem precisa digitar 46 ids, e se o mob_db mudar basta rodar de novo.

  2. As ancoras de spawn precisam ser CONFERIDAS contra o map_cache. O mapa
     escolhido tem 44.916 celulas andaveis, mas so 24.388 estao ligadas a
     entrada: o resto sao bolsoes isolados. Um spawn "mapa,0,0" colocaria
     quase metade dos MVPs onde o jogador nunca chega. Aqui cada MVP recebe
     uma ancora sorteada dentro da regiao conectada, com a vizinhanca de
     +-RAIO celulas verificada uma por uma.

Para trocar de mapa: mude MAPA e ENTRADA e rode de novo. O script aborta se a
entrada nao for andavel ou se nao houver ancoras limpas suficientes.

    python docs/gerar-cheffenia.py

O arquivo sai em latin-1, que e o encoding dos outros NPCs custom (ver
npc/custom/rotd.txt) e o que o cliente sabe decodificar.
"""
import re
import struct
import zlib
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MAPA = 'ordeal_a02'
ENTRADA = (103, 156)               # onde o jogador chega
VOLTA = ('prontera', 155, 186)     # para onde o passe vencido devolve
PORTA = ('prontera', 154, 187)     # onde fica o Guarda
RAIO = 3                           # +- celulas na linha de spawn
DELAY1, DELAY2 = 1800000, 900000   # respawn: 30 min + ate 15 min de variacao

CUSTO = 1000000                    # zeny por passe
MINUTOS = 60                       # duracao do passe
NIVEL = 80                         # nivel base minimo
LOTACAO = 30                       # jogadores simultaneos

SAIDA = REPO / 'npc/custom/cheffenia.txt'
TAB = '\t'

# Mobs com Mvp: true que NAO sao conteudo de sala de MVP.
FORA = {
    1399: 'Baphomet de evento',
    1502: 'Poring de evento',
    1766: 'Angeling de evento',
    1767: 'Deviling de evento',
    1917: 'Morroc Ferido - tem linha de quest propria',
    1980: 'Kublin de evento',
    2022: 'Sombra de Nidhoggur - mob de instancia',
}


# ---------------------------------------------------------------------------
# leitura do map_cache
# ---------------------------------------------------------------------------
def ler_mapa(nome):
    """Devolve (celulas, largura, altura) de um mapa do db/map_cache.dat.

    Formato: int32 tamanho, int32 quantidade, e entao por mapa
    char[12] nome, int16 xs, int16 ys, int32 len, e len bytes deflatados.
    """
    d = (REPO / 'db/map_cache.dat').read_bytes()
    n, = struct.unpack_from('<i', d, 4)
    off = 8
    for _ in range(n):
        m = d[off:off + 12].split(b'\x00')[0].decode('latin-1')
        off += 12
        xs, ys = struct.unpack_from('<hh', d, off)
        off += 4
        ln, = struct.unpack_from('<i', d, off)
        off += 4
        if m == nome:
            return zlib.decompress(d[off:off + ln]), xs, ys
        off += ln
    raise SystemExit('mapa %s nao esta no map_cache' % nome)


def regiao_de(cel, xs, ys, origem):
    """Todas as celulas que o jogador alcanca a pe a partir de origem."""
    def anda(x, y):
        # tipo 0 = chao, tipo 3 = agua rasa; o resto nao se pisa
        return 0 <= x < xs and 0 <= y < ys and cel[y * xs + x] in (0, 3)

    if not anda(*origem):
        raise SystemExit('a entrada %d,%d nao e andavel em %s'
                         % (origem[0], origem[1], MAPA))
    vis = bytearray(xs * ys)
    vis[origem[1] * xs + origem[0]] = 1
    fila = deque([origem])
    dentro = set()
    while fila:
        x, y = fila.popleft()
        dentro.add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = x + dx, y + dy
            if anda(a, b) and not vis[b * xs + a]:
                vis[b * xs + a] = 1
                fila.append((a, b))
    total = sum(1 for x in range(xs) for y in range(ys) if anda(x, y))
    return dentro, total, anda


def ancoras(dentro, anda, quantas, raio):
    """Pontos bem espalhados cuja caixa +-raio nao vaza da regiao.

    "Nao vaza" = toda celula andavel dessa caixa tambem esta na regiao. Assim
    o sorteio que o servidor faz dentro do raio nunca cai num bolsao isolado.
    """
    limpos = sorted((x, y) for (x, y) in dentro
                    if all((x + a, y + b) in dentro
                           for a in range(-raio, raio + 1)
                           for b in range(-raio, raio + 1)
                           if anda(x + a, y + b)))
    if len(limpos) < quantas:
        raise SystemExit('so %d ancoras limpas para %d MVPs - diminua o RAIO'
                         % (len(limpos), quantas))
    # amostragem do ponto mais distante: espalha em vez de agrupar
    escolhidos = [limpos[len(limpos) // 2]]
    dist = [abs(p[0] - escolhidos[0][0]) + abs(p[1] - escolhidos[0][1])
            for p in limpos]
    while len(escolhidos) < quantas:
        i = max(range(len(limpos)), key=lambda k: dist[k])
        escolhidos.append(limpos[i])
        px, py = limpos[i]
        for k, (x, y) in enumerate(limpos):
            d = abs(x - px) + abs(y - py)
            if d < dist[k]:
                dist[k] = d
    return limpos, escolhidos


def lista_mvps():
    """(nivel, id, nome) de cada MVP do pre-renewal, menos os de evento."""
    txt = (REPO / 'db/pre-re/mob_db.yml').read_text(encoding='utf-8',
                                                    errors='replace')
    achados = []
    for bloco in re.split(r'\n(?=  - Id: )', txt):
        if not re.search(r'^\s*Mvp:\s*true', bloco, re.M):
            continue
        i = re.search(r'Id:\s*(\d+)', bloco)
        nm = re.search(r'Name:\s*(.+)', bloco)
        lv = re.search(r'Level:\s*(\d+)', bloco)
        if not (i and nm):
            continue
        mid = int(i.group(1))
        if mid in FORA:
            continue
        achados.append((int(lv.group(1)) if lv else 0, mid, nm.group(1).strip()))
    achados.sort()
    return achados


# ---------------------------------------------------------------------------
# o arquivo
# ---------------------------------------------------------------------------
CABECALHO = u'''\
//===== rAthena Script =======================================
//= Cheffenia - a sala dos MVPs
//===== Descricao: ===========================================
//= Mapa fechado onde so ha MVP. A entrada e paga e vale por
//= tempo; vencido o passe, o jogador volta para Prontera.
//=
//= GERADO POR docs/gerar-cheffenia.py - NAO EDITE A MAO.
//= Mexer aqui e perder a alteracao na proxima geracao. Mude o
//= gerador e rode de novo.
//=
//===== SOBRE O NOME =========================================
//= "Cheffenia" vem dos servidores custom brasileiros (bRO
//= Thor, RO Latam). La era um MAPA PROPRIO - cheffenia.gat -
//= distribuido junto com o cliente.
//=
//= Esse mapa NAO existe nas nossas GRFs. Foi conferido:
//= procurei cheffen/chefenia/bossnia nos 214.224 arquivos da
//= data.grf e nao ha nada. Trazer o mapa original exigiria
//= distribuir .gat/.gnd/.rsw pelo patcher, registrar em
//= db/map_index.txt e regerar o map_cache - projeto a parte.
//=
//= Entao a Cheffenia daqui e o CONTEUDO - sala so de MVP com
//= entrada paga - montado sobre um mapa oficial do kRO.
//=
//===== POR QUE %(mapa)s ==============================
//= Salao das Provacoes. Escolhido por medida, nao por gosto:
//=
//=   - %(and_reg)s celulas andaveis LIGADAS ENTRE SI. Da para
//=     cacar MVP sem virar moedor de carne.
//=   - arte completa no cliente: .rsw, .gnd e .gat estao na
//=     data.grf (conferido)
//=   - ZERO uso no servidor. Nenhum mob, nenhum NPC, nenhum
//=     warp, nenhuma mapflag apontam para ele. Nao tira
//=     conteudo de lugar nenhum.
//=
//===== POR QUE CADA MVP TEM SUA PROPRIA LINHA DE SPAWN ======
//= O jeito obvio seria "%(mapa)s,0,0" - nascer em qualquer
//= lugar do mapa. Aqui isso esta errado.
//=
//= O mapa tem %(and_tot)s celulas andaveis, mas so %(and_reg)s
//= estao ligadas a entrada. Os outros %(pct)d%% sao bolsoes
//= isolados, inalcancaveis a pe. Com spawn 0,0 quase metade
//= dos MVPs nasceria onde ninguem chega.
//=
//= Por isso cada MVP tem ancora propria, escolhida dentro da
//= regiao conectada e com a caixa de +-%(raio)d celulas conferida
//= uma a uma: o sorteio que o servidor faz dentro do raio nao
//= tem como cair fora da regiao.
//=
//= As ancoras sao espalhadas por amostragem do ponto mais
//= distante, entao os MVPs nao ficam empilhados num canto.
//=
//===== O PASSE ==============================================
//= cheffenia_ate e variavel de PERSONAGEM (permanente) e
//= guarda o unixtime em que o passe vence.
//=
//= Morreu? Voltou para o savepoint, mas o passe continua
//= valendo: o Guarda deixa reentrar de graca ate vencer. Isso
//= e de proposito - o custo e da SESSAO, nao da porta. Sem
//= isso, morrer para um MVP custaria %(custo)s zeny.
//=
//= Quem expulsa e o Relogio de Cheffenia, que varre o mapa a
//= cada 30 segundos. Varredura em vez de addtimer porque
//= timer de jogador morre em relog e em @reloadscript, e ai
//= o passe vencido nunca expiraria. A varredura nao esquece.
//============================================================

'''


def gerar():
    cel, xs, ys = ler_mapa(MAPA)
    dentro, total, anda = regiao_de(cel, xs, ys, ENTRADA)
    mvps = lista_mvps()
    limpos, pontos = ancoras(dentro, anda, len(mvps), RAIO)

    print('%s: %d andaveis, %d na regiao da entrada (%.1f%%)'
          % (MAPA, total, len(dentro), 100.0 * len(dentro) / total))
    print('%d ancoras limpas disponiveis, %d MVPs no elenco'
          % (len(limpos), len(mvps)))
    print('%d MVPs de evento ficaram de fora' % len(FORA))

    cab = CABECALHO % {
        'mapa': MAPA,
        'and_tot': '{:,}'.format(total).replace(',', '.'),
        'and_reg': '{:,}'.format(len(dentro)).replace(',', '.'),
        'pct': round(100.0 * (total - len(dentro)) / total),
        'raio': RAIO,
        'custo': '{:,}'.format(CUSTO).replace(',', '.'),
    }

    p = [cab]
    p.append(CORPO % {
        'porta': '%s,%d,%d' % PORTA,
        'mapa': MAPA,
        'ex': ENTRADA[0], 'ey': ENTRADA[1],
        'custo': CUSTO, 'minutos': MINUTOS,
        'nivel': NIVEL, 'lotacao': LOTACAO,
        'vmapa': VOLTA[0], 'vx': VOLTA[1], 'vy': VOLTA[2],
        'vigia': '%s,%d,%d' % (MAPA, ENTRADA[0] + 3, ENTRADA[1]),
    })

    # --- spawns ---
    p.append('\n//======================================================\n'
             '// Os MVPs\n'
             '//\n'
             '// Formato: <mapa>,<x>,<y>,<raio x>,<raio y> boss_monster\n'
             '//          --ja-- <id>,<qtd>,<respawn>,<variacao>\n'
             '//\n'
             '// --ja-- faz o servidor usar o nome do mob_db em vez de um\n'
             '// nome escrito aqui, entao os nomes em portugues de\n'
             '// db/import/mob_db.yml valem tambem aqui dentro.\n'
             '//\n'
             '// boss_monster (e nao monster) para o Espelho Convexo\n'
             '// enxergar. Numa sala de MVP isso e o ponto.\n'
             '//\n'
             '// Respawn: %d min + ate %d min de sorteio.\n'
             '//======================================================\n'
             % (DELAY1 // 60000, DELAY2 // 60000))

    faixa = None
    for (lv, mid, nome), (x, y) in zip(mvps, pontos):
        if lv // 10 * 10 != faixa:
            faixa = lv // 10 * 10
            p.append('\n// --- nivel %d+ ---' % faixa)
        p.append(TAB.join(['%s,%d,%d,%d,%d' % (MAPA, x, y, RAIO, RAIO),
                           'boss_monster', '--ja--',
                           '%d,1,%d,%d' % (mid, DELAY1, DELAY2)]))
    p.append('')

    # --- mapflags ---
    p.append(MAPFLAGS % {'mapa': MAPA})

    txt = '\n'.join(p)
    SAIDA.write_bytes(txt.encode('latin-1'))
    print('escrito: %s (%d linhas)' % (SAIDA, txt.count('\n') + 1))


CORPO = u'''
//======================================================
// O Guarda - a porta, em Prontera
//======================================================
%(porta)s,4\tscript\tGuarda de Cheffenia::CheffeniaPorta\t811,{
\t.@resta = cheffenia_ate - gettimetick(2);

\tmes "[Guarda de Cheffenia]";

\t// Passe ainda de pe: entra de novo sem pagar. Ver O PASSE
\t// no cabecalho - o custo e da sessao, nao da porta.
\tif (.@resta > 0) {
\t\tmes "Seu passe ainda vale ^0000FF" + (.@resta / 60 + 1) + " minuto(s)^000000.";
\t\tmes "Entre à vontade.";
\t\tnext;
\t\tif (select("Voltar para Cheffenia:Fico por aqui") == 2)
\t\t\tclose;
\t\tif (getmapusers(.mapa$) >= .lotacao) {
\t\t\tmes "[Guarda de Cheffenia]";
\t\t\tmes "O salão está lotado. Espere alguém sair.";
\t\t\tclose;
\t\t}
\t\tclose2;
\t\twarp .mapa$, .x, .y;
\t\tend;
\t}

\tmes "Atrás de mim fica ^FF0000Cheffenia^000000, o salão onde";
\tmes "os senhores de Midgard estão presos.";
\tmes "Só há MVP lá dentro. Mais nada.";
\tnext;
\tmes "[Guarda de Cheffenia]";
\tmes "A passagem custa ^FF0000" + callfunc("F_InsertComma", .custo) + " zeny^000000";
\tmes "e vale por ^0000FF" + .minutos + " minutos^000000.";
\tmes " ";
\tmes "Se você morrer lá dentro, o passe continua";
\tmes "valendo. Volte aqui que eu deixo entrar.";
\tnext;

\tswitch (select("Quero entrar:Quantos estão lá dentro?:Melhor não")) {
\tcase 1:
\t\tmes "[Guarda de Cheffenia]";
\t\tif (BaseLevel < .nivel) {
\t\t\tmes "Nível base ^FF0000" + .nivel + "^000000, no mínimo.";
\t\t\tmes "Você tem " + BaseLevel + ". Volte mais forte.";
\t\t\tclose;
\t\t}
\t\tif (getmapusers(.mapa$) >= .lotacao) {
\t\t\tmes "O salão está lotado - ^FF0000" + .lotacao + "^000000 lá dentro.";
\t\t\tmes "Espere alguém sair.";
\t\t\tclose;
\t\t}
\t\tif (Zeny < .custo) {
\t\t\tmes "Faltam ^FF0000" + callfunc("F_InsertComma", .custo - Zeny) + " zeny^000000.";
\t\t\tclose;
\t\t}
\t\tZeny -= .custo;
\t\tcheffenia_ate = gettimetick(2) + .minutos * 60;
\t\tmes "Que Odin tenha piedade.";
\t\tclose2;
\t\twarp .mapa$, .x, .y;
\t\tend;

\tcase 2:
\t\tmes "[Guarda de Cheffenia]";
\t\tmes "Há ^0000FF" + getmapusers(.mapa$) + "^000000 de " + .lotacao + " lá dentro agora.";
\t\tclose;

\tcase 3:
\t\tmes "[Guarda de Cheffenia]";
\t\tmes "Sensato.";
\t\tclose;
\t}

OnInit:
\t// ---- a configuracao inteira mora aqui ----
\t// O Vigia e o Relogio leem daqui por getvariableofnpc, entao
\t// mudar um valor neste bloco muda o sistema todo.
\t.mapa$ = "%(mapa)s";
\t.x = %(ex)d;
\t.y = %(ey)d;
\t.custo = %(custo)d;
\t.minutos = %(minutos)d;
\t.nivel = %(nivel)d;
\t.lotacao = %(lotacao)d;
\t.volta$ = "%(vmapa)s";
\t.volta_x = %(vx)d;
\t.volta_y = %(vy)d;

\twaitingroom "Cheffenia", 0;
\tend;
}

//======================================================
// O Vigia - a saida, dentro do salao
//======================================================
%(vigia)s,4\tscript\tVigia de Cheffenia::CheffeniaVigia\t778,{
\t.@resta = cheffenia_ate - gettimetick(2);

\tmes "[Vigia de Cheffenia]";
\tif (.@resta > 0)
\t\tmes "Restam ^0000FF" + (.@resta / 60 + 1) + " minuto(s)^000000 do seu passe.";
\telse
\t\tmes "Seu passe venceu. Sai andando ou eu te arrasto.";
\tnext;
\tif (select("Sair do salão:Ficar") == 2)
\t\tclose;
\tclose2;
\twarp getvariableofnpc(.volta$, "CheffeniaPorta"),
\t     getvariableofnpc(.volta_x, "CheffeniaPorta"),
\t     getvariableofnpc(.volta_y, "CheffeniaPorta");
\tend;

OnInit:
\twaitingroom "Saída de Cheffenia", 0;
\tend;
}

//======================================================
// O Relogio - expulsa quem esta com o passe vencido
//
// Varre o mapa a cada 30s em vez de dar addtimer no jogador
// na entrada. O motivo esta no cabecalho: timer de jogador
// morre em relog e em @reloadscript, e ai o passe vencido
// nunca expiraria. A varredura sobrevive aos dois.
//======================================================
-\tscript\tCheffeniaRelogio\t-1,{
OnInit:
\tinitnpctimer;
\tend;

OnTimer30000:
\t.@mapa$ = getvariableofnpc(.mapa$, "CheffeniaPorta");
\t.@volta$ = getvariableofnpc(.volta$, "CheffeniaPorta");
\t.@vx = getvariableofnpc(.volta_x, "CheffeniaPorta");
\t.@vy = getvariableofnpc(.volta_y, "CheffeniaPorta");
\t.@agora = gettimetick(2);

\t// getmapunits devolve os block ids; para jogador o block id
\t// E o account id, entao attachrid recebe ele direto.
\t.@n = getmapunits(BL_PC, .@mapa$, .@rid);
\tfor (.@i = 0; .@i < .@n; .@i++) {
\t\tif (!attachrid(.@rid[.@i]))
\t\t\tcontinue;
\t\t// GM entra para administrar, nao para farmar: nao expulsa.
\t\tif (getgroupid() < 99 && cheffenia_ate <= .@agora) {
\t\t\tdispbottom "Seu passe de Cheffenia venceu.";
\t\t\twarp .@volta$, .@vx, .@vy;
\t\t}
\t\tdetachrid;
\t}
\tsetnpctimer 0;
\tend;
}
'''

MAPFLAGS = u'''
//======================================================
// Mapflags
//
// O mapa nao tinha NENHUMA mapflag antes disto - todas as
// linhas abaixo sao nossas.
//
// nomemo / noreturn / noteleport fecham as tres saidas de
//   graca: /memo, Asa de Borboleta e Asa de Mosca. Quem
//   pagou pelo tempo sai pelo Vigia ou espera o Relogio.
//
// monster_noteleport e o importante: MVP se teleporta o
//   tempo todo. Sem isto o jogador paga o passe e passa a
//   sessao perseguindo boss que pula de canto em canto.
//
// nosave SavePoint devolve quem deslogar la dentro para o
//   proprio savepoint. Sem isto daria para deslogar dentro
//   do salao e voltar depois sem pagar.
//
// nobranch e noicewall tapam Galho Seco e Muro de Gelo, que
//   sao os dois jeitos classicos de quebrar sala de MVP.
//
// NAO ponha hidemobhpbar aqui: conf/battle/monster.conf usa
//   show_mob_info 2 para mostrar o HP do MVP em porcentagem,
//   e a mapflag desligaria justamente isso.
//======================================================
%(mapa)s\tmapflag\tnomemo
%(mapa)s\tmapflag\tnoreturn
%(mapa)s\tmapflag\tnoteleport
%(mapa)s\tmapflag\tmonster_noteleport
%(mapa)s\tmapflag\tnobranch
%(mapa)s\tmapflag\tnoicewall
%(mapa)s\tmapflag\tnosave\tSavePoint
'''


if __name__ == '__main__':
    gerar()
