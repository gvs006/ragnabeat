# Alterações em habilidades de classe

Toda mudança de skill feita neste servidor, com o antes, o depois e o porquê.
Se você alterou uma skill e não registrou aqui, ela vai virar bug de origem
desconhecida na próxima vez que alguém reclamar do dano.

> Skills **do Super Aprendiz EX** têm seção própria em
> [rebalance.md § 5](rebalance.md#5-skills-do-super-aprendiz-ex) — aquilo é
> árvore de skill, não ajuste de skill, e ainda está em proposta.

---

## Onde uma alteração de skill mora

São **três lugares diferentes**, e escolher o errado faz a mudança não pegar.

| O que muda | Onde | Recarrega com |
|---|---|---|
| dano, cast, alcance, área, empurrão, custo | `db/import/skill_db.yml` | `@reloadskilldb` |
| comportamento global de uma mecânica | `conf/battle/skill.conf` | `@reloadbattleconf` |
| quem aprende o quê | `db/pre-re/skill_tree.yml` | `@reloadskilldb` |

### O import mescla por campo — escreva só o que muda

Em [src/map/skill.cpp:15177](../src/map/skill.cpp#L15177) o parser faz:

```c
if (this->nodeExists(node, "CastTime")) { ... }
else { if (!exists) memset(skill->cast, 0, sizeof(skill->cast)); }
```

Para um `Id` que **já existe** no `db/pre-re`, campo ausente no import mantém o
valor original. Por isso a entrada do Bowling Bash tem quatro linhas e não
quarenta.

> ⚠ O `else` só zera quando `!exists`. **Não use o import para criar skill
> nova** — todo campo que você esquecer vira zero.

O `Name` é obrigatório junto do `Id`, mesmo quando não muda.

---

## As alterações

> Organizado **por classe**, não por arquivo. Quem vem aqui está atrás de
> "o que mudou na minha classe", e é essa a pergunta que o futuro site vai
> repetir. O aviso de rebalanceamento de cada uma está em citação, pronto
> para copiar.

---

## Cavaleiro / Lorde

### Impacto de Tyr — `KN_BOWLINGBASH` (62)

Pedido em 03/set/2026. Quatro mudanças, em **dois arquivos**.

| | antes | depois |
|---|---|---|
| Conjuração | 700 ms | **0** |
| Empurrão | 1 célula | **0** — mas *não* pelo skill_db, ver abaixo |
| Sistema de área | gutter lines oficiais | **caixa 5x5 no conjurador** |
| Bug de gutter | presente | eliminado junto |
| Exibição do dano | 1 número | **2 brancos + total amarelo** |

**No `db/import/skill_db.yml`:**

```yaml
- Id: 62
  Name: KN_BOWLINGBASH
  CastTime: 0
  Hit: Multi_Hit
  HitCount: -2
```

**No `src/map/skills/swordman/bowlingbash.cpp`:** a chamada de `skill_blown`
da linha 97 ficou comentada.

**No `conf/battle/skill.conf`:** `bowling_bash_area: 0` → **`2`**

#### Por que a área não está no skill_db

Este é o ponto que engana. O que define a área do Impacto de Tyr no
pre-renewal **não é o `SplashArea`** — é a caixa da reação em cadeia, calculada
em [bowlingbash.cpp:48-68](../src/map/skills/swordman/bowlingbash.cpp#L48):

```c
if (bowling_bash_area == 0) {
    // gutter line oficial
    min_x = ((src->x)-c) - ((src->x)-c)%40;   // <- o -c e o demi gutter bug
    max_x = min_x + 39;
} else if (bowling_bash_area == 1) {
    // gutter line sem o bug
    min_x = src->x - (src->x)%40;
} else {
    // caixa de +-N celulas em volta do conjurador
    min_x = src->x - bowling_bash_area;
}
```

Com `0`, o alvo é enquadrado num bloco de 40 células **deslocado por `c`** — e é
esse deslocamento que produz o comportamento errático conhecido como gutter
line. O valor `1` corrige o deslocamento mas mantém os blocos de 40. O valor
`2` abandona os blocos: passa a ser ±2 células em volta de quem conjurou, ou
seja **5x5**.

Um valor resolveu os dois pedidos — tirar o bug e dar o 5x5.

#### O GRF de gutter lines não é mais necessário

Aquele GRF que desenha as linhas divisórias no chão existe para o jogador saber
onde os blocos de 40 células começam e terminam. **Com `bowling_bash_area: 2`
não há mais blocos** — a área acompanha o conjurador, onde quer que ele esteja.
O auxílio visual perdeu a função e pode sair.

#### O empurrão NÃO se desliga pelo skill_db

> ⚠ **Correção de 04/set/2026.** A versão anterior deste documento dizia que
> `Knockback: 0` no import tinha tirado o empurrão. **Não tinha.** O campo é
> inerte para esta skill, e a consequência disso é a seção seguinte.

Dois motivos, os dois em
[bowlingbash.cpp](../src/map/skills/swordman/bowlingbash.cpp):

1. `modifyDamageData` já faz `dmg.blewcount = 0` de forma **incondicional** no
   pre-renewal ([linha 27](../src/map/skills/swordman/bowlingbash.cpp#L27)) —
   o valor do banco nunca chega a ser lido.
2. Quem empurra de verdade é uma chamada solta, com o `1` escrito na mão
   ([linha 97](../src/map/skills/swordman/bowlingbash.cpp#L97)):

```c
skill_blown(src,target,1,dir,BLOWN_NONE);
```

Ela está **comentada**, e é isso que tira o empurrão.

#### Isso custava metade do dano

Não era conforto: era dano. O laço da corrente move um cursor `(tx,ty)` em
`-dir` enquanto o empurrão levava o alvo em `+dir`.

| iteração | cursor | alvo | distância |
|---|---|---|---|
| início | 0 | 0 | 0 |
| i=0 **com** empurrão | −1 | +1 | **2** |
| i=0 **sem** empurrão | −1 | 0 | **1** |

Os dois se afastavam **duas células por iteração**. O splash 3x3 em volta do
cursor nunca mais alcançava o alvo, `count` ficava zero, e sem `count` a
auto-colisão da [linha 109](../src/map/skills/swordman/bowlingbash.cpp#L109)
não dispara. Sobrava só o golpe final da
[linha 114](../src/map/skills/swordman/bowlingbash.cpp#L114):

**um golpe onde o Bowling Bash clássico dá dois.**

Com `bowling_bash_area: 2` ficava pior ainda — o alvo saía da caixa 5x5 numa
iteração e passava a ser descartado logo na entrada da função
([linha 72](../src/map/skills/swordman/bowlingbash.cpp#L72)).

O comentário do `skill.conf` já avisava, e foi lido do jeito errado:

> *If you knock the target out of the area it will only be hit once and won't
> do splash damage*

#### Espada de duas mãos não dá golpes extras aqui

O bônus que faz `div_` virar 3 ou 4 com espada de duas mãos está dentro de
`#ifdef RENEWAL` ([linhas 17-25](../src/map/skills/swordman/bowlingbash.cpp#L17-L25)).
No pre-renewal **não existe**.

Isso não quer dizer que a arma não importe: a Espada Veterana (`Veteran_Sword`,
180 de ATK) aumenta o dano do Impacto de Tyr como qualquer outra arma, via ATK.
O que ela não faz é somar golpes.

#### A contagem de golpes é NEGATIVA, e isso não é engano

`HitCount: -2` faz a skill sair como rajada de dois golpes **sem alterar o dano
total**. Quem decide é o `DAMAGE_DIV_FIX`, em
[battle.cpp:4350](../src/map/battle.cpp#L4350):

```c
#define DAMAGE_DIV_FIX(dmg, div) \
    { if ((div) < 0) { (div) *= -1; (dmg) /= (div); } (dmg) *= (div); }
```

| valor | efeito |
|---|---|
| `HitCount: 2` | só multiplica → **dobro do dano** |
| `HitCount: -2` | divide e depois multiplica → **mesmo total**, em 2 golpes |

O número amarelo com o total é o cliente que desenha sozinho, porque o `Hit:
Multi_Hit` manda o tipo `DMG_MULTI_HIT`. Não é invenção nossa: **81 skills do
`db/pre-re` usam esse mesmo par** — o Golpe Sônico é `-8`.

> ⚠ Trocar o `-2` por `2` dobra o dano do Impacto de Tyr. É um sinal de menos
> separando as duas coisas.

---

## Champion

### Explosão de Energia — `MO_EXTREMITYFIST` (271)

Alterado em 03/set/2026. **Não mexemos na skill** — mexemos em quem tinha
permissão de melhorá-la.

> **Aviso de rebalanceamento**
> *Canto de Batalha — agora funciona em Champions e Criadores.*

Antes, o buff de ataque do Canto de Batalha (`PA_GOSPEL`, 369) era ignorado por
completo pela Explosão de Energia. O Champion tomava o buff, via o ícone, e o
dano não subia um ponto.

**No `src/map/battle.cpp`:** `MO_EXTREMITYFIST` saiu da lista de
`battle_skill_stacks_masteries_vvs` ([:3376](../src/map/battle.cpp#L3376)).

#### Por que uma lista de exceção apagava um buff inteiro

Estar naquela lista não custa um bônus — custa **cinco grupos de uma vez**:

| onde | o que era descartado |
|---|---|
| [3821](../src/map/battle.cpp#L3821) | Star Crumb |
| [3826](../src/map/battle.cpp#L3826) | dano de esferas espirituais |
| [3907](../src/map/battle.cpp#L3907) | dano de maestria |
| [4469](../src/map/battle.cpp#L4469) | **todo o grupo ATKpercent** |
| [5016](../src/map/battle.cpp#L5016) | bônus de refino |

O ATKpercent é o que carrega o `SC_INCATKRATE` do Canto de Batalha. E é tudo ou
nada — o comentário da própria função avisa:

> *This bonus works as a separate unit to the rest (e.g., if one of these is
> not applied to a skill, then we know none are)*

Junto com o Canto de Batalha voltaram Provocar, Aumentar Concentração, Sentido
Verdadeiro e Bloodlust, que caíam no mesmo bloco
([battle.cpp:4472-4497](../src/map/battle.cpp#L4472-L4497)).

#### O que NÃO mudou

A fórmula continua a mesma
([asurastrike.cpp](../src/map/skills/acolyte/asurastrike.cpp)):

```c
base_skillratio += 700 + sstatus->sp * 10;
```

Isso é **multiplicador em cima do dano de ATK**, não um substituto dele — o
Asura sempre dependeu das duas coisas. O que faltava era só o grupo de
percentuais.

**Perfurar Armadura (`MO_INVESTIGATE`) continua excluída.** A decisão foi só
para a Explosão de Energia.

---

## Criador

### Terror Ácido — `AM_ACIDTERROR` (230)

Mesma alteração, mesma data, mesmo motivo do Champion acima — o Terror Ácido
estava na mesma lista.

> **Aviso de rebalanceamento**
> *Canto de Batalha — agora funciona em Champions e Criadores.*

**No `src/map/battle.cpp`:** `AM_ACIDTERROR` saiu da lista de
`battle_skill_stacks_masteries_vvs` ([:3376](../src/map/battle.cpp#L3376)).

Vale a leitura da seção do Champion: o mecanismo é o mesmo, e os cinco grupos
de bônus que voltaram são os mesmos.

---

## Classes que seguem intocadas nesse ponto

Estavam na mesma lista e **foram deixadas de fora de propósito**, para a
mudança ficar restrita ao que foi pedido:

| skill | classe |
|---|---|
| `MO_INVESTIGATE` | Perfurar Armadura — Champion |
| `PA_SACRIFICE` | Sacrifício — Paladino |
| `PA_SHIELDCHAIN` | Corrente de Escudo — Paladino |
| `CR_SHIELDBOOMERANG` | Bumerangue de Escudo — Cruzado |
| `LK_SPIRALPIERCE` | Perfurar — Lorde (caso condicional no pre-renewal) |

Se um dia alguém perguntar "por que o Canto de Batalha funciona no Champion mas
não no Paladino", a resposta é esta tabela, e não um bug.

---

## Mudanças de conf que afetam combate, mas não são de skill

Ficam aqui porque quem procura "por que o dano mudou" vai olhar neste arquivo.

| Config | Antes | Depois | Por quê |
|---|---|---|---|
| `conf/battle/drops.conf` → `first_attack_loot_bonus` | 30 | **0** | quem atacou primeiro ganhava 30% do dano total como bônus na fila de loot. Isso descolava o dono do item de MVP (maior dano cru) de quem o `OnNPCKillEvent` credita (topo da fila de loot) — e o Salão dos Bravos dava ponto para a pessoa errada. Ver [npc/custom/rank_mvp.txt](../npc/custom/rank_mvp.txt) |
| `conf/battle/monster.conf` → `show_mob_info` | 0 | **2** | mostra o HP do monstro em porcentagem ao lado do nome |

---

## O que ainda NÃO foi alterado

Registrado para não parecer esquecimento:

- **Nenhuma skill teve dano alterado.** Todo o balanço de dano é o do
  pre-renewal do rAthena.
- A árvore de skill (`skill_tree.yml`) está intocada — inclusive a proposta do
  Super Aprendiz EX, que continua aguardando as duas decisões da
  [rebalance.md § 5](rebalance.md#5-skills-do-super-aprendiz-ex).
