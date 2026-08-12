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
5. **Rode `pos-warp.bat`** (ou `python pos-warp.py RagnaBeat.exe`).

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

1. **Redirecionar os 7 endereços** para `127.0.0.1` — é o que o `pos-warp.py` faz.
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

Ele compara os dois GRFs e marca `<<< FALTA NO BUILD` no que quebraria.

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
