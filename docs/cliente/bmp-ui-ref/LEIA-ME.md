# Rótulos pintados em BMP — o que dá para traduzir no Photoshop

Nem todo texto da interface é string. Boa parte é **desenhada dentro de uma
imagem**, e traduzir esses exige editar o BMP — não existe chave no
`msgstringtable` para eles.

Os `.bmp` desta pasta foram extraídos da nossa `data.grf` e servem de molde.

---

## Janela de status (Alt+V)

| Arquivo | Tamanho | O que tem escrito |
|---|---|---|
| `w_statwin_bg.bmp` | 280 x 124 | **Str, Agi, Vit, Int, Dex, Luk** / **Atk, Matk, Hit, Critical, Status Point, Guild** / **Def, Mdef, Flee, Aspd** |
| `w_ex_statwin_bg.bmp` | 280 x 224 | tudo do de cima **mais** a parte de 4ª classe: **Pow, Sta, Wis, Spl, Con, Crt** / **P.Atk, S.Matk, H.Plus, C.Rate, T.Status Point** / **Res, Mres** |

O `w_ex_` é a versão expandida (botão de seta na janela). **Os dois precisam da
mesma tradução**, senão o texto muda quando o jogador expande.

Os outros quatro da pasta `statuswnd\` — `expand_on_normal`, `expand_on_press`,
`expand_off_normal`, `expand_off_press`, todos 276x18 — são **só a barrinha do
botão de expandir**. Não têm texto, não precisam de nada.

### O que NÃO está nessas imagens

**Peso, Zeny, Nv base. e Nv. classe são TEXTO**, não imagem. Vêm do
`data\msgstringtable.csv`:

| chave | valor em PT-BR |
|---|---|
| `MSI_WEIGHT` | `Peso : %3d / %3d` |
| `MSI_BASIC_MSG_ZENY` | `Zeny : %s` |
| `MSI__BASIC_MSG_BASE` | `Nv base. %d` |
| `MSI__BASIC_MSG_JOB` | `Nv. classe. %d` |

Já estão traduzidos no arquivo solto. Se ainda aparecem em inglês, o problema é
outro — ver a seção do `DataFolderFirst` em [../leia-me.md](../leia-me.md).

> Isso também quer dizer que **esses quatro mudam de fonte** junto com o resto
> do cliente, e os `Str`/`Atk`/`Def` **não** — a fonte deles é a do desenho.
> Para testar fonte, olhe o Peso e o Zeny, nunca o Str.

---

## Photoshop 2022 — parâmetros para BMP

Diferente dos ícones de status (que são TGA 32 bits com alfa). Aqui é **BMP
24 bits, sem transparência**.

**Abrir o arquivo de referência e editar por cima** — assim o tamanho e a
paleta já vêm certos.

**Ao salvar:**

| Opção | Valor |
|---|---|
| Formato | **BMP** |
| Formato de arquivo | **Windows** |
| Profundidade | **24 bits** |
| Compactar (RLE) | **desmarcado** |

Não mude as dimensões. O cliente posiciona os campos por coordenada fixa; uma
imagem de tamanho diferente desalinha tudo — ou nem carrega.

### Cuidado com o espaço

Os rótulos estão espremidos. `Critical` já ocupa quase todo o campo, e
`Crítico` não cabe. Vale abreviar antes de esbarrar na borda:

| Original | Cabe | Não cabe |
|---|---|---|
| `Critical` | `Crít.` | `Crítico` |
| `Status Point` | `Pontos` | `Pontos de Status` |
| `T.Status Point` | `T.Pontos` | `Total de Pontos` |

---

## Onde o arquivo vai

```
data\texture\<pasta de UI em cp949>\statuswnd\<nome>.bmp
```

A pasta de UI tem nome em coreano (aparece como `À¯ÀúÀÎÅÍÆäÀÌ½º` num terminal
latin-1). Ela **já existe solta** na nossa instalação — é só criar a subpasta
`statuswnd\` dentro dela.

> ⚠ Antes de gastar tempo editando: confirme que override solto está
> funcionando. Em 04/set/2026 descobrimos que o patch `DataFolderFirst` **não
> foi aplicado** no nosso cliente 2025 — o script do WARP tem um ramo para
> builds 2025+ que acha o padrão e retorna sem escrever nada. Enquanto isso não
> for corrigido, arquivo solto que **conflita** com a GRF perde em silêncio, e
> uma imagem editada não apareceria no jogo. Ver [../leia-me.md](../leia-me.md).

---

## Ainda não mapeado

Estas outras telas também têm texto pintado, e não foram levantadas:

- inventário, equipamentos, habilidades
- janela de guilda e de grupo
- loja / carrinho

O `docs/cliente/gen-texturas-ptbr.py` já cobre **111 imagens** da tela de login
e do menu ESC, trocando pelas PT-BR do GRF do RO LATAM. Vale checar se alguma
destas acima também tem par por lá antes de redesenhar à mão.
