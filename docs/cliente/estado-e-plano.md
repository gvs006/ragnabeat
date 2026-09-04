# Estado do cliente

> A tradução tem documento próprio: **[../traducao.md](../traducao.md)**.
> O patcher tem o seu: **[patcher.md](patcher.md)**.

## ⚠ O IP DA TAILNET VAI MUDAR — e ele está compilado no .exe

Atualizado em 03/set/2026, com a **0.0.11**, a primeira versão entregue a
testers. Ela é distribuída pelo Thor Patcher, pela tailnet, e tudo aponta para
**100.76.66.99** — o endereço desta máquina no Tailscale.

Esse endereço não é estável. Ele muda se a máquina sair e voltar para a
tailnet, se o servidor trocar de host, ou quando isso virar domínio público.
Quando mudar, **não basta editar o `clientinfo.xml`**: o cliente 2025 acha o
login numa tabela em `.rdata`, compilada dentro do binário. Trocar só o XML
deixa o tester preso em "Please wait" sem nada no log do servidor.

A lista completa dos cinco lugares e a receita estão em
**[patcher.md](patcher.md#-o-ip-muda-leia-isto-antes-de-qualquer-outra-coisa)**.

O `build.py` agora **barra o build** se algum exe do tamanho do cliente não
contiver o endereço do `clientinfo.xml` que vai junto. A checagem nasceu de um
caso real: um dos exes secundários entrou na 0.0.11 ainda com `127.0.0.1`,
porque só o principal era conferido.

> **Rename de 03/set/2026:** o servidor passou a se chamar **Midgard Eternal**.
> O cliente é `MidgardEternal.exe`, o patcher é `MidgardPatcher.exe` e o build
> sai em `MidgardEternalProdV<versao>`. O título da janela do jogo ficou em
> **"Midgard"**, e não no nome completo, porque a string mora no binário com
> apenas 9 caracteres de espaço; o nome inteiro exige rebuild no WARP com
> `$customWindowTitle`.

Atualizado em 08/ago/2026. Este arquivo é a fonte da verdade — se o contexto da
conversa se perder, comece por aqui.

---

## 1. O que JÁ ESTÁ FUNCIONANDO

Cliente conecta, entra no jogo, sem erro de lua, com itens em português.

| Componente | Estado |
|---|---|
| Cliente | `MidgardEternal.exe` na pasta de desenvolvimento (hoje `C:\RagnaClient\RagnaBeat.Dev`, era `KRO-NEW`) — Ragexe 2025-04-16 (build 2025-04-10) |
| Base para rebuild | `BASE_2025-04-16_limpo.exe` (14.987.776 bytes após patch) |
| Patcher | `C:\RagnaClient\DEVTOOLS\WARP-2025` |
| `data.grf` | 4024 MB, v2, full client 2025-04-16 |
| `en.grf` | tradução inglesa, prioridade 0 |
| Servidor | rAthena pre-renewal, `PACKETVER 20250416` em `src/custom/defines_pre.hpp` |
| Docker | portas 6900, 6121, 5121 **e 6951→6900** |
| Itens PT-BR | **5.296 gerados** em `SystemEN\itemInfo_C.lua` (85,8% do `db/pre-re`) |

## ✅ ACENTUAÇÃO: RESOLVIDA em 10/ago/2026

Eram **7 constantes cp949 compiladas no binário** — o cliente converte texto para
Unicode ele mesmo, e o codepage estava fixo em 949. Trocadas para 1252 pelo passo 3
do `pos-warp.py`. Causa, offsets e o que foi descartado no caminho:
**[acentuacao.md](acentuacao.md)**.

O diagnóstico abaixo, de 08/ago, está **superado** — fica registrado porque descreve
corretamente o *sintoma* e porque a conclusão a que levou ("é o build, pergunte à
comunidade") era errada por um motivo instrutivo: nenhum patch do WARP alcança essas
constantes.

<details>
<summary>Diagnóstico original de 08/ago (superado)</summary>

### ⚠ ACENTUAÇÃO: NÃO FUNCIONA NESTE CLIENTE (medido em 08/ago 18:40)

Teste conclusivo com os dois encodings no mesmo arquivo, itens 501 e 502:

| Item | Bytes gravados | Como renderizou |
|---|---|---|
| 501 (cp1252) | `e7 e3` | `a-? c-? a-? e-?` — vira `?` |
| 502 (UTF-8) | `c3 a7` | `a-찿 c-쐴` — vira ideograma coreano |

**Comportamento idêntico ao cliente kRO de 2021.** O cliente lê em cp949 duplo-byte:
`c3 a7` é par válido → glifo coreano; `e7` sozinho não forma par → `?`.

Ser build regional (basesdk/iapsdk) **não bastou**. A premissa da migração não se
confirmou.

**O que ainda não foi explicado**: o ThanatosRO usa este mesmo binário (`.text`
idêntico byte a byte, verificado) e exibe acentos. Existe uma configuração que
replica isso e não foi encontrada.

Candidatos:
1. ~~`CustomFontCharset = ANSI`~~ — **testado em 08/ago 18:50, NÃO resolve.**
   Resultado idêntico ao teste sem ele: `?` no cp1252, ideograma no UTF-8.
2. Algum lua nos GRFs do ThanatosRO que sobrescreve fonte/charset (GRFs encriptados,
   não foi possível ler)
3. O patcher Odin que eles usam
4. Alguma fonte customizada empacotada por eles

**Conclusão da investigação de dois dias**: nem o cliente kRO 2021 nem o regional
2025 renderizam acentos latinos, nem com cp1252 nem com UTF-8, nem com
`CustomFontCharset=ANSI`, `AlwaysAscii`, `FixFontsCharset`, `_setmbcp(1252)`,
langtype ou servicetype. Todos leem em cp949 duplo-byte.

O ThanatosRO usa o **mesmo binário** e funciona. A diferença está em dados ou
configuração que não conseguimos observar (GRFs deles são encriptados).

**Recomendação**: perguntar na comunidade BR. A pergunta agora é precisa —
*"como fazer o Ragexe 2025 renderizar acentos?"* — e alguém que roda servidor BR
responde de cabeça.

</details>

## ⚠ BLOQUEIO ATUAL: login intermitente

> 📄 O fluxo completo do web auth token — geração, entrega, validação, o que quebra ao
> desligar e como religar — está documentado em **[../auth-token.md](../auth-token.md)**.
> As implicações de segurança estão em **[../seguranca.md](../seguranca.md)**.

Sintoma: "Please wait" após informar login e senha.

**Causa identificada e corrigida**: `use_web_auth_token: yes`. O cliente busca o token
por HTTP no web-server; a porta 8888 do host está ocupada pelo **OpenTelemetry
Collector**, e o rAthena foi publicado na 8889. Desligado via
`conf/import/login_conf.txt` → o login passou a funcionar (confirmado no log:
`'deve ser' logged in`, inventário com 51 itens).

**Mas voltou a travar** após o rebuild com `CustomFontCharset`. Estado no momento:
- exe com os 6 IPs e todos os patches ✅
- 5 portas abertas no host ✅
- `use_web_auth_token: no` ativo ✅
- nenhum personagem preso online, conta `state 0` ✅
- `login.web_auth_token_enabled = 0` ← não investigado
- o servidor **não registra a tentativa** — o cliente não chega nele

Próximo passo sugerido: monitorar TCP durante a tentativa (`monitor3.ps1`, 10 min em
segundo plano) para distinguir entre "não abre socket" e "abre e cai".

---

## 2. Os dois patches manuais que somem a cada rebuild

Rode **`pos-warp.bat`** depois de todo build no WARP. Ele:

1. Redireciona 7 endereços da Gravity para `127.0.0.1` (offsets `0x00C28520`–`0x00C285E8`)
2. Corrige o separador do caminho do itemInfo para contrabarra

Sem o passo 1 o cliente trava em "Please wait". Detalhes em `LEIA-ME.md`.

---

## 3. Ferramentas prontas nesta pasta

| Arquivo | Uso |
|---|---|
| `pos-warp.py` / `.bat` | reaplica o que o WARP desfaz |
| `validar-iteminfo.py` | confere sintaxe do itemInfo_C antes de abrir o cliente |
| `LEIA-ME.md` | documentação do cliente, patches obrigatórios e proibidos |

Em `C:\RagnaClient\DEVTOOLS\PTBR\`:

| Arquivo | Uso |
|---|---|
| — | as ferramentas de tradução estão listadas em [../traducao.md](../traducao.md) |

---

## 4. Tradução

Movida para **[../traducao.md](../traducao.md)** — estado por camada, fontes,
ferramentas, armadilhas e pendências, em documento próprio.

---

## 5. Preview de visual — RESOLVIDO em 12/ago/2026

O preview aparece na **janela de descrição do próprio item**, não dentro da
loja. E não é patch de binário: o exe delega a decisão ao Lua.

Em `0x00C11CF8` o exe empurra a string `IsEffectHatItem` e chama a função Lua de
mesmo nome, definida em `hateffectinfo/hateffect_f.lub`:

```lua
function IsEffectHatItem(itemID)
  for k, v in pairs(effectHatItemTable) do
    if v == itemID then return true end
  end
  return false
end
```

O botão só é criado quando isso devolve `true`. A `effectHatItemTable` original
(`hateffectinfo/effecthatitemtable.lub`, compilada no GRF) tem **126 IDs** — só
os "hats de efeito" oficiais. Nossos 1.020 visuais não estavam lá, e era essa a
única razão de não haver preview neles.

**Solução:** [gen-preview-visuais.py](gen-preview-visuais.py) reescreve a tabela
como a união dos 126 originais com os IDs de `db/ragnabeat_visuais.yml` — 1.140
no total, 1.014 acrescentados (6 já estavam). Sai como Lua em texto puro na
pasta solta, que vence o GRF pelo `DataFolderFirst`, igual ao `pcjobname.lub`.

Os 126 originais são preservados de propósito: tirar um apagaria o preview de um
item que hoje funciona.

**Por que é seguro:** varri os 471 `.lub` de `luafiles514` e a
`effectHatItemTable` é lida **só** pelo `IsEffectHatItem`. Quem controla
renderização de efeito de chapéu é a `hatEffectTable`, que é outra coisa — um ID
a mais aqui não liga efeito nenhum, só o botão.

**Custo: zero no exe.** Não precisou de WARP nem de `pos-warp.py`; é só o
`build.py`. O patch `NoEquipPreview` do WARP (que *desligaria* isso) não está no
nosso perfil, então a feature sempre esteve ligada — faltava o dado.

> **Diagnóstico anterior, errado, registrado para não voltar:** cheguei a
> concluir que faltavam os patches `PreviewInShop` e `PreviewInTrader` do WARP.
> Eles existem e fazem outra coisa — põem preview *dentro da janela de loja*.
> Continuam disponíveis se um dia quisermos isso também, mas não eram o caso
> aqui, e teriam custado um rebuild do exe à toa.

## 6. Regras que não podem ser esquecidas

1. **Encoding cp1252 (ANSI)** em tudo que o cliente lê. UTF-8 quebra os acentos.
   O `resourceName` dos itens é cp949 e deve ser copiado byte a byte, nunca reencodado.
2. **Escapar aspas** ao gerar Lua. Uma aspa literal numa descrição derruba o arquivo inteiro.
3. **Fechar o cliente** antes de rodar scripts que gravam no `.exe`.
4. **Fonte do WARP** sempre um `BASE_*.exe` limpo, e clicar em recarregar ao trocar.
5. **`NoPacketEncr` e `DataFolderFirst`** são `recommend: no` — somem no "select recommended".
6. Editar poucos itens e testar. Um erro de sintaxe derruba o itemInfo todo.

---

## 7. Backups e o que pode ser descartado

- `C:\RagnaClient` (7,3 GB) — setup antigo de 2021, intocado, serve de referência
- `_exes_antigos\` na pasta de desenvolvimento — descartáveis
- `RagnaBeat-BKP.exe` — rede de segurança do cliente que funciona
- `C:\RagnaClient\_removed_20260806\` — backups dos experimentos

---

## 8. Fila de trabalho no cliente

O que só sai com GRF novo e release no Thor Patcher. Cada item diz **onde**
mexer — o custo aqui quase sempre é achar o arquivo, não editar.

### 8.1 Ícones próprios de VIP e ROTD — *contornado, mas provisório*

Os dois ícones já **aparecem** na barra da direita, sem nenhuma alteração de
cliente. O atalho foi apontar dois `SC_` inertes para EFST que já têm arte e
texto em português — está tudo explicado em
[`db/import/status.yml`](../../db/import/status.yml):

| | `SC_` usado | EFST emprestado | Arte | O balão diz hoje |
|---|---|---|---|---|
| VIP | `SC_HAT_EFFECT` | `EFST_KINGS_GRACE` | `KINGS_GRACE.TGA` (brasão dourado) | "Graça Real / Imóvel / Imune a ataques" — **errado** |
| ROTD | `SC_TIME_ACCESSORY` | `EFST_AID_PERIOD_PLUSEXP` | `EXP_G.TGA` ("EXP" com setas) | "Bônus de EXP / Mais ganho de EXP de Base e Classe" — correto |

Os dois `SC_` foram escolhidos porque **não aparecem em nenhum `.cpp` de
`src/map` fora do próprio enum** — são efeitos cosméticos de chapéu de renewal.

**O que falta para ficar definitivo**, e é sempre a mesma receita de três peças:

1. a arte em `data\texture\effect\<nome>.tga` — **32×32, TGA 32 bits**
   (os do kRO têm 4140 bytes; `gogi.tga` e `exp.tga`, com 3116, são 24 bits)
2. `data\luafiles514\lua files\stateicon\stateiconimginfo.lub` — a linha
   `StateIconImgList[EFST_IDs.EFST_X] = { "<nome>.tga", PRIORITY_* }`
3. `data\luafiles514\lua files\stateicon\stateiconinfo.lub` — o balão

> **Limite que não tem contorno:** o balão **não** mostra número vindo do
> servidor. O `stateiconinfo.lub` deste cliente tem 678 `%s` (o relógio) e
> **zero `%d`** — não existe campo numérico. Por isso a porcentagem do dia mora
> no título da sala de chat do NPC ROTD, e não no ícone. O servidor de
> referência faz igual.

Se um dia forem precisos EFST realmente novos (e não emprestados), eles têm de
existir nos **dois** lados: no enum de [`src/map/status.hpp`](../../src/map/status.hpp)
e no `efstids.lub` do cliente. O `efstids.lub` tem metatable com
`__newindex = error`, então chave nova vai **dentro** do literal — ver a
armadilha correspondente em [`../traducao.md`](../traducao.md).

### 8.2 Trocar as telas de fundo

Login, seleção de personagem e tela de criação. As texturas são
`data\texture\<pasta de UI em cp949>\login_interface\*.bmp` e `esc_*`.

Metade do trabalho já está feito: o
[`gen-texturas-ptbr.py`](gen-texturas-ptbr.py) extrai, tria e instala, e o
[`grf_listar.py`](grf_listar.py) já decifra GRF encriptado. O que sobrou são os
**30 arquivos sem par** (8 divergem em dimensão/bpp, 22 só existem no kRO 2025)
— a lista nominal sai em `DEVTOOLS\PTBR\_extraido\texturas\TRIAGEM.txt` a
cada execução. Detalhe em [`../traducao.md`](../traducao.md#2-texturas-de-login-e-menu-esc--feito-o-que-dava).

Trocar por arte própria é o mesmo caminho: mesmo nome, mesma dimensão, mesmo
bpp. Dimensão diferente o cliente aceita mal — foi o que travou `warning.bmp`
(1920×1440 aqui contra 640×480 no LATAM).

### 8.3 Mapas custom

Um mapa novo exige as duas metades, e a que costuma ser esquecida é a do servidor:

- **cliente:** `.gat`, `.gnd`, `.rsw` em `data\`, o nome em
  `System\mapInfo_true.lub` (senão a tela mostra o nome interno cru), e o
  minimapa em `data\texture\<UI>\map\<mapa>.bmp`
- **servidor:** a linha em `db/map_index.txt`, o `npc: ...mapflag` se precisar,
  e sobretudo o **mapcache**. Sem regerar o `db/import/map_cache.dat` o
  map-server aborta no boot — o log já mostra hoje
  `Unable to open map cache file db/import/map_cache.dat` quando ele falta.

Regra prática: **o mapcache é gerado a partir dos `.gat` do cliente**, então a
ordem é sempre cliente primeiro, mapcache depois, servidor por último.

### 8.4 Mobs custom

O sprite é a parte cara. Cada mob precisa de:

- `data\sprite\<pasta de monstro em cp949>\<nome>.spr` e `.act`
- a entrada em `data\luafiles514\lua files\datainfo\npcidentity.lub` (o id)
  e em `jobname.lub` (id → pasta do sprite)
- do lado do servidor, a linha no `db/import/mob_db.yml` com o mesmo `Id`

O caminho barato, e o que já está em uso, é **reaproveitar sprite existente com
paleta diferente** — é assim que os [`champions.txt`](../../npc/custom/champions.txt)
funcionam hoje, sem tocar no cliente. Só vale desenhar sprite novo quando a
silhueta precisar ser diferente.

> Nome de mob vem do **servidor** (campo `Name:` do `mob_db`), não do cliente —
> ver [`../traducao.md`](../traducao.md#a-fonte-que-faltava-para-os-mobs).

### 8.6 Nomes de Bônus Aleatório em PT-BR — pronto para instalar

**Hoje o jogador lê coreano.** O nome que aparece na linha do B.A. do item sai
de `data\luafiles514\lua files\datainfo\addrandomoptionnametable.lub`, e o
nosso é o do kRO puro. As curtas até passam (`STR + %d`, `MHP + %d%%`), mas as
longas são cp949:

```
ATTR_TOLERACE_FIRE   ->  È­¼Ó¼º °ø°Ý¿¡ ´ëÇÑ ³»¼º %d%% Áõ°¡
VAR_PLUSASPDPERCENT  ->  °ø°Ý¼Óµµ Áõ°¡(°ø°Ý ÈÄµô·¹ÀÌ %d%% °¨¼Ò)
```

Ou seja, toda resistência elemental e toda velocidade de ataque que o servidor
sorteia hoje aparecem ilegíveis.

**A tradução já existe e é drop-in.** O LATAM tem o arquivo pronto em
`DEVTOOLS\PTBR\latam\luafiles514\lua files\datainfo\addrandomoptionnametable_ptbr.lub`:

```
VAR_MAXSPPERCENT              SP máx. +%d%%
VAR_PLUSASPD                  Velocidade de ataque +%d
VAR_PLUSASPDPERCENT           Velocidade de ataque +%d%%
ATTR_TOLERACE_FIRE            Resistência a Fogo +%d%%
DAMAGE_PROPERTY_SAINT_TARGET  Dano físico contra Sagrado +%d%%
RACE_DAMAGE_INSECT            Dano físico contra Inseto +%d%%
CLASS_DAMAGE_BOSS_TARGET      Dano físico contra Chefes +%d%%
```

**A armadilha das constantes foi conferida e está limpa.** A regra de
[`../traducao.md`](../traducao.md) manda cruzar o que o arquivo do LATAM indexa
com o que o nosso `enumvar.lub` define — `tabela[nil]` é erro em Lua e derruba
o arquivo inteiro. Medido em 03/set/2026:

| | |
|---|---|
| constantes na tabela PT-BR do LATAM | 251 |
| constantes na nossa tabela kRO | 251 |
| definidas no nosso `enumvar.lub` | 254 |
| **no PT-BR e sem definição aqui** | **0** |

É trocar o arquivo, sem remendo. Só falta o release.

> Diferente do balão de ícone de status (8.1), esta tabela **aceita número do
> servidor**: o `%d` é preenchido com o valor sorteado. São mecanismos
> diferentes do cliente — não conclua a limitação de um a partir do outro.

### 8.5 Onde tudo isso vira release

Nada acima chega ao tester sem passar por
[`build.py`](build.py) e pelo Thor — receita em
[`patcher.md`](patcher.md) e [`build-release.md`](build-release.md). O `build.py`
**barra o build** se o exe não contiver o IP do `clientinfo.xml` que vai junto;
não contorne essa checagem, ela nasceu de um release quebrado.
