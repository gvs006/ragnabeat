# Doram (Summoner) — desativado como "Coming Soon"

Decidido em 11/ago/2026. O servidor é pre-renewal 99/70 e não tem a classe; o cliente
deixou de oferecê-la.

---

## Como está

| Camada | Mecanismo | Efeito |
|---|---|---|
| **Cliente** | `MakeableRace = { Doram = false }` | o botão vira o painel **Coming Soon** |
| **Servidor** | `allowed_job_flag: 1` | recusa `JOB_SUMMONER` com erro `-2` |

O cliente para antes de enviar o pacote; o servidor recusa caso alguém envie assim mesmo.

## Cliente — a via oficial

Linha 19 dos oito `ExternalSettings`, em texto puro:

```
data\luafiles514\lua files\service_america\ExternalSettings_us.lub
                                          ..._us_qm.lub  ..._us_sak.lub  ..._us_sak_qm.lub
data\luafiles514\lua files\service_korea\ExternalSettings_kr.lub   (+ as 3 variantes)
```

O `servicetype` hoje é `america`, mas os dois conjuntos andam juntos para não deixar
uma armadilha se alguém trocar o serviço.

**É o mecanismo que a própria Gravity usa.** O `ExternalSettings.lub` oficial do RO LATAM,
decompilado, traz exatamente `MakeableRace = {Doram = false}`. Por isso o cliente já tem a
textura pronta — `data\texture\<UI>\make_character_ver2\img_doram_comingsoon.bmp`
(181.328 bytes), mais a variante em `select_character_ver3\`.

## Servidor — tornando explícito o que já era acidental

[conf/import/char_conf.txt](../../conf/import/char_conf.txt) → `allowed_job_flag: 1`
(1 = Novice, 2 = Summoner, 3 = ambos).

Esse já era o valor efetivo, mas **por efeito colateral**:
[src/char/char.cpp:2814](../../src/char/char.cpp#L2814) escolhe o default com
`#if defined(RENEWAL) && PACKETVER >= 20151001` — e como `PRERE` está ativo em
[src/config/renewal.hpp:8](../../src/config/renewal.hpp#L8), cai no `else` com flag `1`.
Se alguém remover o `PRERE` um dia, o default vira `3` e o Doram volta a ser criável sem
ninguém ter pedido.

A barreira real está em [src/char/char.cpp:1488](../../src/char/char.cpp#L1488):

```cpp
if(!(start_job == JOB_NOVICE   && (charserv_config.allowed_job_flag&1)) &&
   !(start_job == JOB_SUMMONER && (charserv_config.allowed_job_flag&2)))
    return -2; // Invalid job
```

O `-2` vira `error = 0xFF` em `char_clif.cpp:1219`, que o cliente exibe como erro genérico
de criação — feio, e é justamente o que a flag do cliente evita.

> ⚠ O log em `charlog_db` é gravado **antes** da checagem de job
> ([char.cpp:1481](../../src/char/char.cpp#L1481)). Tentativas de criar Doram sujam o log
> mesmo sendo recusadas.

## Patches do WARP — avaliados e descartados

| Patch | Por que não |
|---|---|
| `NoDoramCreation` | `validate: BuildDate <= 20170614`. Nosso build é 2025-04-16, então o WARP **pula** o patch. O próprio autor comenta que em clientes modernos o bloqueio é externo — ou seja, o `MakeableRace` |
| `DisableDoram` | Aplica no nosso build, mas só reaponta as texturas do botão para string vazia. Deixa o botão **invisível e ainda clicável**, e não impede o job de ir no pacote. Cosmético |

## Se um dia quisermos Doram jogável

Não basta reverter as duas linhas. Seria preciso:

1. `allowed_job_flag: 3` no servidor
2. `MakeableRace = { Doram = true }` no cliente
3. **Portar os dados**: `db/pre-re/` não tem Summoner em `job_stats.yml`, `job_exp.yml`,
   `job_basepoints.yml`, `job_aspd.yml` nem `skill_tree.yml` — `grep -rl Summoner db/pre-re/`
   não retorna nada. Tudo isso existe só em `db/re/`
4. Balancear para 99/70 — a classe foi desenhada para renewal

É trabalho de conteúdo, não de configuração. Fica no [ROADMAP.md](../../ROADMAP.md) se virar
prioridade.
