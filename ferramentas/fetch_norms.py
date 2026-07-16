# -*- coding: utf-8 -*-
"""Baixa o HTML/PDF de cada norma do catálogo para o cache local."""
import hashlib
import json
import os
import subprocess
import time

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
CACHE = "cache"
os.makedirs(CACHE, exist_ok=True)


def cache_path(url):
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE, h)


def fetch(url):
    dest = cache_path(url)
    if os.path.exists(dest + ".ok"):
        return "cache", None
    for tentativa in range(3):
        r = subprocess.run(
            ["curl", "-sL", "--compressed", "-A", UA, "--max-time", "60",
             "-o", dest, "-w", "%{http_code}\t%{content_type}\t%{url_effective}", url],
            capture_output=True, text=True)
        partes = (r.stdout or "").split("\t")
        code = partes[0] if partes else "000"
        if code == "200" and os.path.getsize(dest) > 500:
            meta = {"content_type": partes[1] if len(partes) > 1 else "",
                    "url_final": partes[2] if len(partes) > 2 else url}
            json.dump(meta, open(dest + ".ok", "w"))
            return "ok", meta
        time.sleep(2 * (tentativa + 1))
    return "falha", {"http_code": code, "size": os.path.getsize(dest) if os.path.exists(dest) else 0}


def main():
    normas = json.load(open("catalogo.json"))
    falhas = []
    for i, n in enumerate(normas, 1):
        status, meta = fetch(n["url"])
        if status == "falha":
            falhas.append({"nome": n["nome"], "url": n["url"], **(meta or {})})
            print(f"[{i}/{len(normas)}] FALHA {n['nome'][:60]} :: {meta}")
        elif i % 20 == 0 or status == "ok":
            print(f"[{i}/{len(normas)}] {status} {n['nome'][:60]}")
        if status == "ok":
            time.sleep(0.6)
    json.dump(falhas, open("falhas_download.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nConcluído. Falhas: {len(falhas)}")


if __name__ == "__main__":
    main()
