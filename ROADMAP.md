# Ragnabeat — Roadmap de Features

Servidor **pre-renewal** (`PRERE` definido em [src/config/renewal.hpp:8](src/config/renewal.hpp#L8)), `PACKETVER 20250416`
(em [src/custom/defines_pre.hpp](src/custom/defines_pre.hpp)), rates 500x/20x, limites 99/70, stack Docker + MariaDB.

> Este arquivo cobre **o que construir**. Para como o que já existe funciona — infra,
> portas, auth token, segurança, cliente — ver **[docs/](docs/README.md)**.

Legenda de origem:
- 🟢 **Nativo** — já está no rAthena, só configurar/popular dados
- 🟡 **Script** — NPC custom, sem recompilar
- 🔴 **C++** — exige alterar `src/` e recompilar o map-server
- 🔵 **Fork/externo** — código de terceiros (eAmod, releases da comunidade) a portar

---

## Fase 0 — Base (concluído)

- [x] Stack Docker (login/char/map + MariaDB), rede e IPs
- [x] Rates 500x/20x, limites 99/70
- [x] Comandos custom de jogador
- [x] NPCs custom: jobmaster (PT-BR), curandeira, black market, hunting missions, quest shop, questboard

---

## Fase 1 — Itens e progressão

### 1.1 Random Options (bônus aleatórios em item) 🟢
**Status: engine 100% pronta, faltam só os dados.**

- Engine sem guard de RENEWAL: [itemdb.cpp:4460](src/map/itemdb.cpp#L4460), [itemdb.cpp:4575](src/map/itemdb.cpp#L4575)
- Exibição no client exige `PACKETVER >= 20150226` ([clif.cpp:2868](src/map/clif.cpp#L2868)) — **ok**
- Script commands: `setrandomoption`, `getrandomoptinfo`, `randomoptgroup`, `getitem3`/`getitem4`
- **Sem restrição por tipo/localização de item** — `s_random_opt_group::apply()` não checa nada.
  Headgear e acessório podem receber bônus igual a arma; excluí-los é decisão de balance, não limitação.

**Teto de 5 opções — é do protocolo.** `MAX_ITEM_RDM_OPT = 5` ([mmo.hpp:113](src/common/mmo.hpp#L113)) casa
com o pacote de item, que carrega `{ <option id>.W <option value>.W <option param>.B }*5` fixo
(ver `ZC_ITEM_PICKUP_ACK_V6` em [clif.cpp:2835](src/map/clif.cpp#L2835)). **Não dá para passar de 5**
sem alterar o client. O padding em [clif.cpp:2820](src/map/clif.cpp#L2820) confirma que o rAthena assume
que o client sempre espera 5 blocos.

**`Slots` × `MaxRandom` — armadilha do parser.** O comentário no cabeçalho do YAML diz que `MaxRandom` é
uma *quantidade* limitada a `(5 - total de Slots)`. **O código não faz isso.** O loop de `apply()` percorre
os **índices** `0 .. MaxRandom-1` e pula os já ocupados pelos `Slots`; o parser só limita `MaxRandom` a 5,
sem descontar os Slots. Ou seja, `MaxRandom` é um **teto de índice**, não uma contagem:

- 1 Slot garantido + `MaxRandom: 4` → 1 a 4 bônus
- 1 Slot garantido + `MaxRandom: 3` → 1 a 3 bônus (não 4)
- Total possível = `max(nº de Slots, MaxRandom)`

Ao final, `apply()` compacta os buracos ("*Fix any gaps, the client cannot handle this*") — chance que
falhou não deixa slot vazio no meio.

**Bloqueio:** [db/item_randomopt_db.yml](db/item_randomopt_db.yml) e
[db/item_randomopt_group.yml](db/item_randomopt_group.yml) importam os dados com `Mode: Renewal`,
que é ignorado no build PRERE.

**Tarefas**
- [ ] Criar `db/import/` a partir de [db/import-tmpl/](db/import-tmpl/)
- [ ] Portar as opções base de [db/re/item_randomopt_db.yml](db/re/item_randomopt_db.yml) para `db/import/item_randomopt_db.yml`
      (as ~40 relevantes: STR/AGI/VIT/INT/DEX/LUK, ATK/MATK %, ASPD, crit, resistência de raça/elemento)
- [ ] Escrever grupos próprios em `db/import/item_randomopt_group.yml` com balance de pre-re
      (**não** copiar as 16k linhas de [db/re/item_randomopt_group.yml](db/re/item_randomopt_group.yml))
- [ ] Definir tiers: comum / raro / MVP — e onde cada um cai
- [ ] Aplicar via `RandomOptionGroup` em drops de mob ([mob.cpp:4908](src/map/mob.cpp#L4908)),
      `item_group_db` e caixas do `item_db`
- [ ] (opcional) NPC de reroll consumindo item, usando `setrandomoption` — 🟡

**Nota:** o client precisa ter `enumvar.lub` com os IDs de opção correspondentes, senão a descrição aparece em branco.

#### Aplicação global (todo equipamento dropado vem com bônus)

**Não existe hook global.** `apply()` só é chamado em 4 lugares:

| Onde | Origem do grupo |
|---|---|
| [mob.cpp:2488](src/map/mob.cpp#L2488) | `RandomOptionGroup` **por drop** no mob_db |
| [itemdb.cpp:3100](src/map/itemdb.cpp#L3100) | `item_group_db` (caixas) |
| [script.cpp:27044](src/map/script.cpp#L27044) | buildin `randomoptgroup` |
| itemdb.cpp:2148 / 2868 | laphine upgrade / item_packages |

Duas rotas:

- **A (🟢 dados puros):** gerar `RandomOptionGroup` em cada linha de drop de equipamento do mob_db.
  Milhares de entradas — diff gigante que conflita em todo merge com o upstream. **Descartada.**
- **B (🔴 ~10 linhas, recomendada):** patch em `mob_setdropitem_option` ([mob.cpp:2482](src/map/mob.cpp#L2482)):
  se o drop não tem grupo definido **e** o item é equipamento, aplica um grupo default lido de `battle_config`.
  Recompila uma vez; depois tudo fica configurável por YAML + conf. Dá para escolher o grupo por
  `weapon_level`/`equip_level_min` do item ou pelo level do mob — assim mapa inicial dropa tier 1 e MVP
  dropa tier 3, sem tocar em mob_db. Patch fica em `src/custom/` para não conflitar no merge.

**Limite das duas rotas:** cobrem **só drop de mob**. Item de loja, quest, craft e MVP room não recebem
bônus — para esses é preciso `randomoptgroup` no script do NPC.

**Decisão pendente:** headgear e acessório entram no sistema ou ficam de fora?

### 1.2 Enchant por slot de carta 🟡
Sistema clássico pre-re, sem dependência de client novo. Bases prontas para adaptar:
[socket_enchant2.txt](npc/re/merchants/socket_enchant2.txt), [enchan_mora.txt](npc/re/merchants/enchan_mora.txt),
[enchan_upg.txt](npc/re/merchants/enchan_upg.txt).

- [ ] Escolher equips-alvo (headgears de quest / armas de fim de game)
- [ ] Tabela de enchants por tier + custo + chance de quebra
- [ ] Decidir convivência com Random Options (sugestão: enchant nos equips de quest, randopt nos drops)

### 1.3 Refino custom 🟡🟢
- [ ] Revisar [db/pre-re/refine.yml](db/pre-re/refine.yml) para as rates do servidor
- [ ] NPC de refino seguro / HD ore adaptado ao pre-re

---

## Fase 2 — Quality of Life

### 2.1 `@restock` 🟡 — **EXCLUSIVO VIP** (decidido)

> ⚠️ **Decisão travada:** `@restock` é **benefício exclusivo de VIP**, não comando geral.
> Razão: se todo mundo usa, deixa de ser diferencial e vira requisito. É a principal
> feature de conversão do pacote VIP.
> **Depende da fase 3.1** — o gate só pode ser ligado depois que o VIP existir.
> **Enquanto isso:** implementar o comando já com o gate escrito e desativado por uma flag
> (`.VipOnly = 0` no `OnInit`), para virar a chave sem reescrever nada.

**Não existe no rAthena** (sem ocorrências em `src/map/atcommand.cpp` nem em [conf/atcommands.yml](conf/atcommands.yml)).

**Base escolhida:** versão do usuário *coiselves* no
[tópico 127084 do rAthena](https://rathena.org/board/topic/127084-utility-restock-get-items-from-storage-with-a-command/#comment-450556)
— é o `@restock` do Mastagoon (v1.2, com correção de hannahhaven621) mais um loop de `addtimer` de 5 s.
Reabastece sozinho, em qualquer mapa, durante o combate. `bindatcmd`, **sem recompilar**.

Verificado no código-fonte, a base é sólida:
- `storagecountitem` lê `sd->storage.u.items_storage` da memória, e o storage é carregado no login
  ([pc.cpp:2434](src/map/pc.cpp#L2434)) → funciona com o armazém **fechado**, que é a premissa do sistema ✓
- Com o storage **aberto** retorna `-1`, e o `if (.@in_storage > 0)` já barra ✓
- `getiteminfo(.@item, 2)` = `ITEMINFO_TYPE` ([script.hpp:2238](src/map/script.hpp#L2238)) — índice numérico ainda bate ✓
- `getitem` falhando aborta o script **antes** do `storagedelitem` → não perde item ✓

**Correções obrigatórias antes de subir** (3 defeitos na versão publicada):

- [ ] **Vazamento de timer.** O `addtimer` está *antes* do `if (!RestockAuto) end;`, então desligar o auto
      não mata a cadeia — ela tica para sempre. E cada `@restock auto` religado cria uma cadeia nova.
      Corrigir com `deltimer` antes de agendar e sair sem reagendar quando `RestockAuto == 0`.
- [ ] **Flood de erro no console.** Com peso alto, `pc_additem` falha e o `getitem` emite
      `ShowError("buildin_getitem: Failed to add the item to player")` **a cada 5 s, por jogador**.
      Corrigir com `checkweight` antes do `getitem`.
- [ ] **Cap de quantidade e tipos.** O coiselves subiu o cap de 500 → 30000. Voltar para valor baixo e
      cortar `.allowedtypes` para `0,2,3,10,11` (healing, usable, etc, ammo, delayconsume) — a lista
      original inclui tipo 7/8 (pet egg/armor) e 12 (shadow gear).

**Outras tarefas**
- [ ] Gate de VIP no topo do `OnAtcommand` **e** do `OnAutoRestockTick` (o tick é o que realmente importa —
      sem ele o VIP expirado continuaria sendo servido pelo timer já agendado)
- [ ] Ao expirar o VIP: matar o timer e zerar `RestockAuto`, senão o benefício sobrevive à assinatura
- [ ] Traduzir mensagens para PT-BR
- [ ] Subir o intervalo de 5 s → 10 s e medir custo (1 timer/jogador; 200 online com lista de 10 itens
      ≈ 400 iterações/s + acesso a storage)
- [ ] Decidir se a lista fica em variável de char (por personagem) ou de conta (`#RestockList`, compartilhada)

### 2.2 Sala VIP 🟡
- [ ] Mapa dedicado (warp exclusivo, healer, storage, refinador, shops)
- [ ] Gate de acesso: `vip_status()` (se VIP nativo) ou variável de conta
- [ ] `mapflag` noteleport/nosave conforme o desenho
- Bases: [npc/custom/healer.txt](npc/custom/healer.txt), [npc/custom/warper.txt](npc/custom/warper.txt)

### 2.3 Outros QoL 🟡
- [ ] Warper / Healer / Stylist / Reset já existem em [npc/custom/](npc/custom/) — só habilitar em `npc/scripts_custom.conf`
- [ ] Banco ([bank.txt](npc/custom/etc/bank.txt)) e Floating Rates ([floating_rates.txt](npc/custom/etc/floating_rates.txt))
- [ ] Revisar `@autoloot`, `@go`, `@storage` em [conf/groups.yml](conf/groups.yml)

---

## Fase 3 — Sistema VIP + Vote4Points

### 3.1 VIP

`VIP_ENABLE` está **comentado** em [src/config/core.hpp:51](src/config/core.hpp#L51) — o sistema nativo está desligado.

#### O que o VIP nativo entrega (escopo completo, mapeado por `pc_isvip`)

| Feature | Config | Default | Onde |
|---|---|---|---|
| Bônus de EXP base/job | `vip_base_exp_increase` / `vip_job_exp_increase` | +50% | [pc.cpp:8349](src/map/pc.cpp#L8349) |
| Bônus de drop | `vip_drop_increase` | +50% | [mob.cpp:2856](src/map/mob.cpp#L2856) |
| Penalidade de morte reduzida | `vip_exp_penalty_base/job`, `vip_zeny_penalty` | 100/100/0 | [pc.cpp:9964](src/map/pc.cpp#L9964) |
| Battle Manual mais forte | `vip_bm_increase` | 2x | [pc.cpp:8358](src/map/pc.cpp#L8358) |
| Dispensa Blue Gemstone | `vip_gemstone` | 2 | [status.cpp:3812](src/map/status.cpp#L3812) |
| Storage maior | `vip_storage_increase` | +300 slots | battle.cpp:8808 |
| Slots de char extras | `MAX_CHAR_VIP` | 6 | [core.hpp:60](src/config/core.hpp#L60) |
| `@rates` com bônus, `@showrate` | `vip_disp_rate` | 1 | atcommand.cpp:8851 |
| `@vip <tempo> <char>` (GM), `vip_status()` / `vip_time()` (script) | — | — | script.cpp:28496 |

> 🔑 **`pc_isvip` não é consultado em nenhum ponto do sistema de permissão de atcommand.**
> O VIP nativo é 100 % rates/storage/slots — **não libera comando nenhum**.
> Expandi-lo para isso exigiria patchar `atcommand.cpp`.

#### Arquitetura decidida: híbrido

São dois problemas distintos e devem ser resolvidos separadamente.

**Comandos VIP → por script.** Nada de C++. `bindatcmd` num NPC + checagem no topo do handler:

```c
OnAtcommand:
    if (!vip_status(VIP_STATUS_ACTIVE)) {   // ou:  if (#vip_expire < gettimetick(2))
        dispbottom "Comando exclusivo para VIP.";
        end;
    }
```

Controle comando a comando, permite tiers (bronze/ouro) e não recompila.
**É por aqui que o [`@restock`](#21-restock--exclusivo-vip-decidido) da fase 2.1 é gateado.**

**Rota descartada:** criar um grupo VIP em [conf/groups.yml](conf/groups.yml). Não existe buildin
`setgroupid` (só `getgroupid`), então a promoção/rebaixamento teria que sair via `@adjgroup` — e grupo
carrega semântica de GM. Fácil de virar exploit.

**`VIP_ENABLE` (🔴 recompila) — só se quisermos os bônus da tabela acima.** Num servidor 500x, +50 % de EXP
é irrelevante; o que de fato vende é **storage maior e slots de char extras**. Avaliar por esse critério.
As duas coisas convivem: com o nativo ligado, `vip_status()` já funciona como gate nos scripts.

**Tarefas**
- [ ] Definir o pacote VIP (o que entra além de `@restock` e sala VIP)
- [ ] Escolher a fonte de verdade do prazo: `vip_time` nativo × variável de conta `#vip_expire`
- [ ] NPC/comando de consulta de prazo para o jogador
- [ ] Rotina de expiração: revogar acessos e **matar timers pendentes** (ver 2.1)
- [ ] Só se optarmos pelo nativo: descomentar `VIP_ENABLE`, recompilar, configurar
      [conf/battle/](conf/battle/), conferir `login.vip_time` no MariaDB ([sql-files/](sql-files/)),
      `@vip` em [conf/groups.yml](conf/groups.yml)

### 3.2 Vote4Points 🔵🟡
- [ ] Escolher engine web (Flux CP / FluxCP-Renewal / painel próprio) — ver [website_info.md](website_info.md)
- [ ] Tabela de pontos + callback dos sites de voto (RMS, XtremeTop100, GTOP100)
- [ ] NPC de troca de pontos → VIP time / itens / cosméticos
- [ ] Anti-abuso: cooldown por IP + por conta

---

## Fase 4 — PvP e conteúdo competitivo

### 4.1 Battlegrounds 🟢🔵
**Nativo já presente:** sistema de fila moderno ([battleground.cpp:33](src/map/battleground.cpp#L33)),
[db/battleground_db.yml](db/battleground_db.yml), [conf/battle/battleground.conf](conf/battle/battleground.conf),
e os modos em [npc/battleground/](npc/battleground/) — Flavius, KVM, Tierra.

- [ ] Habilitar e testar os 3 modos nativos primeiro (custo baixo, valida o pipeline)
- [ ] Loja de badges + balance dos itens de BG em pre-re
- [ ] Ranking de BG (tabela SQL + NPC de consulta)

#### ExtendedBG (xEasycore) — analisado, **diff descartado**

Fonte: <https://github.com/xEasycore/ExtendedBG> — cópia local em `BG-ANALISAR/` (gitignorada).
Conteúdo: diff de 113 KB (**+2586 / −141**, 23 arquivos de `src`/`conf`), 11 scripts de NPC,
sprites/textures de client, 13 emblemas.

**Traz:** 10 modos contra os 3 nativos — Conquest, FFA, Rush, Flavius CTF/SC/TD, Tierra Boss/DOM/EoE/TI.
Mais 26 buildins, 5 atcommands (`@listenbg`, `@order`, `@leader`, `@reportafk`, `@bgskill`) e 4 mapflags
(`MF_NOECALL`, `MF_BG_CONSUME`, `MF_WOE_CONSUME`, `MF_BG_TOPSCORE`).

**Por que o `.diff` não serve** (janeiro/2020):

1. **Colide com o BG queue oficial.** O rAthena implementou a fila própria *depois* desse fork. O repo já tem
   `bg_queue_on_ready`, `clif_bg_queue_apply_result` e [db/battleground_db.yml](db/battleground_db.yml).
   O ExtendedBG traz os dele (`bg_queue_create`, `bg_queue_join`, `bg_queue2team`, `bg_queue_checkstart`) —
   mesma responsabilidade, arquitetura incompatível. E `bg_create` já existe em
   [script.cpp:28414](src/map/script.cpp#L28414) com assinatura `"sii??"`; o ExtendedBG redefine como
   `"siiiss"` — colisão direta de símbolo.
2. **API antiga.** 121 ocorrências de `struct map_session_data` no diff; nosso
   [battleground.cpp](src/map/battleground.cpp) tem **zero** (o rAthena migrou para classe). Idem `int` → `int32`.
   Praticamente todo hunk falha no contexto.

**Veredito: é reescrita, não port.** Aplicar hunk a hunk deixaria dois sistemas de fila brigando.

**O que aproveitar**
- [ ] Os **11 scripts de NPC** em `BG-ANALISAR/ExtendedBG/npc/` — o valor real está aqui (lógica de gameplay
      de cada modo). Servem como especificação de regras mesmo onde não rodarem direto.
- [ ] Assets de client (skull sprites, emblemas, `idnum2item*`) — reaproveitáveis integralmente
- [ ] Reimplementar 1 modo escolhido sobre o BG queue **atual**; os buildins que faltarem
      (`bg_reward`, `bgannounce`, `bg_team_updatescore`) são pequenos e se escrevem do zero em `src/custom/`

### 4.2 WoE 🟡
- [ ] [woe_controller.txt](npc/custom/woe_controller.txt) já está no repo — configurar horários e castles
- [ ] Recompensas de WoE + anúncio automático

### 4.3 Eventos 🟡
- [ ] Habilitar de [npc/custom/events/](npc/custom/events/): devil_square, mvp_ladder, mushroom_event, disguise
- [ ] Agendador automático de eventos

---

## Fase 5 — Infra e operação

- [ ] Backup automático do volume MariaDB (cron + retenção)
- [ ] Painel de controle web + registro de conta
- [ ] Logs e antifraude: revisar [conf/log_athena.conf](conf/log_athena.conf)
- [ ] Estratégia de merge com upstream `rathena/rathena` (manter custom em `src/custom/` e `db/import/`
      para reduzir conflito)
- [ ] Ambiente de teste separado do de produção

---

## Ordem sugerida

1. **1.1 Random Options** — maior impacto, custo baixo, zero recompilação
2. **2.3 QoL** — habilitar o que já está no repo
3. **2.1 @restock** — implementar com o gate VIP escrito e desligado por flag
4. **4.1 BG nativo** — validar os 3 modos oficiais
5. **3.1 VIP** — define o pacote e **liga o gate do @restock**
6. **2.2 Sala VIP** — depende do gate da 3.1
7. **3.2 Vote4Points** — depende do painel web
8. **1.2 Enchant** e **4.1 reescrita de modo de BG** — os mais caros, por último

## Decisões travadas

| # | Decisão | Onde |
|---|---|---|
| 1 | `@restock` é **exclusivo VIP** — é a principal feature de conversão do pacote | [2.1](#21-restock--exclusivo-vip-decidido) |
| 2 | Comandos VIP saem **por script** (`bindatcmd` + `vip_status()`), não por patch em `atcommand.cpp` nem por grupo em `groups.yml` | [3.1](#31-vip) |
| 3 | Base do `@restock`: versão do **coiselves** (tópico 127084), com 3 correções obrigatórias | [2.1](#21-restock--exclusivo-vip-decidido) |
| 4 | `.diff` do **ExtendedBG descartado**; aproveitar só os scripts de NPC e os assets | [4.1](#extendedbg-xeasycore--analisado-diff-descartado) |
| 5 | Aplicação global de Random Options pela **rota B** (patch em `mob_setdropitem_option`) | [1.1](#11-random-options-bônus-aleatórios-em-item-) |

**Pendentes:** headgear/acessório recebem Random Options? · `VIP_ENABLE` nativo vale a recompilação?

## Convenções

- Dados custom em `db/import/` (nunca editar `db/pre-re/` direto) → merge com upstream sem conflito
- C++ custom em `src/custom/` (`atcommand.inc`, `script.inc`, `defines_pre.hpp`)
- NPCs custom em `npc/custom/`, registrados em `npc/scripts_custom.conf`
- Alterações de conf em `conf/import/`
