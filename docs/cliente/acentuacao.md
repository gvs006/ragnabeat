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

| Offset | Instrução | Seguido de | Trocado? |
|---|---|---|---|
| `0x0022807D` | `push 949` | `E8` call rel32 | sim |
| `0x0022EDF9` | `push 949` | `E8` call rel32 | sim |
| `0x0095226A` | `push 949` | `E8` call rel32 | sim |
| `0x00978155` | `push 949` | `E9` jmp | sim |
| `0x004CC3DC` | `push 949` | **`FF 15`** call indireto → `_setmbcp` | **não** |
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
- **6 — funciona**, e é a que está em uso. Não há ganho em mexer no CRT inteiro, e
  deixar o `_setmbcp` em 949 preserva o comportamento multibyte para caminhos de
  arquivo, onde o `resourceName` dos itens é cp949.

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
corretamente, e as fases 2 a 5 do plano de tradução
([estado-e-plano.md](estado-e-plano.md)) deixam de ser especulativas.
