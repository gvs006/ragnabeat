# RagnaBeat — cliente 2025-04-16

Documentação do cliente e dos problemas resolvidos até aqui. Escrita em 08/ago/2026.

---

## Resumo da configuração

| | |
|---|---|
| Executável base | `BASE_2025-04-16_limpo.exe` (build 2025-04-10, desempacotado) |
| Origem do exe | github.com/hiphop9/ROClient_en → `2025-04-16_Ragexe_1744255909_fix.exe` |
| Full client | 3,8 GB, link no README do mesmo repo |
| `data.grf` | 4024 MB, formato v2 `Master of Magic`, 215.047 arquivos |
| `en.grf` | 6 MB, tradução inglesa, prioridade 0 no `DATA.ini` |
| Patcher | warp2025 (`DEVTOOLS/WARP-2025`) |
| Servidor | rAthena `PACKETVER 20250416`, pre-renewal |

---

## Rotina após cada build no WARP

1. Fonte (`Source`) sempre o **`BASE_2025-04-16_limpo.exe`**, nunca um exe já patcheado.
   Ao trocar o campo, use o botão de **recarregar** — o WARP não recarrega sozinho e
   continua usando o binário anterior em memória.
2. Confira que o resultado tem **14.987.776 bytes**. Se der 15.075.840, a fonte estava
   errada (é o exe 2025-06-04).
3. Renomeie para `RagnaBeat.exe`.
4. **Feche o cliente** se estiver aberto.
5. **Rode `python pos-warp.py RagnaBeat.exe`** — sem nenhuma flag.

> ⚠ **Não passe `--setmbcp`.** A flag existe no script e continua documentada,
> mas **não use**. Ela foi testada in-game em 12/ago/2026 (build 0.0.8) e **não
> resolveu** as mensagens sem acento; em troca, mexe no codepage do CRT inteiro,
> o que põe em risco os nomes de arquivo cp949 de dentro do GRF. Foi revertida —
> o estado bom é o de **6** constantes trocadas, não 7. O porquê, e o que o teste
> negativo ensinou, em [acentuacao.md](acentuacao.md).
>
> As mensagens automáticas do chat **seguem sem acento**. É um problema aberto,
> que esta rotina não resolve: a conversão usa um codepage 949 que não é nenhuma
> das 7 constantes conhecidas.

O passo 5 é obrigatório. Sem ele o cliente volta a travar em "Please wait" **e os
acentos param de renderizar** — o `pos-warp.py` reaplica as duas coisas.

O script termina com `>>> PRONTO PARA USAR` quando está tudo certo. Se algum item
aparecer marcado com `!!`, ele diz qual.

> **Se der `PermissionError`**: o cliente está aberto. O Windows não deixa sobrescrever
> um `.exe` em execução, nem rodando como administrador. Feche e rode de novo.

---

## Patches obrigatórios no WARP

O preset "select recommended" **não** marca estes. Marque na mão:

| Patch | Por quê |
|---|---|
| `NoPacketEncr` | O servidor loga `Packet Obfuscation: Disabled`. Sem este patch o cliente criptografa e é rejeitado. Fica no grupo **DISABLE ENCRYPTION**, com o título "Disable Map packet encryption" — não tem "packet key" no nome. |
| `DataFolderFirst` | Faz a pasta `data\` vencer os GRFs. Necessário para os overrides de lua e para o `clientinfo.xml`. |
| `CustomItemInfoLub` | Aponta o itemInfo para a tradução. Valor: `SystemEN\itemInfo.lua` — **com contrabarra**. Com barra normal o cliente dá `Invalid argument`. |

### Ícone do cliente

O grupo **ENABLE ICON** é `mutex` — só um dos dois pode estar marcado:

| Patch | O que faz |
|---|---|
| `Restore Inbuilt App icon` | usa o ícone **embutido no exe**. É `recommend: yes`, então entra sozinho no "select recommended" |
| `Customize App icon` | usa um `.ico` seu, gravando-o dentro do exe |

Um `.ico` solto na pasta do cliente **não faz nada** — nada o lê em runtime. Para um
ícone próprio, desmarque o `Restore Inbuilt` e marque o `Customize`. Para Win7+ o
patch recomenda um `.ico` com **256x256 32bit mais um 16x16**; só com 32x32 o ícone
sai borrado na barra de tarefas.

### Patches que NÃO devem ser marcados

| Patch | O que acontece |
|---|---|
| `HKLMtoHKCU` | Trava o cliente: 100% de CPU, sem janela. Descoberto por bisect de 81 bytes. |
| `EnableEotFonts` | Prende o cliente numa fonte coreana embutida e torna as `.eot` obrigatórias — sem elas nem abre. |
| `FixFontsCharset` | A tabela que ele instala sai zerada e ainda sequestra a leitura do `CustomFontCharset`. |
| `NoWalkDelay` | **Faz o clique de skill de chão virar também comando de andar.** Ver abaixo. |
| `CustomFontCellHeight` | **Tela branca e fecha sozinho.** Testado em 04/set/2026 com o valor certo e com o errado — quebra dos dois jeitos neste build. |

### Patches de tamanho de fonte — o que foi testado

Em 04/set/2026, caçando a diferença de fonte para o ThanatosRO:

| Patch | Resultado |
|---|---|
| `CustomFontHgtLimits` **14/14** | ✅ o que usamos. Com min = max não é limite, é trava: toda fonte sai em 14 |
| `CustomFontHgtLimits` 12..16 | abre, mas o nick no hover continua estranho |
| `CustomFontHeight` 16 | abre — **gigante** |
| `CustomFontHeight` 18 | nem testado, o 16 já estourava |
| `CustomFontHeight` 14 | abre — **descaracteriza**, "muito errado" |
| `CustomFontCellHeight` 14 | ❌ **tela branca**, fecha sozinho |
| `CustomFontWeight` 700 | ❌ tela branca (mas a codificação do input estava errada; não foi refeito) |
| `CustomNormalFontWeight` 500 | não chegou a ser avaliado |

**Conclusão:** os patches de altura são beco sem saída. O `14/14` continua sendo
o melhor que temos, e a diferença que sobra para o ThanatosRO não é tamanho.

> ⚠ **A codificação do input no perfil é por TIPO, e errar dá tela branca.**
> Copie sempre de um input que já funciona, nunca invente:
>
> | Input | `data:` | Bytes |
> |---|---|---|
> | `$fontHgtLimitL` / `$fontHgtLimitH` | `'0e'` | **1** (tamanho de fonte) |
> | `$fontHgtOff` | `'01'` | **1** |
> | `$chatFloodLimit` | `'0a'` | **1** |
> | `$walkDelay` / `$walkDelay2` | `'9600'` | **2** (uint16, little-endian) |
> | `$newFont` | `'417269616c00'` | string + `\0` |
>
> Escrever `'0e00'` (2 bytes) num campo de 1 byte faz o WARP gravar lixo, o
> `CreateFont` falhar e o cliente morrer antes de desenhar a tela.

### `NoWalkDelay` — a armadilha que custou uma investigação inteira

**Sintoma:** ao usar Nevasca (ou Muralha de Fogo, Barreira Sagrada, Tempestade
de Meteoros — qualquer skill de chão), o personagem **caminha até a célula** e a
skill sai lá, parecendo sair "nos pés dele".

O patch faz o clique que lança a skill virar **também** um comando de andar para
a mesma célula. A própria descrição dele avisa — *"client may likely send
more/duplicated packets"* — e ele é `recommend: no`.

O servidor amplifica: com o personagem já andando, o ramo `stepaction`
(`src/map/unit.cpp:2679-2688`) **adia** a skill até a caminhada aproximar.

É bug conhecido, com Storm Gust citado nominalmente:
[rathena#2046](https://github.com/rathena/rathena/issues/2046),
[NEMO#152](https://github.com/Neo-Mind/NEMO/issues/152),
[board 112192](https://rathena.org/board/topic/112192-character-walks-after-using-a-ranged-insta-cast-skill/).

**O substituto:** o grupo **WALK DELAY** ("ATRASO DE CAMINHADA") é `mutex`.
Desmarque `Remove Walk Delay` e marque **`Customize Walk Delay`**, respondendo
**150** nas duas perguntas de valor. O padrão do cliente é 600; abaixo de 100 o
bug volta (NEMO#152). Corrigido assim em 02/set/2026.

### Os dois perfis agora são o MESMO arquivo

Existem dois caminhos com o mesmo nome, e isso já custou uma build inteira:

```
DEVTOOLS\WARP-2025\BASE_2025-04-16_limpo_PROFILE.yml
RagnaBeat.Dev\BASE_2025-04-16_limpo_PROFILE.yml
```

Em 04/set/2026 o conteúdo dos dois foi **igualado**, justamente para a escolha
deixar de importar. Se um dia divergirem de novo, o de `DEVTOOLS\WARP-2025\`
é o bom.

> ⚠ **O que aconteceu:** gerei uma build a partir do da raiz, que era de
> 10/ago. Saíram fora `CustomFontCharset`, `CustomFontHgtLimits` e
> `LoadKrExtSettings`, e entraram `AlwaysAscii` e `CallKoreaClientInfo`. O
> `CustomWalkDelay` voltou para o padrão do cliente (600 e 350) sem nenhum
> aviso — quem jogou sentiu o atraso na caminhada antes de alguém entender
> por quê.

**Como conferir que uma build saiu certa**, sem depender de memória: compare o
exe novo com um exe antigo que funcionava, ignorando as regiões que o
`pos-warp.py` altera depois. Duas medidas resolvem:

| Medida | Valor bom |
|---|---|
| bytes diferentes fora das regiões do `pos-warp` | **0** |
| bytes não-zero na seção `.xdiff` (`0x00E4AE00`–`0x00E4B200`) | **670** |

A `.xdiff` é onde o WARP injeta os trampolins dos patches. Patch faltando
aparece ali como código a menos, e foi assim que os três perdidos foram
achados — o perfil errado dava 651.

Valores de referência gravados no binário, úteis para conferir sem abrir o WARP:

| O que | Offset | Valor certo |
|---|---|---|
| `CustomWalkDelay` (1º) | `0x0085A859` | `150` (padrão do cliente: 600) |
| `CustomWalkDelay` (2º) | `0x0092B522` | `150` (padrão do cliente: 350) |
| `Zoom67Percent` (`FAR_DIST`) | `0x00BB20D8` | float `730.0` (limpo: `480.0`) |
| `CustomFontName` | — | família `Arial`, igual ao cliente LATAM |
| Título da janela | `0x00C0CD88` | `Midgard Eternal Ragnarok Onlne \| Gepard Shield 3.0` |

### O patch de zoom só levanta o teto — quem liga é o `/zoom`

O grupo **ZOOM OUT** é `mutex` e todas as opções escrevem o mesmo float
(`FAR_DIST`, `0x00BB20D8`):

| opção | FAR_DIST |
|---|---|
| sem patch | 480.0 |
| `Zoom25Percent` | 128.0 (*diminui*) |
| `Zoom50Percent` | 510.0 |
| **`Zoom67Percent`** | **730.0** — em uso |
| `Zoom75Percent` | 818.0 |
| `ZoomMax` | 1224.0 |

> ⚠ **O patch sozinho não faz nada visível.** O cliente só usa o alcance
> estendido com o modo `/zoom` ligado, e ele nasce **desligado**. Em
> 04/set/2026 isso custou uma investigação inteira: o float estava correto no
> binário, conferido byte a byte, e o zoom "não funcionava". Faltava o
> `/zoom`.
>
> Por isso `savedata-padrao\OptionInfo.lua` agora traz `CmdOnOffList["/zoom"]`
> e `OptionInfoList["/zoom"]` em `1`. O `Zoom75Percent` avisa que não funciona
> com Gepard Shield — não usamos Gepard, a menção no título da janela é isca.

### A fonte: `CustomFontName` some quando se troca a base do cliente

O perfil do cliente LATAM de 2021 tinha `CustomFontName` = **`Arial`**. O perfil
de 2025 nasceu sem ele, e a fonte passou a ser a embutida do cliente sem que
ninguém tivesse mexido em fonte. É ele que redireciona a família passada ao
`CreateFontA`.

Reposto em 04/set/2026. O par completo é `CustomFontName` (Arial) +
`CustomFontCharset` (ANSI) + `CustomFontHgtLimits` (14/14). A família precisa
existir no Windows do jogador — Arial, Tahoma e Verdana são as seguras.

### Dá para gerar o exe sem abrir a interface

`DEVTOOLS\WARP-2025\win32\WARP_console.exe` aplica um perfil sem GUI:

```
WARP_console.exe -using <perfil.yml> [-from <exe>] [-to <exe>]
```

O `from` e o `to` já vêm no próprio perfil, então na prática basta o `-using`.
Rode de dentro de `DEVTOOLS\WARP-2025\`, senão ele não acha `Patches/` e
`Inputs/`.

> ⚠ **Ele sobrescreve o `LastSession.yml` ao terminar.** Se a sua seleção boa
> estiver só na sessão e não num perfil salvo, ela se perde. Salve o perfil
> antes de rodar o console.

---

## O problema do "Please wait" — causa e solução

O cliente de 2025 **não usa o `clientinfo.xml` para descobrir o endereço do login**.
Ele tem uma tabela de endereços fixos em `.rdata` e usa o fluxo moderno de *agency
server* da Gravity.

Capturado com `Get-NetTCPConnection`, ele tentava:

```
52.79.57.79:6953   [SynSent]     ← servidor da Gravity, sem resposta
```

**Solução em duas partes:**

1. **Redirecionar os 7 endereços** — é o que o `pos-warp.py` faz, para o valor da
   constante `SERVIDOR` no topo dele. `127.0.0.1` só serve para testar nesta
   máquina; para outras pessoas tem que ser um endereço que elas alcancem
   (hoje o IP do Tailscale). Ver [infra-docker.md](../infra-docker.md).
   Ficam nos offsets `0x00C28520`–`0x00C285E8`, espaçados de 32 bytes.

2. **Publicar a porta 6951 no Docker** apontando para a 6900. O cliente deriva essa
   porta em código, não do XML. Já está no `docker-compose.yml`:

   ```yaml
   - "6951:6900"
   ```

Depois disso a captura mostra o caminho completo:

```
127.0.0.1:6121  [Established]    ← char server
127.0.0.1:5121  [Established]    ← map server
```

---

## Por que este cliente, e não outro

O objetivo era **acentuação PT-BR**, que os builds kRO não renderizam. Foram
eliminados, com medição direta no binário e na memória do processo: charset de fonte,
`AlwaysAscii`, `FixFontsCharset`, `CustomFontCharset`, `CallKoreaClientInfo`,
`_setmbcp(949→1252)`, langtype e servicetype.

> ⚠ **A conclusão abaixo estava errada.** Em 10/ago/2026 descobriu-se que a acentuação
> não depende da origem do build: são 7 constantes cp949 no `.text`, trocadas para 1252
> pelo `pos-warp.py`. Ver [acentuacao.md](acentuacao.md). O critério regional × kRO
> continua útil para *outras* coisas, mas não decide acentuação.

A diferença real está na **origem do build**. Clientes regionais importam
`basesdk.dll` e `iapsdk.dll` do `.rdata` com dezenas de funções — os kRO não têm.
O ThanatosRO usa um build assim, e é por isso que exibe acentos.

**Como identificar um candidato:**

```
basesdk/iapsdk importados de .rdata com 24 e 37 funcoes  ->  regional  ->  serve
ausentes, ou em .xdiff com 1-2 funcoes                   ->  kRO       ->  nao serve
```

O `2025-06-04` também é regional, mas produz erro de lua (`GetTableIntValueForC`) com
este `data.grf`, porque o `ExternalSettings` compilado do GRF é de 2024-08. Por isso
ficamos no par exato **exe 2025-04-16 + full client 2025-04-16**.

---

## Estrutura de arquivos

```
DATA.ini              0=en.grf  1=data.grf
data\                 overrides (vencem os GRFs via DataFolderFirst)
  clientinfo.xml      127.0.0.1:6900 — não é usado para o login, mas
  sclientinfo.xml     mantido por segurança
  luafiles514\...\service_korea\   ExternalSettings em texto puro, 99/70
System\               arquivos do full client (coreano)
SystemEN\             tradução inglesa
  itemInfo.lua        stub, encadeia para LuaFiles514\itemInfo.lua (20,7 MB)
  itemInfo_C.lua      itens custom — é aqui que a tradução PT-BR entra
```

---

## Executáveis

| Arquivo | O que é |
|---|---|
| `BASE_2025-04-16_limpo.exe` | base hexed, fonte de todo rebuild |
| `RagnaBeat.exe` | build em uso |
| `RagnaBeat2.exe` | versão que conectou pela primeira vez, sem tradução — rede de segurança |
| `_exes_antigos\` | descartados, incluindo o 2025-06-04 |

---

## Features do cliente sem suporte no servidor

O cliente 2025 traz features do kRO que **o rAthena não implementa**. A UI abre e
parece funcionar, mas nada acontece ao aplicar, porque o pacote não tem tratador
do outro lado.

| Feature | Evidência |
|---|---|
| **Damage Skin** de cash shop | O exe procura `Lua Files\DamageSkin\DamageSkinInfo` e `DamageSkinList`, e tem `GetDamageSkinName`, `DamageSkinSize`. No rAthena: **zero ocorrências** de `damageskin`/`damage_skin` em `src/`. Sem port conhecido (verificado em 10/ago/2026). Implementar exige pacotes em C++, concessão à conta e persistência — é feature, não configuração |

> **Não confundir com a aba "Damage Info"** da janela de Equipamento (Alt+Q), que
> escolhe o estilo dos números — Normal / Colorido / Palavras / Nada, e a posição.
> Essa é preferência de exibição, não item de cash shop, e o ThanatosRO a tem
> funcionando. Ela grava via web-server, que estava quebrado por dois motivos
> independentes — ver [auth-token.md](../auth-token.md).

> **12/ago/2026 — o `C:\RagnaClient\data.grf` sumiu da máquina.** Sobrou só o
> do `RagnaBeat.Dev`. A comparação abaixo fica registrada porque explica o
> histórico, mas hoje não há segundo GRF para consultar. Consequências:
> o `checar-sprite.py` continua funcionando (ele pula GRF ausente), e os 3
> sprites de Saiadim que só existiam lá — 20248, 31613 e o feminino do 20250 —
> **não têm mais fonte local**. Os 6 das Lendárias Asas de Demônio estão
> salvos: foram extraídos para `RagnaBeat.Dev\data\sprite\` antes.

## Os dois `data.grf` não têm o mesmo conteúdo

Descoberto em 11/ago/2026, investigando um `Cannot find File : sprite\...act`
in-game:

| GRF | Formato | Arquivos | Carregado por |
|---|---|---|---|
| `C:\RagnaClient\data.grf` | **v3** "Event Horizon", 4,2 GB | **268.764** | só o cliente antigo em `C:\RagnaClient` |
| `C:\RagnaClient\RagnaBeat.Dev\data.grf` | v2 "Master of Magic", 4,0 GB | 214.224 | o dev **e o build entregue aos jogadores** |

São **54 mil arquivos a menos** no que os jogadores recebem. O caso concreto
foram os sprites das "Lendárias Asas de Demônio" (item 5376): existem no de
produção, não existem no do build, e equipar o item abria uma caixa de erro do
cliente na cara do jogador.

**Antes de pôr qualquer item novo no servidor, rode:**

```
python docs/cliente/checar-sprite.py <id> [<id> ...]
```

Ele compara os GRFs disponíveis e marca `<<< FALTA NO BUILD` no que quebraria.

Para **lote** (centenas de itens), use o `docs/gerar-visuais.py`: ele monta um
índice do GRF uma vez só. O `checar-sprite.py` varre a lista inteira por item,
o que não termina acima de algumas dezenas.

E cuidado com a diferença entre os dois tipos de sprite — traje e equipamento
não se checam do mesmo jeito:

| | equipamento | traje |
|---|---|---|
| chão (`sprite\<item>\`) | obrigatório | obrigatório — é o que crashou o 5376 |
| vestido | `sprite\<acessório>\<sexo>\` | capa vai em `sprite\<robe>\<AegisName>\<sexo>\` |

**Ele não cobre item custom.** A fonte dele é o `iteminfo_ptBR.lua` do LATAM, e
ID 60000+ não existe lá — sai `<ausente no LATAM> SEM identifiedResourceName`,
que soa como "o campo está vazio" quando o campo pode estar preenchido e
errado. Para custom, confira à mão que o `identifiedResourceName` do
`itemInfo_C.lua` é **copiado** de um item que já existe, nunca traduzido: em
12/ago/2026 os Transmutadores (60000/60001) apontavam para as palavras
coreanas de "anel" e "brinco" em vez do recurso `ring` que o Anel (2601) e o
Brinco (2602) usam, e o cliente **fechava** ao desenhar o ícone — sem caixa de
erro, sem log.

Sobre o formato v3: não é kRO padrão, é o que o GRF Editor gera quando o
arquivo passa de 4 GB — o offset de cada entrada vira de 8 bytes (21 bytes de
metadado em vez de 17) e a tabela é `tam_real(4) + zlib` em vez de
`comprimido/real`. O `grf_listar.py` lê os dois formatos.

### Como recuperar um arquivo que falta

O `grf_listar.py` também **decifra** as entradas encriptadas (flags 0x02 e
0x04) — o porte é direto de `src/common/des.cpp` e `src/common/grfio.cpp` do
próprio rAthena deste repo, ou seja, a mesma lógica que o servidor usa. Não é
DES de verdade: é uma versão mutilada, de uma rodada e sem chave.

```
python docs/cliente/grf_listar.py --grf C:/RagnaClient/data.grf --filtro <parte-do-nome>
python docs/cliente/grf_listar.py --grf C:/RagnaClient/data.grf --extrair <caminho\completo>
```

O destino tem que usar **os mesmos bytes cp949** do nome dentro do GRF. Na
prática isso significa gravar o nome como a sequência que o cp1252 mostra
(`»çÅ¸´ÐÃ¼ÀÎ.spr`), porque o cliente abre o arquivo pela API ANSI e o Windows
converte de volta para os mesmos bytes. Nome em coreano de verdade (Unicode)
**não** casa.

Feito assim em 12/ago/2026 para as "Lendárias Asas de Demônio" (item 5376): os
6 arquivos foram para `RagnaBeat.Dev\data\sprite\`, que o `build.py` copia
inteira para o jogador. Pasta solta é preferível a GRF aqui — é como o projeto
já sobrescreve os `.lub`, e não exige tocar no `DATA.ini`.

## Cores de roupa e cabelo — o pacote `palette.grf`

Instalado em 12/ago/2026. São **225.109 arquivos** (112 MB) em
`data\palette\<corpo>\` e `data\palette\<cabelo>\`.

Ele estava na pasta mas **fora do `DATA.ini`**, ou seja, não era carregado por
ninguém. Agora entra como **entrada 2, depois do `data.grf`** — e a ordem é
deliberada: as cores 0 a 3 não existem no pacote porque já vêm no GRF base, e
pôr o pacote na frente trocaria a aparência de quem já joga.

**Os limites do servidor foram medidos, não chutados** — em
`conf/import/battle_conf.txt`:

| | medido no GRF | config |
|---|---|---|
| roupa | 4..699 presentes nos **213** grupos classe+sexo | `max_cloth_color: 699` |
| cabelo | 0..127 presentes nos **240** grupos | `max_hair_color: 127` |

O pacote também traz 43 mil paletas de traje e visual, que **não entram nessa
conta** — só os grupos com cobertura completa valem, porque cor sem `.pal` para
a classe do jogador deixa o personagem com a paleta errada. Trocando o pacote,
remeça a medição antes de mexer no `battle_conf`.

O NPC **Estilista** (`npc/custom/stylist.txt`) foi habilitado e traduzido, e
fica em `prontera,142,187`. Ele usa `getbattleflag`, então acompanha esses
limites sozinho — mexer no `battle_conf` basta.

> ⚠ A prévia do estilista é aplicada **de verdade** no personagem enquanto se
> navega. Sair pelo ESC deixa a última cor visualizada; só o "Voltar ao
> original" desfaz. É comportamento do script do Euphy, registrado no cabeçalho
> dele.

## O botão "Visualizar" (preview de item)

> **Correção de 02/set/2026.** A versão anterior desta seção dizia que o preview
> exigia recompilar o servidor, aplicar o `PreviewInShop` no WARP e migrar a loja
> de barter para Loja Cash. **As três estavam erradas** para o nosso caso.

O servidor **já manda os dados de preview em todas as 26 lojas barter, hoje.**
`clif_barter_open` (`src/map/clif.cpp:23226-23228`):

```cpp
#if PACKETVER_MAIN_NUM >= 20210203 || PACKETVER_RE_NUM >= 20211103
    item.viewSprite = id->look;
    item.location = pc_equippoint_sub( &sd, id.get() );
#endif
```

Nosso `PACKETVER` é 20250416 e **não** cai em nenhuma faixa RE (`src/config/packets.hpp:22`),
então `PACKETVER_MAIN_NUM = 20250416` e o `#if` é verdadeiro. Não há `#ifdef` de
preview aqui — é por packetver puro, sem switch de compilação. **Nada a compilar,
nada a migrar.**

Os dois defines do `core.hpp` servem a outras janelas, e nenhum é o nosso:

| Define | Par no WARP | Janela |
|---|---|---|
| `ENABLE_CASHSHOP_PREVIEW_PATCH` (`core.hpp:100`) | `PreviewInShop` | Loja Cash nova, a do botão — `ZC_ACK_SCHEDULER_CASHITEM` |
| `ENABLE_OLD_CASHSHOP_PREVIEW_PATCH` (`core.hpp:103`) | `PreviewInTrader` | Loja Cash antiga, aberta por NPC — `ZC_PC_CASH_POINT_ITEMLIST` |
| *(nenhum)* | *(nenhum)* | **barter — nativa, é a nossa** |

Ou seja: **recompilar o WARP com `PreviewInShop` não colocaria o botão na nossa
loja.** Se ele não aparecer na janela de barter, o problema é do lado do cliente
(a UI `BARTER_MARKET`), e não existe patch de WARP para isso.

Antes de mexer em qualquer coisa: abrir a loja de visuais e tentar **botão
direito** num item que tenha `View:` (as asas, `View` 34/61/75). O item precisa
ter `View` — o servidor manda `id->look`, e item com `View: 0` não tem o que
previsualizar (é o caso dos Transmutadores e do Anel do Mercador, que são
acessórios sem sprite).

### Por que NÃO migrar para `itemshop`

Seria um retrocesso, e tem um bug de verdade no caminho. `npc.cpp:2245-2249`
manda `cashshop`, `itemshop` e `pointshop` todos para o mesmo `clif_cashshop_show`
— não existe UI alternativa, o cliente desenha a Loja Cash com os rótulos
"Cash"/"Free Cash"/"Kafra" fixos.

A compra em si usa a moeda-item corretamente (`npc.cpp:2472` faz `pc_delitem` da
moeda, sem `pc_paycash`). Mas `cost[1]` é sempre **0** no itemshop
(`clif.cpp:17407`), e a checagem em `npc.cpp:2449` é:

```cpp
if (cost[1] < points || cost[0] < (price - points)) { ... PURCHASE_FAIL }
```

Logo, **qualquer `kafraPoints > 0` que o cliente mande faz a compra falhar** com
"You do not have enough", mesmo com moedas de sobra. Foi exatamente o sintoma
relatado quando o Contrabandista ainda era `itemshop`.

### Se um dia for preciso mesmo rebuildar o WARP

A rotina completa está em "Rotina após cada build no WARP", acima. As três
armadilhas que uma auditoria da sessão salva encontrou:

1. **Load Session** de `DEVTOOLS\WARP-2025\BASE_2025-04-16_limpo_PROFILE.yml`
   (33 patches). **Nunca** o homônimo da raiz `RagnaBeat.Dev\` — aquele é de
   10/ago, perdeu `CustomFontCharset` e `CustomFontHgtLimits` (quebra a
   acentuação) e traz de volta `AlwaysAscii`/`CallKoreaClientInfo`.
2. **Recarregar a fonte** depois de apontar para o `BASE`: o WARP mantém o
   binário anterior em memória e patcheia o errado em silêncio.
3. Conferir no fim: `SkippedPatches.log` **vazio**, saída com **14.987.776 bytes**,
   e `SendClientFlags` ainda presente (o caminho legado do `PreviewInShop.qjs`
   tem um `Exe.ClearPatch('SendClientFlags')` — inofensivo em builds 2024+, que
   retornam antes, mas vale conferir).

## Pendente

- **O `ragnabeat.grf` tem 953 arquivos e não é carregado por ninguém.** Está em
  `C:\RagnaClient`, fora do `DATA.ini` e fora do `build.py`. O conteúdo é de
  peso: `msgstringtable.txt`, `questid2display.txt` (1,4 MB), `itemmoveinfov5`,
  `mapnametable`, textos de livro. Alguém montou e nunca ligou. Decidir se
  entra — ligar 953 arquivos de uma vez muda texto e quest, então precisa de
  teste, não de um `DATA.ini` no escuro.
- Tradução PT-BR dos itens. O material está em `C:\RagnaClient\DEVTOOLS\PTBR\`:
  `iteminfo_ptBR.lua` (16.731 itens do LATAM, decompilados), `unluac.jar` e os scripts
  de cruzamento. **5.298 dos 6.169 itens do `db/pre-re` (85,9%) já mapeados.**
- ~~Verificar se a acentuação realmente funciona neste cliente~~ — **confirmada in-game
  em 10/ago/2026**, ver [acentuacao.md](acentuacao.md). Falta determinar o conjunto
  mínimo de constantes e checar se os sprites de itens continuam carregando.
- Reavaliar o `rdata.grf` (abr/2021), hoje fora do `DATA.ini`.
