# Documentação do Ragnabeat

Servidor **pre-renewal**, `PACKETVER 20250416`, rates 500x/20x, limites 99/70,
stack Docker + MariaDB. Cliente próprio baseado no Ragexe 2025-04-16.

## Onde cada coisa vive

| Documento | Quando abrir |
|---|---|
| [../ROADMAP.md](../ROADMAP.md) | features planejadas, decisões travadas, convenções de código |
| [infra-docker.md](infra-docker.md) | subir/derrubar a stack, entender as portas, mexer no banco |
| [auth-token.md](auth-token.md) | login travando em "Please wait", ou antes de religar o web-server |
| [seguranca.md](seguranca.md) | antes de expor qualquer porta fora do localhost |
| [cliente/leia-me.md](cliente/leia-me.md) | rebuild do `.exe` no WARP, patches obrigatórios e proibidos |
| [cliente/acentuacao.md](cliente/acentuacao.md) | acentos PT-BR: as 7 constantes cp949 e o que já foi descartado |
| [cliente/estado-e-plano.md](cliente/estado-e-plano.md) | estado da tradução PT-BR e o que fazer em seguida |

O `ROADMAP.md` fica na raiz de propósito — é o documento que se lê primeiro, e cobre
*o que construir*. Esta pasta cobre *como o que existe funciona*.

## Convenções

Herdadas do [ROADMAP.md](../ROADMAP.md) e válidas para todo o repositório:

- Dados custom em `db/import/` — nunca editar `db/pre-re/` direto
- C++ custom em `src/custom/`
- NPCs custom em `npc/custom/`, registrados em `npc/scripts_custom.conf`
- Alterações de conf em `conf/import/`

Tudo isso existe para que o merge com o upstream `rathena/rathena` não conflite.

> ⚠ **As três pastas de customização são git-ignored por padrão.** O
> [.gitignore](../.gitignore) ignora `/db/import/*` (linha 70), `/conf/import/*` (linha 73)
> e `/src/custom` (linha 94), e depois abre exceção **por arquivo** no bloco do fim.
>
> Arquivo custom **novo** precisa ser adicionado lá conscientemente — senão funciona na
> sua máquina e some no clone. Foi exatamente o que aconteceu com o `login_conf.txt`
> (ver [auth-token.md](auth-token.md)).
>
> Os arquivos de `src/custom/` escapam disso hoje só porque já vêm rastreados como stubs
> do upstream — regra de ignore não afeta arquivo já rastreado. Um `.inc` ou `.hpp` novo
> ali **não** teria essa sorte. Ao criar um, conferir com
> `git check-ignore -q <caminho>; echo $?` — deve responder `1`.

## Documentos destes docs

Ao escrever aqui: português, fatos com `arquivo:linha` como link relativo, tabela em vez
de parágrafo quando couber. Um documento por assunto, não um arquivão. Se algo foi medido,
diga quando — datas absolutas, nunca "semana passada".

## Repositório irmão

O site e o painel ficam em `ragna-site` (Next.js + TypeScript), com docs próprios em
`docs/decisoes.md`.
