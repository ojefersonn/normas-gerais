# -*- coding: utf-8 -*-
"""Assistente de consulta às normas do acervo Normas Gerais (RAG agêntico).

O Claude recebe duas ferramentas — buscar trechos no acervo e ler uma norma —
e as usa quantas vezes precisar antes de responder, sempre citando as normas.

Uso:
    export ANTHROPIC_API_KEY="sua-chave"      # https://platform.claude.com/
    python3 assistente.py "Posso pagar um fornecedor antecipadamente?"
    python3 assistente.py                      # modo interativo
"""
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_NORMAS = os.path.join(RAIZ, "normas")

STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas", "o",
    "a", "os", "as", "um", "uma", "para", "por", "com", "que", "ao", "aos",
    "sobre", "ou", "se", "sua", "seu", "suas", "seus", "ser", "como", "nao",
    "art", "artigo", "lei", "decreto", "norma", "posso", "pode", "qual",
    "quais", "quando", "onde", "the",
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", texto.lower())


def tokens_de(texto):
    return [t for t in normalizar(texto).split() if len(t) > 1 and t not in STOPWORDS]


# ---------------------------------------------------------------------------
# Carga do acervo e fatiamento por artigo
# ---------------------------------------------------------------------------

def carregar_acervo():
    """Lê todas as normas e fatia o corpo em trechos (preâmbulo + artigos)."""
    trechos = []  # cada item: dict(arquivo, titulo, situacao, temas, fonte, rotulo, texto)
    for pasta, _, arquivos in os.walk(DIR_NORMAS):
        for nome in sorted(arquivos):
            if not nome.endswith(".md"):
                continue
            caminho = os.path.join(pasta, nome)
            bruto = open(caminho, encoding="utf-8").read()
            meta = {}
            corpo = bruto
            if bruto.startswith("---"):
                fim = bruto.find("\n---", 3)
                for linha in bruto[3:fim].splitlines():
                    m = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', linha)
                    if m:
                        meta[m.group(1)] = m.group(2)
                corpo = bruto[fim + 4:]
            rel = os.path.relpath(caminho, RAIZ)
            base = {
                "arquivo": rel,
                "titulo": meta.get("titulo", nome),
                "situacao": ("revogada" if "Revogada" in meta.get("situacao", "") else "vigente"),
                "ementa": meta.get("ementa", ""),
                "fonte": meta.get("fonte", ""),
            }
            # fatia por artigo (linhas que começam com "Art." — com ou sem negrito)
            padrao = re.compile(r"^(?:\*\*)?\s*Art\.?\s*[\d]", re.M)
            indices = [m.start() for m in padrao.finditer(corpo)]
            blocos = []
            if indices:
                blocos.append(("preâmbulo", corpo[: indices[0]]))
                for i, ini in enumerate(indices):
                    fim_b = indices[i + 1] if i + 1 < len(indices) else len(corpo)
                    bloco = corpo[ini:fim_b]
                    m = re.match(r"(?:\*\*)?\s*(Art\.?\s*[\d\w\.º°-]+)", bloco)
                    blocos.append((m.group(1) if m else f"trecho {i}", bloco))
            else:
                blocos.append(("íntegra", corpo))
            for rotulo, texto in blocos:
                texto = texto.strip()
                if len(texto) < 60:
                    continue
                # limita trechos gigantes (anexos, tabelas) a ~6000 chars
                for j in range(0, len(texto), 6000):
                    parte = texto[j: j + 6000]
                    trechos.append({**base, "rotulo": rotulo + (f" (cont. {j // 6000 + 1})" if j else ""), "texto": parte})
    return trechos


TRECHOS = carregar_acervo()
# frequência de documento por token, para ponderação IDF
_DF = Counter()
_TOKENS_TRECHO = []
for t in TRECHOS:
    toks = set(tokens_de(t["titulo"] + " " + t["ementa"] + " " + t["texto"]))
    _TOKENS_TRECHO.append(toks)
    _DF.update(toks)
_N = len(TRECHOS)


def pontuar(consulta, top=12):
    termos = tokens_de(consulta)
    if not termos:
        return []
    resultados = []
    for i, t in enumerate(TRECHOS):
        toks = _TOKENS_TRECHO[i]
        pontos = 0.0
        for termo in termos:
            if termo in toks:
                idf = math.log(_N / (1 + _DF[termo]))
                pontos += idf
                # reforço quando o termo aparece no título ou na ementa
                if termo in normalizar(t["titulo"]) or termo in normalizar(t["ementa"]):
                    pontos += idf
        if pontos > 0:
            if t["situacao"] == "vigente":
                pontos *= 1.15
            resultados.append((pontos, i))
    resultados.sort(reverse=True)
    return [(p, TRECHOS[i]) for p, i in resultados[:top]]


# ---------------------------------------------------------------------------
# Ferramentas expostas ao Claude
# ---------------------------------------------------------------------------
import anthropic
from anthropic import beta_tool


@beta_tool
def buscar_normas(termos: str) -> str:
    """Busca trechos relevantes no acervo de normas de licitações e contratações.

    Args:
        termos: Palavras-chave da busca (ex.: "antecipacao pagamento fornecedor").
            Use termos técnicos variados; repita a busca com sinônimos se necessário.
    """
    resultados = pontuar(termos, top=12)
    if not resultados:
        return "Nenhum trecho encontrado. Tente outros termos."
    saida = []
    for pontos, t in resultados:
        saida.append({
            "norma": t["titulo"],
            "trecho": t["rotulo"],
            "situacao": t["situacao"],
            "arquivo": t["arquivo"],
            "resumo": re.sub(r"\s+", " ", t["texto"])[:350],
        })
    return json.dumps(saida, ensure_ascii=False, indent=1)


@beta_tool
def ler_trecho(arquivo: str, rotulo: str = "") -> str:
    """Lê o texto integral de um trecho (artigo) ou de uma norma inteira do acervo.

    Args:
        arquivo: Caminho do arquivo retornado por buscar_normas (ex.: "normas/leis/lei-14133-2021.md").
        rotulo: Identificador do trecho retornado por buscar_normas (ex.: "Art. 75"). Vazio = norma completa (limitada a 30 mil caracteres).
    """
    candidatos = [t for t in TRECHOS if t["arquivo"] == arquivo]
    if not candidatos:
        return f"Arquivo não encontrado: {arquivo}"
    if rotulo:
        alvo = [t for t in candidatos if t["rotulo"].lower().startswith(rotulo.lower())]
        if alvo:
            cab = alvo[0]
            return f"{cab['titulo']} ({cab['situacao']}) — {cab['rotulo']}\nFonte: {cab['fonte']}\n\n" + "\n\n".join(t["texto"] for t in alvo)
    cab = candidatos[0]
    completo = "\n\n".join(t["texto"] for t in candidatos)
    return f"{cab['titulo']} ({cab['situacao']})\nFonte: {cab['fonte']}\n\n" + completo[:30000]


SISTEMA = """Você é um assistente especializado em licitações e contratações públicas \
federais do Brasil, respondendo a servidores públicos com base num acervo local de \
normas (leis, decretos, instruções normativas, portarias) coletado do Portal de \
Compras do Governo Federal.

Regras:
- Fundamente TODA resposta em trechos do acervo, obtidos com as ferramentas \
buscar_normas e ler_trecho. Busque mais de uma vez, com sinônimos, antes de concluir \
que algo não existe no acervo.
- Cite sempre a norma e o dispositivo (ex.: "art. 75, II, da Lei nº 14.133/2021") e \
liste ao final as normas consultadas com seus arquivos no acervo.
- Se um trecho relevante estiver marcado como revogado (situacao: revogada, ou texto \
~~riscado~~), avise explicitamente e procure a norma que o substituiu.
- Se o acervo não cobrir a pergunta, diga isso com clareza — não invente dispositivos.
- Este é um apoio à pesquisa, não parecer jurídico: em caso de dúvida relevante, \
recomende confirmar na fonte oficial ou com a assessoria jurídica.
- Responda em português, de forma clara e direta."""


def perguntar(client, pergunta, historico):
    historico.append({"role": "user", "content": pergunta})
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=[{"type": "text", "text": SISTEMA, "cache_control": {"type": "ephemeral"}}],
        tools=[buscar_normas, ler_trecho],
        messages=historico,
    )
    final = None
    for mensagem in runner:
        final = mensagem
        for bloco in mensagem.content:
            if bloco.type == "tool_use":
                print(f"  🔎 {bloco.name}({json.dumps(bloco.input, ensure_ascii=False)[:100]})")
        historico.append({"role": "assistant", "content": mensagem.content})
        resposta_tools = runner.generate_tool_call_response()
        if resposta_tools is not None:
            historico.append(resposta_tools)
    texto = "\n".join(b.text for b in final.content if b.type == "text")
    return texto, final.usage


ARQUIVO_CHAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chave.txt")


def obter_chave():
    """Obtém a chave de API: variável de ambiente, arquivo local ou pergunta ao usuário."""
    chave = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if chave:
        return chave
    if os.path.exists(ARQUIVO_CHAVE):
        chave = open(ARQUIVO_CHAVE, encoding="utf-8").read().strip()
        if chave:
            return chave
    print("Primeira execução: preciso da sua chave de API da Anthropic.")
    print("Crie uma em https://platform.claude.com/ (menu API Keys) e cole aqui.")
    print("(No Windows, cole com o botão direito do mouse ou Ctrl+V.)\n")
    while True:
        chave = input("Chave (começa com sk-ant-): ").strip().strip('"').strip("'")
        if chave.startswith("sk-ant-"):
            break
        print("Isso não parece uma chave válida — ela começa com sk-ant-. Tente de novo.")
    resposta = input("Salvar a chave neste computador para as próximas vezes? [s/n] ").strip().lower()
    if resposta.startswith("s"):
        with open(ARQUIVO_CHAVE, "w", encoding="utf-8") as f:
            f.write(chave + "\n")
        print(f"Salva em {ARQUIVO_CHAVE} — esse arquivo fica fora do controle de versão (não sobe para o GitHub).")
    return chave


def main():
    client = anthropic.Anthropic(api_key=obter_chave())
    print(f"📚 Normas Gerais — assistente de consulta ({len(TRECHOS)} trechos de {_N and len({t['arquivo'] for t in TRECHOS})} normas)")
    historico = []
    if len(sys.argv) > 1:
        perguntas = [" ".join(sys.argv[1:])]
    else:
        print("Digite sua pergunta (ou 'sair'):")
        perguntas = None
    while True:
        if perguntas is not None:
            if not perguntas:
                break
            pergunta = perguntas.pop(0)
            print(f"\n❓ {pergunta}")
        else:
            try:
                pergunta = input("\n❓ ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not pergunta or pergunta.lower() in ("sair", "exit", "quit"):
                break
        texto, uso = perguntar(client, pergunta, historico)
        print(f"\n{texto}")
        print(f"\n[tokens: {uso.input_tokens} entrada / {uso.output_tokens} saída]")


if __name__ == "__main__":
    main()
