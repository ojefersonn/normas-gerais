# -*- coding: utf-8 -*-
"""Aplica correções de URLs quebradas nas páginas-índice do gov.br (idempotente).

Execute sempre após scrape_catalog.py. Cada entrada corrige um link que está
quebrado na página oficial (404/indisponível), apontando para o endereço
oficial alternativo. Quando nem isso é acessível a robôs, usa-se um espelho
(Wayback Machine/instituição federal) apenas para download, mantendo a URL
oficial como fonte de citação.
"""
import json

# URL quebrada na página-índice -> URL oficial alternativa (vira a fonte)
CORRECOES_FONTE = {
    "https://www.gov.br/compras/pt-br/nllc/resolveuid/0c8930da78474f51822d8b95a7c77ed6":
        "https://www.gov.br/contratamaisbrasil/pt-br/central-de-conteudo/editais-e-regulamentacao/instrucoes-normativas/instrucao-normativa-seges-mgi-no-52-de-10-de-fevereiro-de-2025",
    "http://inmetro.gov.br/legislacao/laf/pdf/LAF000168.pdf":
        "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-n-o-142-de-05-de-agosto-de-1983",
    "https://www.gov.br/compras/pt-br/centrais-de-conteudo/orientacoes-e-procedimentos/desfazimento-de-bens-de-informatica":
        "https://www.gov.br/compras/pt-br/agente-publico/orientacoes-e-procedimentos/desfazimento-de-bens-de-informatica",
    "https://www.gov.br/compras/pt-br/centrais-de-conteudo/orientacoes-e-procedimentos/16-orientacao-sobre-sistema-integrado-de-gestao-patrimonial-2013-siads":
        "https://www.gov.br/compras/pt-br/agente-publico/orientacoes-e-procedimentos/16-orientacao-sobre-sistema-integrado-de-gestao-patrimonial-2013-siads",
    "https://www.gov.br/compras/pt-br/centrais-de-conteudo/orientacoes-e-procedimentos/25-orientacao-sobre-desfazimento-de-bens":
        "https://www.gov.br/compras/pt-br/agente-publico/orientacoes-e-procedimentos/25-orientacao-sobre-desfazimento-de-bens",
    "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/resolveuid/66e7e8902a0e4c4b908e0d4d1d62da5a":
        "https://in.gov.br/en/web/dou/-/portaria-n%C2%BA-179-de-22-de-abril-de-2019-83417682",
    "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-10-de-23-de-novembro-de-2018":
        "https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/52001726/do1-2018-11-27-instrucao-normativa-n-10-de-23-de-novembro-de-2018-52001279",
}

# Fonte oficial -> URL de download alternativa (quando a fonte bloqueia robôs)
ESPELHOS_DOWNLOAD = {
    "https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/52001726/do1-2018-11-27-instrucao-normativa-n-10-de-23-de-novembro-de-2018-52001279":
        "https://web.archive.org/web/20250504102743/https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-10-de-23-de-novembro-de-2018",
    "https://in.gov.br/en/web/dou/-/portaria-n%C2%BA-179-de-22-de-abril-de-2019-83417682":
        "https://web.archive.org/web/20240704201640/https://www.in.gov.br/en/web/dou/-/portaria-n%C2%BA-179-de-22-de-abril-de-2019-83417682",
    "https://sapiens.agu.gov.br/valida_publico?id=1781855249":
        "https://ufsj.edu.br/portal2-repositorio/File/dconf/Parecer%20Referencial%20004-2024.pdf",
}


def main():
    normas = json.load(open("catalogo.json"))
    nf = nd = 0
    for n in normas:
        if n["url"] in CORRECOES_FONTE:
            n["url_original"] = n["url"]
            n["url"] = CORRECOES_FONTE[n["url"]]
            nf += 1
        if n["url"] in ESPELHOS_DOWNLOAD:
            n["url_download"] = ESPELHOS_DOWNLOAD[n["url"]]
            nd += 1
    json.dump(normas, open("catalogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Correções de fonte: {nf}; espelhos de download: {nd}")


if __name__ == "__main__":
    main()
