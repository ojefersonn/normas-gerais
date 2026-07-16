# -*- coding: utf-8 -*-
"""Monta o catálogo de normas a partir das duas páginas-índice do gov.br/compras."""
import json
import re
import unicodedata
from bs4 import BeautifulSoup, NavigableString, Tag

URL1 = "https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema"
URL2 = "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/legislacao-por-tema"

# Temas de nível superior da página 1 (Lei 14.133 por tema)
TEMAS_TOPO_P1 = {
    "bens", "execucao contratual", "fornecedores",
    "governanca das contratacoes publicas", "licitacoes",
    "planejamento da contratacao", "politicas publicas licitacoes", "outros",
}

# Temas selecionados pelo usuário na página 2
TEMAS_SELECIONADOS_P2 = [
    "Almoxarifado", "Bagagens", "Bens móveis",
    "Cartão de Pagamentos do Governo Federal (CPGF)", "Cartão de Visita",
    "ETP digital", "Licitações", "Obras", "Outros – Contratos",
    "Pesquisa de Preços", "PGC e Cronograma de Contratação",
    "Racionalização de Gastos", "Revogação de normativos", "RNCP",
    "SCDP", "SEI", "SICAF", "SISG", "Sustentabilidade",
    "Telefonia", "Terceirização", "Veículos",
]


def norm_txt(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[–—-]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def tema_selecionado_p2(nome):
    n = norm_txt(nome)
    for t in TEMAS_SELECIONADOS_P2:
        if n.startswith(norm_txt(t).split()[0]) and norm_txt(t) in n or n.startswith(norm_txt(t)):
            return True
    return False


def ementa_apos(a):
    """Coleta o texto entre este <a> e o próximo <a> (a ementa da norma)."""
    partes = []
    for el in a.next_elements:
        if isinstance(el, Tag) and el.name == "a":
            break
        if isinstance(el, NavigableString):
            # ignora strings que estão DENTRO do próprio <a>
            if a in el.parents:
                continue
            partes.append(str(el))
    txt = re.sub(r"\s+", " ", " ".join(partes)).strip()
    txt = re.sub(r"^[\s\-–—:]+", "", txt).strip()
    return txt


def classificar_tipo(nome):
    n = norm_txt(nome)
    for chave, tipo in [
        ("lei complementar", "Lei Complementar"),
        ("lei ", "Lei"),
        ("decreto-lei", "Decreto-Lei"),
        ("decreto", "Decreto"),
        ("instrucao normativa", "Instrução Normativa"),
        ("portaria", "Portaria"),
        ("resolucao", "Resolução"),
        ("orientacao", "Orientação"),
        ("medida provisoria", "Medida Provisória"),
        ("emenda constitucional", "Emenda Constitucional"),
        ("acordao", "Acórdão"),
        ("parecer", "Parecer"),
        ("comunicado", "Comunicado"),
        ("nota tecnica", "Nota Técnica"),
        ("constituicao", "Constituição"),
        ("in n", "Instrução Normativa"),
    ]:
        if n.startswith(chave) or (chave == "lei " and re.match(r"^lei n", n)):
            return tipo
    return "Outro"


def raspar(arquivo, url_pagina, pagina_id):
    soup = BeautifulSoup(open(arquivo, encoding="utf-8"), "html.parser")
    main = soup.find(id="content-core")
    registros = []
    tema, subtema = None, None
    for a in main.find_all("a"):
        href = (a.get("href") or "").strip()
        texto = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        if not texto:
            continue
        if href.rstrip("/").split("#")[0] == url_pagina:
            # é um cabeçalho de tema/subtema
            if pagina_id == "p1":
                if norm_txt(texto) in TEMAS_TOPO_P1:
                    tema, subtema = texto, None
                else:
                    subtema = texto
            else:
                tema, subtema = texto, None
            continue
        if not href or href.startswith("mailto:"):
            continue
        # links de navegação que não são normas
        if norm_txt(texto) in ("voce sera direcionado para o portal pncp", "perguntas frequentes"):
            continue
        if href.startswith("resolveuid/"):
            base = url_pagina.rsplit("/", 1)[0]
            href = base + "/" + href
        registros.append({
            "nome": texto,
            "url": href,
            "ementa": ementa_apos(a),
            "tipo": classificar_tipo(texto),
            "tema": tema,
            "subtema": subtema,
            "pagina": pagina_id,
        })
    return registros


def main():
    r1 = raspar("indice1.html", URL1, "p1")
    r2 = todos_r2 = raspar("indice2.html", URL2, "p2")
    temas_p2 = sorted({r["tema"] for r in todos_r2 if r["tema"]})
    r2 = [r for r in todos_r2 if r["tema"] and tema_selecionado_p2(r["tema"])]
    temas_p2_sel = sorted({r["tema"] for r in r2})

    # Deduplicação por URL normalizada (e nome como fallback)
    def chave(r):
        u = r["url"].rstrip("/").replace("http://", "https://").lower()
        return u

    catalogo = {}
    for r in r1 + r2:
        k = chave(r)
        if k not in catalogo:
            catalogo[k] = {
                "nome": r["nome"], "url": r["url"], "tipo": r["tipo"],
                "ementa": r["ementa"], "temas": [],
            }
            item = catalogo[k]
        else:
            item = catalogo[k]
            if len(r["ementa"]) > len(item["ementa"]):
                item["ementa"] = r["ementa"]
        origem = "Lei 14.133 por tema" if r["pagina"] == "p1" else "Legislação por tema"
        rotulo = r["tema"] + (f" / {r['subtema']}" if r["subtema"] else "")
        entrada = {"origem": origem, "tema": r["tema"], "subtema": r["subtema"], "rotulo": rotulo}
        if entrada not in item["temas"]:
            item["temas"].append(entrada)

    normas = list(catalogo.values())
    print(f"Página 1: {len(r1)} registros")
    print(f"Página 2: {len(todos_r2)} registros no total; {len(r2)} nos temas selecionados")
    print(f"Temas encontrados na página 2: {json.dumps(temas_p2, ensure_ascii=False, indent=1)}")
    print(f"Temas selecionados casados: {json.dumps(temas_p2_sel, ensure_ascii=False, indent=1)}")
    print(f"Normas únicas após deduplicação: {len(normas)}")
    from collections import Counter
    print("Por tipo:", Counter(n["tipo"] for n in normas))
    json.dump(normas, open("catalogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
