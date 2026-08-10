# Estado consolidado e plano de tradução

Atualizado em 08/ago/2026. Este arquivo é a fonte da verdade — se o contexto da
conversa se perder, comece por aqui.

---

## 1. O que JÁ ESTÁ FUNCIONANDO

Cliente conecta, entra no jogo, sem erro de lua, com itens em português.

| Componente | Estado |
|---|---|
| Cliente | `C:\RagnaClient\KRO-NEW\RagnaBeat.exe` — Ragexe 2025-04-16 (build 2025-04-10) |
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
| `iteminfo_ptBR.lua` | 16.731 itens do RO LATAM, decompilados (fonte da tradução) |
| `unluac.jar` | decompilador Lua 5.1, funciona standalone |
| `xref_cobertura.py` | cruza itens do LATAM com o `db/pre-re` |
| `gen_item_ptbr.py` | gerador do itemInfo_C |

---

## 4. Fontes de tradução disponíveis

| Camada | Fonte | Estado |
|---|---|---|
| Itens (cliente) | RO LATAM oficial, decompilado | **feito** — 5.296 |
| NPCs (servidor) | brAthena, diálogos oficiais do bRO | a fazer |
| Mensagens do servidor | brAthena `conf/msg_conf` | a fazer |
| `msgstringtable` (cliente) | traduzir do inglês | a fazer |
| Skills (cliente) | `skilldescript.lub` do LATAM | a fazer |
| Nomes item/mob (servidor) | `db/pre-re/*.yml` | a fazer |

**brAthena**: github.com/brAthena/brAthena20180924 — base Hercules, pasta `npc/` toda em
português (`cidades`, `classes`, `kafras`, `comerciantes`...), com "diálogos oficiais do bRO".
Sintaxe ~90% compatível com rAthena.

---

## 5. Plano de tradução — ordem por retorno

### ~~Fase 1 — mensagens do servidor~~ ✅ FEITO em 08/ago/2026

O rAthena **já vinha** com a tradução: `conf/msg_conf/map_msg_por.conf`, 1.276 mensagens
em cp1252 com acentos corretos (tradução oficial de mkbu95 e Mahiro).

Ativada copiando para `conf/msg_conf/import/map_msg_eng_conf.txt` — o slot de import do
idioma padrão, que é o que o cliente pede com `langtype 1`. O `.gitignore` exclui essa
pasta (linha 74), então é config por instalação.

Confirmado no boot: `Done reading '1276' messages in
'conf/msg_conf/import/map_msg_eng_conf.txt'`.

### Fase 2 — `msgstringtable.txt` do cliente
~4 mil linhas, cobre toda mensagem de interface. Extrair do `en.grf`, traduzir, colocar
em `data\` (o `DataFolderFirst` está ativo).

### Fase 3 — NPCs — EM ANDAMENTO

**Ferramenta**: `C:\RagnaClient\DEVTOOLS\PTBR\traduzir_npc.py`

```
python traduzir_npc.py --dry cities/prontera.txt cidades/prontera.txt   # simula
python traduzir_npc.py       cities/prontera.txt cidades/prontera.txt   # aplica
python traduzir_npc.py --forcar ...                                     # modo permissivo
```

Casa NPCs pela **coordenada no mapa** (`mapa,x,y`), que não muda entre forks —
casar por nome não funciona, porque o brAthena traduziu os nomes.
Substitui só as linhas `mes`, preservando lógica, variáveis e quests.

**Piloto em `cities/prontera.txt`: FEITO.** 19 NPCs casados por coordenada, mas só
**3 traduzidos** — nos outros 16 a contagem de falas difere.

**Limitação medida**: o brAthena é de 2018 e o rAthena atual de 2026; os scripts
divergiram. Quando a contagem de falas difere, substituir em ordem desalinha o
diálogo, então o script **pula por padrão**. Rendimento seguro: ~16%.

**Caminho para escalar — memória de tradução (a fazer):**

Em vez de casar NPC a NPC, construir um dicionário `frase em inglês → frase em
português` a partir de TODOS os pares brAthena/rAthena onde a contagem bate. Depois
aplicar esse dicionário linha a linha em todos os 383 scripts. Casamento por texto
exato é seguro e escala muito melhor que casamento posicional.

**Alerta**: nome de NPC em português é mais longo e há limite de bytes no cliente.
Alguns podem precisar de encurtamento.

### Fase 4 — os 873 itens restantes
Não existem no cliente LATAM (itens antigos de pre-renewal). Traduzir à mão ou buscar
no brAthena.

### Fase 5 — skills
`data\luafiles514\lua files\skillinfoz\skilldescript.lub` — extrair do LATAM, mesma
técnica dos itens.

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
- `KRO-NEW\_exes_antigos\` — descartáveis
- `KRO-NEW\RagnaBeat2.exe` — primeira versão que conectou; rede de segurança
- `C:\RagnaClient\_removed_20260806\` — backups dos experimentos
