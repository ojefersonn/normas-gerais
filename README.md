# 📚 Normas Gerais

_Acervo pesquisável de normas de licitações, contratos e gestão administrativa federal._

Acervo em Markdown com o **texto integral** das normas sobre licitações, contratos e gestão
administrativa federal, coletadas do [Portal de Compras do Governo Federal](https://www.gov.br/compras/pt-br)
e de fontes oficiais (Planalto, Diário Oficial da União). Todo o conteúdo é pesquisável —
artigos, incisos e parágrafos, não apenas as ementas.

**217 normas** · atualizado em 16/07/2026

| Tipo | Quantidade |
|---|---|
| Decreto | 86 |
| Instrução Normativa | 67 |
| Portaria | 46 |
| Resolução | 6 |
| Lei | 5 |
| Orientação | 4 |
| Parecer | 2 |
| Medida Provisória | 1 |

## 🔎 Como pesquisar

- **No GitHub:** tecle `/` (ou use a caixa de busca), digite os termos e restrinja ao repositório.
  A busca varre o texto integral de todas as normas. Ex.: `pesquisa de preços sobrepreço`.
- **No site de busca:** abra o [buscador do acervo](https://ojefersonn.github.io/normas-gerais/) para
  busca instantânea com filtros por tema e tipo (requer GitHub Pages ativado).
- **Clonado localmente:** `grep -ril "termo" normas/` ou a busca da sua IDE.
- **Perguntando em linguagem natural:** use o [assistente com IA](assistente/README.md), que
  responde com citações de norma e artigo (requer chave de API da Anthropic).

## 🗂️ Estrutura

```
normas/                  ← texto integral (1 arquivo .md por norma)
  leis/  decretos/  instrucoes-normativas/  portarias/
  resolucoes/  orientacoes/  pareceres/  medidas-provisorias/
indices/                 ← índices de navegação por tema e por tipo
docs/                    ← site estático de busca (GitHub Pages)
assistente/              ← assistente de consulta com IA (protótipo RAG)
ferramentas/             ← scripts para atualizar o acervo
dados/                   ← catálogo estruturado (JSON)
```

Cada arquivo de norma tem um cabeçalho padronizado (YAML front matter) com título, tipo,
ementa, temas, situação, fonte oficial e data de captura, seguido do texto integral.
Trechos revogados aparecem ~~riscados~~, como na fonte consolidada do Planalto.

## 📑 Índices por tema

### Lei nº 14.133/2021 — legislação por tema
_Fonte: [https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema](https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema)_

- [Bens](indices/lei-14133-bens.md) (3)
- [Execução Contratual](indices/lei-14133-execucao-contratual.md) (4)
- [Fornecedores](indices/lei-14133-fornecedores.md) (2)
- [Governança das Contratações Públicas](indices/lei-14133-governanca-das-contratacoes-publicas.md) (6)
- [Licitações](indices/lei-14133-licitacoes.md) (10)
- [Outros](indices/lei-14133-outros.md) (12)
- [Planejamento da Contratação](indices/lei-14133-planejamento-da-contratacao.md) (6)
- [Políticas Públicas - Licitações](indices/lei-14133-politicas-publicas-licitacoes.md) (20)

### Legislação geral por tema (temas selecionados)
_Fonte: [https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/legislacao-por-tema](https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/legislacao-por-tema)_

- [Almoxarifado](indices/almoxarifado.md) (20)
- [Bagagens](indices/bagagens.md) (1)
- [Bens móveis](indices/bens-moveis.md) (22)
- [Cartão de Pagamentos do Governo Federal (CPGF)](indices/cartao-de-pagamentos-do-governo-federal-cpgf.md) (13)
- [Cartão de Visita](indices/cartao-de-visita.md) (1)
- [ETP digital](indices/etp-digital.md) (1)
- [Licitações – RDC – SRP – Pregão – Cotação eletrônica](indices/licitacoes-rdc-srp-pregao-cotacao-eletronica.md) (18)
- [Obras – Construção e Manutenção](indices/obras-construcao-e-manutencao.md) (5)
- [Outros – Contratos](indices/outros-contratos.md) (10)
- [PGC e Cronograma de Contratação](indices/pgc-e-cronograma-de-contratacao.md) (2)
- [Pesquisa de Preços](indices/pesquisa-de-precos.md) (1)
- [RNCP - Rede Nacional de Compras](indices/rncp-rede-nacional-de-compras.md) (1)
- [Racionalização de Gastos](indices/racionalizacao-de-gastos.md) (3)
- [Revogação de normativos](indices/revogacao-de-normativos.md) (6)
- [SCDP - Passagens aéreas](indices/scdp-passagens-aereas.md) (24)
- [SEI – Protocolo](indices/sei-protocolo.md) (11)
- [SICAF](indices/sicaf.md) (5)
- [SISG - SIASG - GSISTE e Redimensionamento de UASG](indices/sisg-siasg-gsiste-e-redimensionamento-de-uasg.md) (9)
- [Sustentabilidade](indices/sustentabilidade.md) (12)
- [Telefonia Fixa e Móvel](indices/telefonia-fixa-e-movel.md) (1)
- [Terceirização](indices/terceirizacao.md) (16)
- [Veículos](indices/veiculos.md) (7)

### Outros índices

- [Todas as normas por tipo](indices/todas-por-tipo.md)

## ⚠️ Avisos importantes

- 26 normas do acervo constam como **revogadas** — estão marcadas nos índices e no cabeçalho.
- Este acervo é uma **cópia de referência** para pesquisa. Para citação oficial, confira sempre a
  versão vigente na fonte indicada no cabeçalho de cada norma.
- A detecção de revogação é automática (indicação na página-índice ou no cabeçalho da fonte) e
  pode não capturar revogações recentes.

## 🔄 Como atualizar o acervo

Os scripts de coleta estão em [`ferramentas/`](ferramentas/) — veja o
[passo a passo](ferramentas/README.md). Em resumo: `scrape_catalog.py` remonta o catálogo a
partir das páginas do gov.br, `fetch_norms.py` baixa as normas e `convert_norms.py` regenera os
arquivos Markdown. Depois, `gen_indexes.py` refaz índices e README e `gen_site.py` refaz a busca.
