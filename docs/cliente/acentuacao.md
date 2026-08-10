# Acentuação PT-BR — causa e solução

Resolvido em **10/ago/2026**, depois de dois dias de investigação. Era o motivo
original da migração para o cliente 2025.

---

## A causa

O cliente **converte texto para Unicode ele mesmo**, com o codepage **949 (cp949,
coreano) compilado no binário** — não via charset de fonte do GDI, não via
servicetype, não via locale do Windows.

São **7 constantes** no `.text`, todas trocadas para **1252** (cp1252, latino):

| Offset | Instrução | O que é |
|---|---|---|
| `0x0022807D` | `push 949` | par `f(949, ptr)` — provável decoder de texto |
| `0x0022EDF9` | `push 949` | idem, segunda cópia |
| `0x004CC3DC` | `push 949` | `_setmbcp(949)`, na inicialização do CRT |
| `0x0095226A` | `push 949` | não identificado |
| `0x00978155` | `push 949` | não identificado |
| `0x00654EE3` | `mov eax, 949` | não identificado |
| `0x0065501B` | `mov eax, 949` | não identificado |

Aplicado automaticamente pelo passo 3 do `pos-warp.py` (em `C:\RagnaClient\KRO-NEW\`).
**É perdido a cada rebuild no WARP**, como os endereços da Gravity — por isso vive lá.

## Como se prova que funcionou

Os itens 501 e 502 do `SystemEN\itemInfo_C.lua` são pares de teste, com o mesmo
texto em encodings diferentes:

| Item | Bytes | Antes | Depois |
|---|---|---|---|
| 501 | cp1252 `e7 e3 e1 ea` | `a-? c-? a-? e-?` | `a-á c-ç a-ã e-ê` ✅ |
| 502 | UTF-8 `c3 a7` | ideograma coreano | mojibake latino `Ã§` |

`@item 501` in-game. Vale também mandar uma mensagem no chat — o caminho de
renderização é outro, e ambos precisam funcionar.

## O que foi descartado no caminho

Registrado para que ninguém repita. **Nada disto resolve:**

| Tentativa | Por que não era |
|---|---|
| `CustomFontCharset = ANSI` | O patch é abrangente — o módulo `FONTAIN` do WARP redireciona **todos** os call sites de `CreateFontA` e força o `lfCharSet`. Estava valendo em todas as fontes e não mudou nada, o que prova que o GDI não faz o mapeamento byte→glifo aqui |
| `<servicetype>america</servicetype>` | A tabela de charset por servicetype existe (`FixFontsCharset` instala uma), mas não governa este caminho |
| `AlwaysAscii` ("Use Ascii on All") | Patcheia `CSession::IsOnlyEnglish` — rede/chat, não o decoder. Continua marcado e não atrapalha |
| `FixFontsCharset`, `EnableEotFonts`, `AlwaysAscii`, `_setmbcp` isolado, langtype | Todos testados isoladamente entre 06 e 09/ago |
| Trocar de build (kRO × regional) | A premissa "build regional renderiza acento" era falsa. O binário é o mesmo; o que muda são estas 7 constantes |

**A armadilha que custou mais tempo:** o patch `CallKoreaClientInfo` faz
`Exe.SetUint32(tblAddr + 4, Exe.GetUint32(tblAddr))` — reescreve a jump table para
que o índice 1 (`america`) caia no mesmo case do índice 0 (`korea`). Com ele marcado,
trocar o servicetype no `clientinfo.xml` é um no-op. Isso fez o servicetype ser dado
como "testado e descartado" quando nunca chegou a ser exercitado.

## Pendências

- **Conjunto mínimo não determinado.** Os 7 sites foram trocados de uma vez. Não
  sabemos quais são realmente necessários. Suspeita: o par `0x0022807D`/`0x0022EDF9`
  basta.
- **Risco no `resourceName`.** O `resourceName` dos itens é cp949 e é ele que localiza
  o sprite dentro do GRF. Se algum dos 7 sites converte nome de recurso, sprites de
  itens com nome coreano podem quebrar. **Verificar ícones no inventário.** Se
  quebrarem, o primeiro suspeito é o `_setmbcp` em `0x004CC3DC`, que afeta todas as
  funções mbcs do CRT — dá para excluir só ele em `CODEPAGE` no `pos-warp.py`.
- Os offsets são **específicos deste build** (2025-04-16, 14.987.776 bytes). Trocar de
  executável exige localizá-los de novo — o `pos-warp.py` busca por padrão de bytes,
  não por offset fixo, então provavelmente continua funcionando.

## O que isso destrava

Com a renderização funcionando, tudo que estava parado esperando por ela volta ao jogo:
os **5.296 itens PT-BR** já gerados passam a exibir corretamente, e as fases 2 a 5 do
plano de tradução ([estado-e-plano.md](estado-e-plano.md)) deixam de ser especulativas.
