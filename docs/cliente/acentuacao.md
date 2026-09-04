# Acentuação PT-BR — causa e solução

Resolvido em **10/ago/2026**, depois de dois dias de investigação. Era o motivo
original da migração para o cliente 2025.

---

## A causa

O cliente **converte texto para Unicode ele mesmo**, com o codepage **949 (cp949,
coreano) compilado no binário** — não via charset de fonte do GDI, não via
servicetype, não via locale do Windows.

O binário tem **7 constantes 949**. Trocamos **6** para 1252; a exceção é o
`_setmbcp`, que configura o codepage multibyte de todo o CRT e é deixado como está,
por precaução com nomes de arquivo dentro do GRF.

> **12/ago/2026 — trocar a sétima foi testado e NÃO resolve.** A hipótese era que
> o `_setmbcp` fosse o codepage usado para converter as mensagens do
> `msgstringtable`, o que explicaria elas saírem sem acento. Foi aplicado com
> `pos-warp.py --setmbcp`, empacotado no build 0.0.8 e testado in-game: **as
> mensagens continuaram sem acento**. Revertido; o estado bom é o de 6.
>
> A opção `--setmbcp` continua no `pos-warp.py`, documentada, para não se perder
> o caminho — mas **não use**: ela mexe no CRT inteiro sem entregar nada.
>
> O que isso ensina: a conversão dessas mensagens usa um codepage 949 que **não
> é nenhuma das 7 constantes conhecidas**. Uma varredura do binário achou 8
> ocorrências cruas de `B5 03 00 00`, das quais duas são instrução de verdade —
> `mov [ebp-4], 949` em `0x006B6798` e `0x006DFAF0` — e não chamam o mesmo
> conversor das que já funcionam. São o próximo lugar a investigar.

| Offset | Instrução | Seguido de | Trocado? |
|---|---|---|---|
| `0x0022807D` | `push 949` | `E8` call rel32 | sim |
| `0x0022EDF9` | `push 949` | `E8` call rel32 | sim |
| `0x0095226A` | `push 949` | `E8` call rel32 | sim |
| `0x00978155` | `push 949` | `E9` jmp | sim |
| `0x004CC3DC` | `push 949` | **`FF 15`** call indireto → `_setmbcp` | **sim, com `--setmbcp`** |
| `0x00654EE3` | `mov eax, 949` | — | sim |
| `0x0065501B` | `mov eax, 949` | — | sim |

O `_setmbcp` é distinguível sem depender de offset: é o **único** `push 949` seguido
de `FF 15`. É assim que o [pos-warp.py](pos-warp.py) o identifica, o que mantém o
patch válido mesmo se um build futuro do WARP deslocar os endereços.

Aplicado automaticamente pelo passo 3 do `pos-warp.py`, na pasta de desenvolvimento.
**É perdido a cada rebuild no WARP**, como os endereços da Gravity — por isso vive lá.

> O passo 1 do mesmo script redireciona **9** endereços, não 7. Os dois últimos —
> `192.168.5.52` e `211.172.247.115` — são IPs crus na mesma tabela, sem `ragnarok.co.kr`
> no nome, e por isso passaram despercebidos até 11/ago/2026. São inalcançáveis daqui, e
> o cliente ficava preso neles até o TCP desistir — a causa provável do login intermitente.

### Por que 6 e não 2, nem 7

- **2 (só o par `0x22807D`/`0x22EDF9`) — testado, NÃO funciona.** Os acentos não aparecem.
- **7 (todas) — funciona.** Foi a primeira versão que renderizou acentos.
- **6 — funciona** para o chat e para os nomes de item, e é a que está em uso.

> **12/ago/2026 — "não há ganho em mexer no CRT inteiro" estava errado.** Há um
> ganho, e ele só apareceu depois: com o `_setmbcp` em 949, **as mensagens do
> `msgstringtable` saem sem acento** — "Alimentacao automatica de mascote
> desligada".
>
> Medido com [sonda-acento.py](sonda-acento.py), que põe a mesma palavra em três
> codificações na mesma linha: **UTF-8 → `acao`** (acento some, sem erro) e
> **cp1252 → `a??o`**. Nenhuma funciona, porque o problema não é o arquivo.
>
> A causa: o cliente lê o CSV como UTF-8 corretamente, mas converte a string
> larga para multibyte com o codepage do CRT — o do `_setmbcp`. E o **cp949 não
> consegue representar `ç` nem `ã`**, nem em byte duplo; o Windows aplica *best
> fit* e troca cada um pela letra base, em silêncio. É por isso que o chat
> digitado acentua normal (outro caminho de renderização) e essas mensagens não.
>
> O `pos-warp.py` ganhou a opção `--setmbcp` para trocar a sétima também. O risco
> continua sendo o que motivou deixá-la de fora: o CRT passa a tratar como byte
> único os nomes de arquivo em cp949 do GRF, e um par cujo segundo byte seja
> `0x5C` viraria barra de caminho. **Isso nunca foi testado** — a doc registra que
> as 7 renderizavam acento, não que os sprites continuavam abrindo. O teste está
> no cabeçalho do passo 3 do `pos-warp.py`.

## Como se prova que funcionou

`@item 501` in-game, e uma mensagem no chat — os dois caminhos de renderização são
diferentes e ambos precisam funcionar.

| Item | Bytes | Antes | Depois |
|---|---|---|---|
| 501 | cp1252 `e7 e3 e1 ea` | `a-? c-? a-? e-?` | `a-á c-ç a-ã e-ê` ✅ |
| 502 | UTF-8 `c3 a7` | ideograma coreano | mojibake latino `Ã§` |

O par de teste está preservado em `SystemEN/itemInfo_C.lua.TESTE-501-502`. **Não deixe
esse arquivo como `itemInfo_C.lua` ativo** — ver a seção seguinte.

## O falso alarme das sprites

Durante o fechamento, os itens de teste apareceram **sem ícone**, e a hipótese
natural foi que trocar o codepage tinha quebrado a busca de sprite no GRF (o
`resourceName` é cp949). **Estava errado.**

A causa real: o `itemInfo_C.lua` ativo tinha **2 entradas** — o par de teste 501/502,
escrito à mão com `identifiedResourceName = ""`. Sem nome de recurso, não há o que
buscar no GRF. Os 5.296 itens traduzidos tinham sido postos de lado num backup
durante os experimentos de encoding, e só esses dois itens ficavam sem ícone; o resto
do jogo usava o itemInfo base normalmente.

**Nenhum patch de codepage jamais quebrou sprite.** A verificação do `build.py` avisa
quando há `resourceName` vazio, exatamente para não repetir esse diagnóstico.

## O que foi descartado no caminho

Registrado para que ninguém repita. **Nada disto resolve:**

| Tentativa | Por que não era |
|---|---|
| `CustomFontCharset = ANSI` | O patch é abrangente — o módulo `FONTAIN` do WARP redireciona **todos** os call sites de `CreateFontA` e força o `lfCharSet`. Estava valendo em todas as fontes e não mudou nada, o que prova que o GDI não faz o mapeamento byte→glifo aqui |
| `<servicetype>america</servicetype>` | A tabela de charset por servicetype existe (`FixFontsCharset` instala uma), mas não governa este caminho |
| `AlwaysAscii` ("Use Ascii on All") | Patcheia `CSession::IsOnlyEnglish` — rede/chat, não o decoder. Continua marcado e não atrapalha |
| `FixFontsCharset`, `EnableEotFonts`, `_setmbcp` isolado, langtype | Todos testados isoladamente entre 06 e 09/ago |
| Trocar de build (kRO × regional) | A premissa "build regional renderiza acento" era falsa. O binário é o mesmo; o que muda são estas constantes |

**A armadilha que custou mais tempo:** o patch `CallKoreaClientInfo` faz
`Exe.SetUint32(tblAddr + 4, Exe.GetUint32(tblAddr))` — reescreve a jump table para
que o índice 1 (`america`) caia no mesmo case do índice 0 (`korea`). Com ele marcado,
trocar o servicetype no `clientinfo.xml` é um no-op. Isso fez o servicetype ser dado
como "testado e descartado" quando nunca chegou a ser exercitado.

## Pendências

- Os offsets são **específicos deste build** (2025-04-16, 14.987.776 bytes). O
  `pos-warp.py` casa por padrão de bytes e não por offset, então provavelmente
  sobrevive a um rebuild — mas ele avisa se a contagem sair diferente de 6, e esse
  aviso deve ser levado a sério.
- Não sabemos o que os sites `0x0095226A`, `0x00978155`, `0x00654EE3` e `0x0065501B`
  fazem individualmente. Sabemos que 2 não bastam e que 6 funcionam.

## O que isso destrava

Com a renderização funcionando, os **5.296 itens PT-BR** já gerados exibem
corretamente, e as demais camadas deixam de ser especulativas —
ver [../traducao.md](../traducao.md).

---

## 04/set/2026 — o que mudou, e o que sobrou

### As mensagens do `msgstringtable` continuam sem acento

Sintoma: *"Alimentação automática de mascote desligada"* sai como
`Alimentacao`, letra base, sem erro nenhum.

Eliminado com teste, nesta ordem:

| tentativa | resultado |
|---|---|
| payload do CSV em UTF-8 | `Alimentacao` |
| payload do CSV em **cp1252** | `Alimentacao` |
| `_setmbcp` em 949 (padrão) | `Alimentacao` |
| `_setmbcp` em 1252 (`--setmbcp`) | `Alimentacao` |
| o texto na origem | **tem acento** — conferido nos bytes |

O texto aparece **em português**, então a tabela traduzida está sendo lida.
Só o acento morre.

### O achado que estreita o problema

Esta página registrava, de uma medição anterior:

```
UTF-8  -> "acao"    best-fit, some em silêncio
cp1252 -> "a??o"    interrogações
```

**Isso mudou.** Depois de trocarmos as 6 constantes de codepage para 1252, o
payload em cp1252 passou a sair `Alimentacao` — limpo, sem interrogações.

Ou seja: **o lado da LEITURA foi consertado**. Os bytes cp1252 agora são
decodificados corretamente. O que sobra é a conversão de **saída**, que faz
*best-fit* para um codepage que não representa acento latino.

### RESOLVIDO em 04/set/2026 — era a tabela de idioma

O culpado era uma **oitava constante 949**, que nenhuma busca anterior via.

O cliente tem uma tabela que escolhe o codepage pelo idioma do serviço:

```
0x006582D2  mov [0156F528], 949     coreano   <- o ramo que usamos
0x006582E8  mov [0156F528], 932     japonês
0x00658303  mov [0156F528], 936     chinês simplificado
0x0065831E  mov [0156F528], 950     chinês tradicional
0x00658339  mov [0156F528], 874     tailandês
0x0065838B  mov [0156F528], 1252    latino ocidental
0x006583A8  mov [0156F528], 1251    cirílico
```

O global `0x0156F528` é referenciado **53 vezes**, a maioria como
`push [global]` — ou seja, entregue como **argumento de conversão**. Com 949
ali, o Windows não representa `ã` nem `ç` no destino, aplica *best-fit* e
devolve a letra base em silêncio. Daí `Alimentacao`.

Trocar o ramo coreano para **1252** resolve. Está no `pos-warp.py`, passo 7.

#### Por que o `--setmbcp` não resolvia

**São codepages diferentes.** O `_setmbcp` configura o CRT; este é do próprio
cliente. Trocar um não mexe no outro — por isso o teste com `--setmbcp` deu o
mesmo resultado nos dois valores, e por isso mexer no arquivo (UTF-8 ou cp1252)
também não mudava nada.

#### Como foi achado — o método, para repetir

Procurar o dword 949 (`B5 03 00 00`) no binário **inteiro, sem filtrar por
opcode**. Deram 9 ocorrências:

- **5 eram coincidência**: deslocamento `0x3B5` de `jmp`, `call` e `jne`
- **4 eram atribuição real** na forma `C7`, que as buscas anteriores
  (`push 949` = `68`, `mov eax, 949` = `B8`) não cobriam

A lição: buscar por **valor**, não por instrução. Filtrar por opcode escondeu
essa constante por meses.

#### As três que sobraram

Não foram tocadas — gravam em variável local, e mexer no que não se testa é
como este arquivo acumula armadilha. Ficam como candidatas se aparecer outro
texto sem acento:

```
0x006B6798  mov [ebp-4], 949
0x006DFAF0  mov [ebp-4], 949
0x0077CF7B  mov [ebp-0EECh], 949
```

---

### Histórico: onde se procurou antes

O codepage de destino **não é o do `_setmbcp`** — testado nos dois valores,
mesmo resultado. Sobra achar uma oitava fonte de 949 que não está entre as
sete constantes imediatas listadas no `pos-warp.py`. Candidatos: `GetACP()`,
o charset da fonte passado ao `CreateFontA`, ou o langtype/servicetype.

Três caminhos no cliente, e só um perde:

| texto | acento |
|---|---|
| nome de item (`itemInfo.lua`) | **sim** |
| o que o jogador digita | **sim** |
| mensagens do `msgstringtable` | **não** |

Comparar como o cliente trata esses três é provavelmente o caminho mais curto.

### O que NÃO era

O "Weight" do Alt+V não tinha nada a ver com acentuação nem com
`msgstringtable`: era **string compilada no exe**, em `0x00C197B0`. Foram
gastas horas em pasta solta, `DataFolderFirst` e GRF própria por causa disso.

A regra que ficou: **compare o formato exibido com o formato da chave** antes
de caçar arquivo. Ver `.claude/agents/ragnabeat-traducao.md`.
