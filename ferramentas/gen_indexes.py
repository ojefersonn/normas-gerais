# -*- coding: utf-8 -*-
"""Gera README e índices por tema/tipo a partir do catálogo convertido."""
import datetime
import json
import os
import re
import unicodedata
from collections import defaultdict

REPO = "/home/user/Claude"
URL1 = "https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema"
URL2 = "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/legislacao-por-tema"


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def ancora(rel_path):
    return "../" + rel_path


def main():
    indice = json.load(open("indice_gerado.json"))
    normas = json.load(open("catalogo.json"))
    por_arquivo = {i["arquivo"]: i for i in indice}
    # reconstrói temas com origem/subtema a partir do catálogo
    cat_por_url = {n["url"]: n for n in normas}

    # ---- agrupamento por tema (rotulo de nível superior) e origem ----
    grupos = defaultdict(lambda: defaultdict(list))  # origem -> tema -> [(subtema, item)]
    for n in normas:
        item = next((i for i in indice if i["url"] == n["url"]), None)
        if not item:
            continue
        for t in n["temas"]:
            grupos[t["origem"]][t["tema"]].append((t["subtema"], item))

    os.makedirs(os.path.join(REPO, "indices"), exist_ok=True)
    hoje = datetime.date.today().strftime("%d/%m/%Y")

    arquivos_tema = []  # (origem, tema, arquivo_indice, contagem)
    for origem, temas in grupos.items():
        for tema, entradas in temas.items():
            slug = ("lei-14133-" if origem.startswith("Lei") else "") + slugify(tema)[:60]
            arq = f"indices/{slug}.md"
            linhas = [f"# {tema}", "",
                      f"_Origem: página “{origem}” do Portal de Compras do Governo Federal._", ""]
            # agrupa por subtema
            por_sub = defaultdict(list)
            for sub, item in entradas:
                por_sub[sub or ""].append(item)
            for sub in sorted(por_sub, key=lambda s: (s != "", s)):
                if sub:
                    linhas += [f"## {sub}", ""]
                vistos = set()
                for item in por_sub[sub]:
                    if item["arquivo"] in vistos:
                        continue
                    vistos.add(item["arquivo"])
                    ementa = item["ementa"] or "(sem ementa na página-índice)"
                    revogada = " ⚠️ **REVOGADA**" if "Revogada" in item["situacao"] else ""
                    linhas.append(f"- **[{item['nome']}]({ancora(item['arquivo'])})**{revogada}  ")
                    linhas.append(f"  {ementa}")
                linhas.append("")
            open(os.path.join(REPO, arq), "w", encoding="utf-8").write("\n".join(linhas).rstrip() + "\n")
            n_unicos = len({i["arquivo"] for _, i in entradas})
            arquivos_tema.append((origem, tema, arq, n_unicos))

    # ---- índice por tipo ----
    por_tipo = defaultdict(list)
    for i in indice:
        por_tipo[i["tipo"]].append(i)
    linhas = ["# Todas as normas por tipo", "", f"Total: **{len(indice)} normas** (capturadas em {hoje})", ""]
    ordem = ["Lei", "Lei Complementar", "Medida Provisória", "Decreto", "Instrução Normativa",
             "Portaria", "Resolução", "Orientação", "Parecer", "Outro"]
    for tipo in sorted(por_tipo, key=lambda t: ordem.index(t) if t in ordem else 99):
        linhas += [f"## {tipo} ({len(por_tipo[tipo])})", ""]
        def chave_ord(i):
            m = re.search(r"(19|20)\d\d", i["nome"])
            return (m.group(0) if m else "0000", i["nome"])
        for i in sorted(por_tipo[tipo], key=chave_ord):
            temas = "; ".join(i["temas"])
            linhas.append(f"- [{i['nome']}]({ancora(i['arquivo'])}) — {temas}")
        linhas.append("")
    open(os.path.join(REPO, "indices/todas-por-tipo.md"), "w", encoding="utf-8").write("\n".join(linhas).rstrip() + "\n")

    # ---- README ----
    n_por_tipo = {t: len(v) for t, v in por_tipo.items()}
    revogadas = sum(1 for i in indice if "Revogada" in i["situacao"])
    r = []
    r.append("# 📚 Acervo de Normas — Licitações e Contratações Públicas")
    r.append("")
    r.append("Acervo em Markdown com o **texto integral** das normas sobre licitações, contratos e gestão")
    r.append("administrativa federal, coletadas do [Portal de Compras do Governo Federal](https://www.gov.br/compras/pt-br)")
    r.append("e de fontes oficiais (Planalto, Diário Oficial da União). Todo o conteúdo é pesquisável —")
    r.append("artigos, incisos e parágrafos, não apenas as ementas.")
    r.append("")
    r.append(f"**{len(indice)} normas** · atualizado em {hoje}")
    r.append("")
    r.append("| Tipo | Quantidade |")
    r.append("|---|---|")
    for tipo in sorted(n_por_tipo, key=lambda t: -n_por_tipo[t]):
        r.append(f"| {tipo} | {n_por_tipo[tipo]} |")
    r.append("")
    r.append("## 🔎 Como pesquisar")
    r.append("")
    r.append("- **No GitHub:** tecle `/` (ou use a caixa de busca), digite os termos e restrinja ao repositório.")
    r.append("  A busca varre o texto integral de todas as normas. Ex.: `pesquisa de preços sobrepreço`.")
    r.append("- **No site de busca:** abra o [buscador do acervo](https://ojefersonn.github.io/claude/) para")
    r.append("  busca instantânea com filtros por tema e tipo (requer GitHub Pages ativado).")
    r.append("- **Clonado localmente:** `grep -ril \"termo\" normas/` ou a busca da sua IDE.")
    r.append("")
    r.append("## 🗂️ Estrutura")
    r.append("")
    r.append("```")
    r.append("normas/                  ← texto integral (1 arquivo .md por norma)")
    r.append("  leis/  decretos/  instrucoes-normativas/  portarias/")
    r.append("  resolucoes/  orientacoes/  pareceres/  medidas-provisorias/")
    r.append("indices/                 ← índices de navegação por tema e por tipo")
    r.append("docs/                    ← site estático de busca (GitHub Pages)")
    r.append("ferramentas/             ← scripts para atualizar o acervo")
    r.append("dados/                   ← catálogo estruturado (JSON)")
    r.append("```")
    r.append("")
    r.append("Cada arquivo de norma tem um cabeçalho padronizado (YAML front matter) com título, tipo,")
    r.append("ementa, temas, situação, fonte oficial e data de captura, seguido do texto integral.")
    r.append("Trechos revogados aparecem ~~riscados~~, como na fonte consolidada do Planalto.")
    r.append("")
    r.append("## 📑 Índices por tema")
    r.append("")
    r.append("### Lei nº 14.133/2021 — legislação por tema")
    r.append(f"_Fonte: [{URL1}]({URL1})_")
    r.append("")
    p1 = sorted([x for x in arquivos_tema if x[0].startswith("Lei")], key=lambda x: x[1])
    for _, tema, arq, cnt in p1:
        r.append(f"- [{tema}]({arq}) ({cnt})")
    r.append("")
    r.append("### Legislação geral por tema (temas selecionados)")
    r.append(f"_Fonte: [{URL2}]({URL2})_")
    r.append("")
    p2 = sorted([x for x in arquivos_tema if not x[0].startswith("Lei")], key=lambda x: x[1])
    for _, tema, arq, cnt in p2:
        r.append(f"- [{tema}]({arq}) ({cnt})")
    r.append("")
    r.append("### Outros índices")
    r.append("")
    r.append("- [Todas as normas por tipo](indices/todas-por-tipo.md)")
    r.append("")
    r.append("## ⚠️ Avisos importantes")
    r.append("")
    r.append(f"- {revogadas} normas do acervo constam como **revogadas** — estão marcadas nos índices e no cabeçalho.")
    r.append("- Este acervo é uma **cópia de referência** para pesquisa. Para citação oficial, confira sempre a")
    r.append("  versão vigente na fonte indicada no cabeçalho de cada norma.")
    r.append("- A detecção de revogação é automática (indicação na página-índice ou no cabeçalho da fonte) e")
    r.append("  pode não capturar revogações recentes.")
    r.append("")
    r.append("## 🔄 Como atualizar o acervo")
    r.append("")
    r.append("Os scripts de coleta estão em [`ferramentas/`](ferramentas/) — veja o")
    r.append("[passo a passo](ferramentas/README.md). Em resumo: `scrape_catalog.py` remonta o catálogo a")
    r.append("partir das páginas do gov.br, `fetch_norms.py` baixa as normas e `convert_norms.py` regenera os")
    r.append("arquivos Markdown. Depois, `gen_indexes.py` refaz índices e README e `gen_site.py` refaz a busca.")
    open(os.path.join(REPO, "README.md"), "w", encoding="utf-8").write("\n".join(r) + "\n")
    print(f"Índices gerados: {len(arquivos_tema)} temas + por-tipo + README")


if __name__ == "__main__":
    main()
