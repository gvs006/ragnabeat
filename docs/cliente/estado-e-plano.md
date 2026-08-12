# Estado do cliente

> A tradução tem documento próprio: **[../traducao.md](../traducao.md)**.

Atualizado em 08/ago/2026. Este arquivo é a fonte da verdade — se o contexto da
conversa se perder, comece por aqui.

---

## 1. O que JÁ ESTÁ FUNCIONANDO

Cliente conecta, entra no jogo, sem erro de lua, com itens em português.

| Componente | Estado |
|---|---|
| Cliente | `RagnaBeat.exe` na pasta de desenvolvimento (hoje `C:\RagnaClient\RagnaBeat.Dev`, era `KRO-NEW`) — Ragexe 2025-04-16 (build 2025-04-10) |
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
