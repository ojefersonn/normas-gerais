# -*- coding: utf-8 -*-
"""Converte o HTML em cache de cada norma para arquivos .md no repositório."""
import datetime
import hashlib
import json
import os
import re
import subprocess
import unicodedata

import html2text
from bs4 import BeautifulSoup

REPO = "/home/user/Claude"
CACHE = "cache"

PASTA_POR_TIPO = {
    "Lei": "leis",
    "Lei Complementar": "leis",
    "Medida Provisória": "medidas-provisorias",
    "Decreto": "decretos",
    "Decreto-Lei": "decretos",
    "Instrução Normativa": "instrucoes-normativas",
    "Portaria": "portarias",
    "Resolução": "resolucoes",
    "Orientação": "orientacoes",
    "Parecer": "pareceres",
    "Outro": "outros",
}


def cache_path(url):
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE, h)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def nome_arquivo(norma, usados):
    nome = norma["nome"]
    # extrai número e ano
    m = re.search(r"n[ºo°\.]?\s*\.?\s*([\d\.]+)", nome, re.I)
    numero = m.group(1).replace(".", "") if m else ""
    m = re.search(r"(19|20)\d\d", nome)
    ano = m.group(0) if m else ""
    # órgão/sigla (SEGES/ME etc.) ajuda a desambiguar
    m = re.search(r"(SEGES|SLTI|SGD|MPDG|MPOG|MGI|MF|ME|MPS|MEFP|SEDAP|SEDGG|SRF|STN|SAF|AGU|TCU|INSS|Conjunta|Interministerial|Normativa AGU)[\w/ ]*", nome)
    orgao = slugify(m.group(0))[:20].strip("-") if m else ""
    base = slugify(f"{norma['tipo']} {orgao} {numero} {ano}" if numero else norma["nome"][:60])
    cand, i = base, 2
    while cand in usados:
        cand, i = f"{base}-{i}", i + 1
    usados.add(cand)
    return cand + ".md"


def detectar_texto(caminho):
    raw = open(caminho, "rb").read()
    m = re.search(rb'charset=["\']?([\w\-]+)', raw[:4000], re.I)
    encs = [m.group(1).decode().lower()] if m else []
    encs += ["utf-8", "windows-1252", "latin-1"]
    for e in encs:
        try:
            return raw.decode(e)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def extrair_conteudo(soup, host):
    """Retorna o nó raiz do conteúdo principal conforme o site."""
    if "planalto.gov.br" in host:
        return soup.body or soup
    if "gov.br" in host:
        core = soup.find(id="content-core")
        if core:
            wrapper = BeautifulSoup("<div></div>", "html.parser").div
            h1 = soup.find("h1", class_="documentFirstHeading")
            desc = soup.find(class_="documentDescription")
            if h1:
                wrapper.append(BeautifulSoup(f"<h1>{h1.get_text(' ', strip=True)}</h1>", "html.parser"))
            if desc:
                wrapper.append(BeautifulSoup(f"<p><em>{desc.get_text(' ', strip=True)}</em></p>", "html.parser"))
            wrapper.append(core)
            return wrapper
        art = soup.find("article") or soup.find(id="content")
        if art:
            return art
    if "in.gov.br" in host:
        art = soup.find(class_="texto-dou") or soup.find("article") or soup.find("main")
        if art:
            return art
    return soup.body or soup


def limpar(no, base_url=""):
    from urllib.parse import urljoin
    for t in no.find_all(["script", "style", "noscript", "iframe", "form", "nav", "header", "footer", "button"]):
        t.decompose()
    # bloco de compartilhamento social do gov.br
    for t in no.find_all(class_=re.compile(r"social|share|addthis", re.I)):
        t.decompose()
    for t in no.find_all("p"):
        if t.get_text(" ", strip=True).startswith("Compartilhe"):
            t.decompose()
    # cabeçalho decorativo do Planalto
    for t in no.find_all("table"):
        txt = t.get_text(" ", strip=True)
        if "Presidência da República" in txt and len(txt) < 200:
            t.decompose()
    # absolutiza links relativos
    if base_url:
        for a in no.find_all("a"):
            href = a.get("href") or ""
            if href and not href.startswith(("http", "#", "mailto:")):
                a["href"] = urljoin(base_url, href)
    # riscado -> marcação markdown
    for t in no.find_all(["strike", "s", "del"]):
        txt = t.get_text(" ", strip=True)
        if txt:
            t.replace_with(f" ~~{txt}~~ ")
        else:
            t.decompose()
    # âncoras internas viram texto puro
    for a in no.find_all("a"):
        href = a.get("href") or ""
        if href.startswith("#") or not href:
            a.replace_with(a.get_text(" ", strip=True))
    return no


def para_markdown(html):
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = True
    h.ignore_emphasis = False
    h.unicode_snob = True
    h.skip_internal_links = True
    md = h.handle(html)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.M)
    linhas = []
    for ln in md.split("\n"):
        s = ln.strip()
        if s == "Compartilhe:" or s == "Brasão do Brasil":
            continue
        # linhas compostas só de links vazios (botões de compartilhamento)
        if s and not re.sub(r"\[\]\([^)]*\)", "", s).strip():
            continue
        linhas.append(ln)
    md = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas))
    return md.strip()


def pdf_para_texto(caminho):
    r = subprocess.run(["pdftotext", "-layout", caminho, "-"], capture_output=True, text=True)
    if r.returncode == 0 and len(r.stdout.strip()) > 200:
        return r.stdout.strip()
    return None


def situacao_da(norma, texto):
    alvo = (norma["nome"] + " " + norma["ementa"]).upper()
    if "REVOGAD" in alvo:
        return "Revogada (conforme indicação na página-índice)"
    ini = texto[:3000].upper()
    m = re.search(r"REVOGADO\s+PEL[OA]|REVOGADA\s+PEL[OA]", ini)
    if m:
        return "Revogada (conforme cabeçalho da fonte)"
    return "Vigente (não consta revogação na fonte consultada)"


def main():
    normas = json.load(open("catalogo.json"))
    usados = set()
    hoje = datetime.date.today().isoformat()
    relatorio = {"ok": 0, "pdf": 0, "falhas": []}
    indice = []

    for n in normas:
        cp = cache_path(n.get("url_download") or n["url"])
        arq = nome_arquivo(n, usados)
        pasta = PASTA_POR_TIPO.get(n["tipo"], "outros")
        rel_path = f"normas/{pasta}/{arq}"
        if not os.path.exists(cp + ".ok"):
            relatorio["falhas"].append({"nome": n["nome"], "url": n["url"], "motivo": "download falhou"})
            continue
        meta = json.load(open(cp + ".ok"))
        ct = (meta.get("content_type") or "").lower()

        if "pdf" in ct or n["url"].lower().endswith(".pdf"):
            texto = pdf_para_texto(cp)
            if not texto:
                relatorio["falhas"].append({"nome": n["nome"], "url": n["url"], "motivo": "PDF sem texto extraível"})
                continue
            corpo = "```\n" + texto + "\n```"
            relatorio["pdf"] += 1
        else:
            html = detectar_texto(cp)
            soup = BeautifulSoup(html, "html.parser")
            url_final = meta.get("url_final", n["url"])
            host = url_final.split("/")[2]
            if "web.archive.org" in host:
                host = url_final.split("/https://")[-1].split("/")[0] if "/https://" in url_final else host
            no = limpar(extrair_conteudo(soup, host), base_url=url_final)
            corpo = para_markdown(str(no))
            if len(corpo) < 300:
                relatorio["falhas"].append({"nome": n["nome"], "url": n["url"], "motivo": f"conteúdo muito curto ({len(corpo)} chars)"})
                continue

        temas = sorted({t["rotulo"] for t in n["temas"]})
        origens = sorted({t["origem"] for t in n["temas"]})
        situacao = situacao_da(n, corpo)
        ementa = n["ementa"].replace('"', "'")

        fm = ["---"]
        fm.append(f'titulo: "{n["nome"]}"')
        fm.append(f'tipo: "{n["tipo"]}"')
        fm.append(f'ementa: "{ementa}"')
        fm.append("temas:")
        for t in temas:
            fm.append(f'  - "{t}"')
        fm.append(f'fonte: "{n["url"]}"')
        fm.append(f'paginas_de_origem: "{"; ".join(origens)}"')
        fm.append(f'situacao: "{situacao}"')
        fm.append(f'capturado_em: "{hoje}"')
        fm.append("---")

        cab = [f"# {n['nome']}", ""]
        if n["ementa"]:
            cab += [f"> {n['ementa']}", ""]
        cab += [f"**Temas:** {'; '.join(temas)}  ", f"**Situação:** {situacao}  ", f"**Fonte oficial:** <{n['url']}>  ", f"**Capturado em:** {hoje}", "", "---", ""]

        destino = os.path.join(REPO, rel_path)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write("\n".join(fm) + "\n\n" + "\n".join(cab) + corpo + "\n")
        relatorio["ok"] += 1
        indice.append({**{k: n[k] for k in ("nome", "tipo", "ementa", "url")}, "temas": temas, "situacao": situacao, "arquivo": rel_path})

    json.dump(indice, open("indice_gerado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(relatorio["falhas"], open("falhas_conversao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Convertidas: {relatorio['ok']} (das quais {relatorio['pdf']} de PDF). Falhas: {len(relatorio['falhas'])}")
    for f_ in relatorio["falhas"]:
        print(" -", f_["nome"][:70], "::", f_["motivo"])


if __name__ == "__main__":
    main()
