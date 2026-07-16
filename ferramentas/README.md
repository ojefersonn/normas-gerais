# Ferramentas de atualização do acervo

Scripts em Python que montam e atualizam o acervo de normas. Requerem
`python3` com `beautifulsoup4` e `html2text` (`pip install beautifulsoup4 html2text`)
e, para normas em PDF, o utilitário `pdftotext` (pacote `poppler-utils`).

## Passo a passo para atualizar o acervo

Execute os scripts **nesta ordem**, a partir de um diretório de trabalho
(os caminhos do repositório estão definidos no topo de cada script — ajuste
`REPO` se necessário):

```bash
# 1. Baixe as duas páginas-índice do gov.br
curl -sL -A "Mozilla/5.0" -o indice1.html "https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema"
curl -sL -A "Mozilla/5.0" -o indice2.html "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/legislacao-por-tema"

# 2. Monte o catálogo (temas, normas, ementas, links)
python3 scrape_catalog.py

# 3. Aplique correções de links quebrados nas páginas oficiais
python3 apply_fixes.py

# 4. Baixe o texto integral de cada norma (usa cache local ./cache/)
python3 fetch_norms.py

# 5. Converta para Markdown (gera normas/)
python3 convert_norms.py

# 6. Regenere índices e README (gera indices/ e README.md)
python3 gen_indexes.py

# 7. Regenere o site de busca (gera docs/)
python3 gen_site.py
```

Depois, revise `git diff`, commite e envie.

## O que cada script faz

| Script | Função |
|---|---|
| `scrape_catalog.py` | Raspa as páginas-índice e gera `catalogo.json` com tema/tipo/nome/ementa/URL de cada norma, deduplicando entre as duas páginas. A lista de temas selecionados da página "Legislação por tema" está no topo do script (`TEMAS_SELECIONADOS_P2`). |
| `apply_fixes.py` | Corrige URLs que estão quebradas nas páginas oficiais (404) e registra espelhos de download para fontes que bloqueiam robôs (in.gov.br, AGU). |
| `fetch_norms.py` | Baixa cada norma para `./cache/` com retentativas. Idempotente: só baixa o que ainda não está em cache. |
| `convert_norms.py` | Extrai o conteúdo principal de cada página (Planalto, gov.br, DOU), converte para Markdown com cabeçalho padronizado e grava em `normas/`. Trechos revogados ficam ~~riscados~~. |
| `gen_indexes.py` | Gera os índices por tema (`indices/*.md`), o índice por tipo e o `README.md`. |
| `gen_site.py` | Gera o buscador estático (`docs/index.html` + `docs/dados.json`) usado no GitHub Pages. |

## Observações

- Falhas de download ficam registradas em `falhas_download.json` e falhas de
  conversão em `falhas_conversao.json` — verifique os dois após atualizar.
- Se uma norma nova aparecer com link quebrado na página do governo, adicione
  a correção em `apply_fixes.py` (há instruções no próprio arquivo).
- O catálogo consolidado da última atualização fica versionado em
  [`dados/catalogo.json`](../dados/catalogo.json).
