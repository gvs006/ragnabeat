# Rebalance e itens trazidos do renewal

Proposta para revisão. **Nada aqui está no jogo ainda** — os valores abaixo são
sugestão minha, ancorada no que o pre-renewal já tem. Aprove, corrija ou risque
item por item, e só então eu escrevo no `db/`.

Data: 11/ago/2026.

---

## 1. A regra do servidor

- Pre-renewal (`PRERE` em `src/config/renewal.hpp:8`), teto **99 base / 70 job**.
- **Não existe 3ª classe.** Item com `Classes: All_Third` ou `Fourth` não é
  equipável por ninguém aqui.
- **`EquipLevelMin` acima de 99 é inalcançável.** Vários itens de renewal pedem
  100+ e entrariam mortos.
- Fórmulas de dano, DEF e refino são as antigas. Número de renewal colado no
  pre-re quase sempre fica forte demais — DEF é o caso mais gritante.

## 2. Por onde um item entra

Três camadas, e as três precisam existir:

| Camada | Arquivo | Situação |
|---|---|---|
| Servidor | [db/ragnabeat_items.yml](../db/ragnabeat_items.yml) | pronto — carrega por último, ganha de tudo |
| Nome/descrição no cliente | `SystemEN/itemInfo_C.lua` | hoje só tem os 4.440 itens de pre-re |
| Sprite/textura | `data.grf` | **não é garantido — tem que conferir item a item** |

**Nome/descrição.** A fonte já existe: `DEVTOOLS/PTBR/iteminfo_ptBR.lua`
(16.731 itens do RO LATAM) **tem os itens de renewal em PT-BR** — conferi o
1746, está lá como "Arco Élfico" com descrição completa. É só estender o
gerador para incluir os IDs importados. Sem isso o item aparece com nome em
coreano/inglês do GRF base.

**Sprite.** Aqui eu estava errado numa versão anterior deste documento: o GRF
de cliente 2025 **não** tem tudo. A "Lendárias Asas de Demônio" (5376) tem
entrada no itemInfo e ícone de collection, mas **nenhum sprite** — foi
exatamente isso que produziu o erro na tela:

```
Cannot find File : sprite\<coreano>.act
```

Por isso existe agora [cliente/checar-sprite.py](cliente/checar-sprite.py).
Rode **antes** de pôr qualquer item novo no `db`:

```
python docs/cliente/checar-sprite.py 5376 5451 1746
```

Ele lê a tabela do `data.grf` sem extrair nada e diz, por item, se existem o
sprite de chão, o sprite vestido e o ícone. `drop=False` significa caixa de
erro na cara do jogador — item vetado até alguém pôr o sprite num GRF custom.

Resultado da varredura de todos os itens desta proposta (11/ago/2026): só o
5376 falhou. Todo o resto está completo no GRF.

---

## 3. Já existem em pre-renewal — nada a importar

Estes você pediu e **já estão no `db/pre-re`**. Só precisam ser colocados à
venda:

| Item | AegisName | ID | Observação |
|---|---|---|---|
| Orelha de Elfo [1] | `Elven_Ears_` | 18507 | idêntica à de renewal. Lv 70, meio da cabeça, Novato e S.A. não usam |
| Orelha de Elfo | `Elven_Ears` | 2286 | sem slot |
| Chapéu de Super Aprendiz [1] | `Super_Novice_Hat_` | 5119 | DEF 4 aqui, 8 no renewal. Todos os Atributos +1 |
| Espírito do Dragão de Ouro | `Dragonhelm_Gold` | 5451 | topo, DEF 7, 1 slot. ASPD +10%, Todos os Atributos +3, +5% dano em Semi-Humano |
| Espírito do Dragão de Prata | `Dragonhelm_Silver` | 5452 | topo, DEF 5, 1 slot. ASPD +7%, Atributos +2, +3% em Semi-Humano |
| Espírito do Dragão de Bronze | `Dragonhelm_Copper` | 5453 | topo, sem DEF, 1 slot. ASPD +5%, Atributos +2, +1% em Semi-Humano |

Os três Espíritos do Dragão são os "RWC ouro/prata/bronze" — no db eles se
chamam *RWC 2008 Dragon Helm*. **A versão de pre-re é diferente da de renewal**
e é melhor deixar a nossa: a de renewal troca ASPD e atributos por resistência
a Semi-Humano. Os três já vêm com todas as travas de comércio (`NoDrop`,
`NoTrade`, `NoSell`, `NoCart`, `NoMail`, `NoAuction`) — proponho **manter**,
são itens de premiação.

---

## 4. Importar do renewal — proposta item a item

### 4.1 Arco Élfico — `Elven_Bow` (1746)

Vem como: ATK 160, Nível de Arma 3, 1 slot, duas mãos, Arqueiro/Bardo-Dançarina
e Caçador, `EquipLevelMin: 100`, `Classes: All_Third + Fourth`, DEX +2.

Âncora do pre-re (arcos com slot): `Balistar_` ATK 145, Lv4, 1 slot, req. 77.
Sem slot chega a 170 (`Bow_Of_Evil`) e 194 nos `_C` de evento.

**Proposta — só o que você pediu, nível e classe:**

| Campo | De | Para | Por quê |
|---|---|---|---|
| `EquipLevelMin` | 100 | **90** | 100 é impossível com base máx 99 |
| `Classes` | All_Third, Fourth | **Normal, Upper, Baby** | senão ninguém equipa |
| `Attack` | 160 | **160** (manter) | fica entre o `Balistar_` (145, com slot) e o `Bow_Of_Evil` (170, sem slot). Nível de Arma 3 já o pune no refino |
| Resto | — | intacto | 1 slot, DEX +2, peso 1500 |

### 4.2 Flecha Élfica — `Arrow_Of_Elf` (1773)

Vem como: ATK 45, peso 1, `EquipLevelMin: 100`, Arqueiro/Ladrão/Assassino/
Bardo-Dançarina/Caçador/Arruaceiro.

| Campo | De | Para | Por quê |
|---|---|---|---|
| `EquipLevelMin` | 100 | **0** | flecha com requisito de nível é um estorvo; e 100 é impossível |
| `Attack` | 45 | **45** (manter) | acima da Flecha de Aço (40) e sem o bônus elemental da de Prata |

### 4.3 Mochila da Aventura — `Bravery_Bag` (2576)

Vem como: manto, **DEF 20**, 1 slot, refinável, `View: 2`, dá `BS_GREED` nível 1,
e a partir do refino +7 dá bônus conforme o atributo passar de 90 (ATQ, MATQ,
resistência Neutro, ASPD, etc).

Âncora: o manto com mais DEF do pre-re inteiro é **10** (Ruffler, Capa de Freyja).
DEF 20 seria o dobro do teto do episódio.

| Campo | De | Para | Por quê |
|---|---|---|---|
| `Defense` | 20 | **10** | empata com o melhor manto do pre-re em vez de dobrá-lo |
| Script de refino | intacto | **intacto** | os gatilhos de atributo ≥90 são alcançáveis aqui (teto 99) |
| `skill "BS_GREED",1` | intacto | **intacto** | conveniência, não é poder de combate |

**Versão aluguel:** o barter não sabe entregar item alugado. Ela vira uma opção
separada no script do NPC, com `rentitem 2576,<segundos>`. Preciso que você
diga a duração — sugiro **7 dias** (604800 s).

### 4.4 Cartas Seladas MVP — 44 itens (`Sealed_*_Card`)

São as versões fracas das cartas MVP. Exemplo, `Sealed_Kiel_Card` (4480):
`bonus bDelayrate,((getrefine()>14)?-20:-15);` — contra -30 da Kiel de verdade.

**Armadilha:** quase todas testam `getrefine()>14`. O refino máximo do
pre-renewal é **10**, então esse ramo nunca dispara e elas ficam sempre no valor
menor. Não quebra nada, mas metade do texto do item vira letra morta.

| Decisão | Proposta |
|---|---|
| Quais entram | as que têm equivalente MVP já vendido pelo Contrabandista — as demais ficam de fora |
| `getrefine()>14` | trocar para **`>9`** (refino máximo daqui), para o ramo alto existir |
| Preço | mais barato que a carta real; sugiro **30 Moedas de Mythril** contra 100 |

Se preferir trazer as 44 de uma vez, é a mesma quantidade de trabalho — só me
diga.

### 4.5 Amplificador de Som [1] — `Sound_Amplifier` (2899)

Nome real no db: "Sound Amplification Device". Acessório, 1 slot, Lv 90,
Bardo-Dançarina e Caçador.

O script que vem é **inutilizável em pre-re**: usa `WM_METALICSOUND` (skill de
3ª classe, não existe) e `bVariableCastrate` (conjuração fixa/variável é
conceito de renewal).

**Proposta — reescrever o script para o que você pediu:**

```
bonus2 bSkillDelay,"SN_SHARPSHOOTING",-500;
```

Tiro Preciso é `SN_SHARPSHOOTING` (Sniper). `bonus2 bSkillDelay` reduz o
pós-conjuração daquela skill em milissegundos — **-500 = meio segundo**.
Diga se quer mais ou menos. Mantendo Lv 90 e as classes como vêm (Caçador
inclui Sniper).

### 4.6 Boina Charmosa — `Parade_Cap` (5468)

Confirmada pelo link que você mandou. Topo da cabeça, DEF 3, 1 slot, refinável,
`View: 465`. Script:

```
bonus bDelayrate,-5;              // pós-conjuração -5%
bonus bMdef,2;
if (getrefine() > 5)
   bonus bVariableCastrate,-(getrefine()-5);   // -1% de conjuração por refino acima de +5
```

Conferi: em pre-renewal o `bVariableCastrate` **funciona** — sem `RENEWAL_CAST`
ele é tratado como `bCastrate` (`doc/item_bonus.txt:240`). Ou seja, o item
funciona exatamente como você descreveu, sem reescrever nada.

**Proposta: entra como está.** DEF 3 e -5% de pós-conjuração são modestos, e o
teto do refino aqui é +10, então o bônus de conjuração para em -5%.

### 4.7 Lendárias Asas de Demônio — `Satanic_Chain_P` (5376)

É esse item mesmo: no LATAM o 5376 se chama **"Lendárias Asas de Demônio"**.
Topo da cabeça, DEF 6, 1 slot, `View: 382`, **SP Máx +120** e 10% de amaldiçoar
ao ser atingido — bate com o que você descreveu.

**O sprite existe.** A causa do erro não é o item: é que os dois clientes da
máquina não têm o mesmo conteúdo.

```
5376  |build drop=False vestido=0  |prod drop=True vestido=2   <<< FALTA NO BUILD
```

Os seis arquivos (`사타닉체인.spr`/`.act` de chão + masculino e feminino
vestidos) estão em `C:\RagnaClient\data.grf`. **Não** estão no
`RagnaBeat.Dev\data.grf`, que é o que vira build para os jogadores. Detalhe em
[cliente/leia-me.md](cliente/leia-me.md).

Ou seja: **não há decisão de balanceamento pendente aqui**. O item entra como
está (DEF 6, SP +120, 1 slot, dentro da escala do pre-re) assim que os sprites
forem para o GRF do build.

**Resolvido em 12/ago/2026.** Os 6 arquivos foram extraídos do GRF de produção
e postos soltos na pasta `data\` do cliente de dev:

```
RagnaBeat.Dev\data\sprite\아이템\사타닉체인.spr           1.245 bytes
RagnaBeat.Dev\data\sprite\아이템\사타닉체인.act             116 bytes
RagnaBeat.Dev\data\sprite\악세사리\남\남_사타닉체인.spr    23.113 bytes
RagnaBeat.Dev\data\sprite\악세사리\남\남_사타닉체인.act    83.220 bytes
RagnaBeat.Dev\data\sprite\악세사리\여\여_사타닉체인.spr    23.113 bytes
RagnaBeat.Dev\data\sprite\악세사리\여\여_사타닉체인.act    83.220 bytes
```

Pasta solta em vez de GRF porque é assim que o projeto já sobrescreve conteúdo
(os `.lub` de `data\luafiles514\`), o `build.py` copia a `data\` inteira para o
jogador, e não exige mexer no `DATA.ini`. Detalhe técnico da extração em
[cliente/leia-me.md](cliente/leia-me.md).

**Falta testar in-game** — passar o mouse no inventário e equipar.

---

## 5. Skills do Super Aprendiz EX

Boa notícia: não precisa de C++ nem de skill nova.

No renewal, o `Super_Novice_E` (`db/re/skill_tree.yml`) é o Super Aprendiz
normal **herdando a árvore de Novato e S.A.** e ganhando por cima um punhado de
skills de 2ª classe que **já existem em pre-renewal**: `PR_IMPOSITIO`,
`PR_ASPERSIO`, `PR_SANCTUARY`, `PR_STRECOVERY`, `PR_MAGNIFICAT`, `PR_GLORIA`,
`WZ_FIREPILLAR`, `WZ_SIGHTRASHER`, `WZ_METEOR`, `WZ_JUPITEL`, `WZ_VERMILION`,
`WZ_WATERBALL` e outras.

**Proposta:** copiar essa lista para o `Super_Novice` de
`db/pre-re/skill_tree.yml`, mantendo os pré-requisitos como estão no renewal.
Nosso S.A. passa a poder aprender essas skills sem virar outra classe.

Antes de fazer, preciso de duas decisões suas:

1. **Todas** as skills da árvore EX, ou uma seleção? A lista completa deixa o
   S.A. com Meteoro e Bola d'Água — é uma classe bem diferente do que era.
2. O teto de job 70 do pre-re dá **menos pontos de skill** que o renewal. Ele
   não vai conseguir tudo de qualquer jeito; é isso mesmo que você quer?

**Equips de Super Aprendiz:** o `Super_Novice_Hat_` (5119) já existe aqui.
Me diga quais outros você tem em mente.

---

## 6. Pendências — não consegui identificar

Resolvidas na sua última mensagem:

- ~~RWC ouro/prata/bronze~~ → são os **Espíritos do Dragão** 5451/5452/5453, e
  **já existem em pre-re**. Ver seção 3.
- ~~Boina charmosa~~ → **`Parade_Cap` (5468)**. Ver 4.6.
- ~~Asas de demônio~~ → é o 5376 mesmo, mas está **bloqueado por falta de
  sprite**. Ver 4.7.

Ainda em aberto:

### 6.1 Asas de Demônio — como levar os sprites para o build
A, B ou C da tabela em 4.7. O item em si já está resolvido.

### 6.2 Rosa eterna
Só existe `C_Eternal_Rose`, que é **traje** (costume, sem atributo). Candidatos
com atributo: `Rose_Of_Eden`, `Mistic_Rose`, `Miracle_Blue_Rose`,
`Rapture_Rose`, `Nile_Rose`. Qual é? Um link do ragnaplace resolve na hora,
como resolveu a Boina.

### 6.3 Duração do aluguel
Da Mochila da Aventura (4.3). Sugestão: 7 dias.

### 6.4 Cartas seladas
Trazer só as que têm MVP equivalente à venda, ou as 44?

### 6.5 Skills do Super Aprendiz
As duas decisões da seção 5: árvore EX inteira ou seleção.

---

## 7. Menu do Contrabandista

Fica em dois níveis, como combinado: primeiro a parte do corpo, depois o tipo.

```
[Contrabandista]
> Capas
    > Cartas [Capas]
    > Equips [Capas]
    > Equips 3rd [Capas]
> Elmo
    > Cartas [Elmo]
    > Equips [Elmo]
    ...
```

Cada folha é uma loja barter em [npc/custom/barters.yml](../npc/custom/barters.yml).
Categoria sem item ainda **não aparece no menu** — nada de porta que abre para
uma sala vazia.

Ainda em aberto: o que é "Equips 3rd" em pre-renewal. Não existe 3ª classe
aqui. Você quer dizer equipamento *originário* do episódio das 3ª classes
(trazido para cá como os desta proposta), ou outra coisa?

---

## 8. O que já está no jogo

Implementado em 12/ago/2026 com os valores propostos acima. Servidor
reiniciado, 7 itens e 11 lojas carregados, zero erro no console.

| Onde | O quê |
|---|---|
| [db/ragnabeat_items.yml](../db/ragnabeat_items.yml) | os 6 itens do renewal + o peso 0 da moeda |
| `SystemEN/itemInfo_C.lua` | nome e descrição PT-BR dos 5 novos (o 5376 já estava). Total 5.296 → **5.301** |
| [npc/custom/barters.yml](../npc/custom/barters.yml) | 11 lojas, 41 itens |
| [npc/custom/black_market.txt](../npc/custom/black_market.txt) | menu de dois níveis |
| `RagnaBeat.Dev\data\sprite\` | os 6 sprites das Lendárias Asas de Demônio |

**A descrição do cliente foi corrigida onde nós mudamos o item.** O texto do
LATAM descreve a versão de renewal, então o tooltip mentiria: o Arco Élfico
diria "Nível necessário: 100" num servidor de nível máximo 99. As trocas estão
na tabela `AJUSTES` de [cliente/add-item-ptbr.py](cliente/add-item-ptbr.py) —
nível 100 → 90, classes de 3ª → Caçadores/Bardos/Odaliscas, DEF 20 → 10, e o
efeito do Amplificador reescrito para o Tiro Preciso. Mudou número no db?
Mude ali junto.

### Ainda de fora

- **Flecha Élfica** está no db (e no `@ii`) mas **não está à venda**. A 1 moeda
  por unidade sairia a 100.000 Zeny a flecha; munição precisa de loja de Zeny,
  não da moeda do Mercado Negro. Diga onde você quer.
- **Cartas seladas** — pendência 6.4.
- **Skills do Super Aprendiz** — pendência 6.5.
- **Mochila da Aventura versão aluguel** — pendência 6.3 (falta a duração).
