# 🤖 Assistente de consulta às normas (protótipo RAG)

Assistente de linha de comando que responde perguntas em linguagem natural sobre
as normas do acervo, **citando norma e artigo**. Usa a abordagem de "RAG
agêntico": o modelo Claude recebe duas ferramentas — buscar trechos no acervo e
ler o texto integral de um dispositivo — e as usa quantas vezes precisar antes
de responder. Não requer banco vetorial nem serviço de embeddings: a busca é
local, sobre os arquivos `normas/*.md`, fatiados por artigo.

## Requisitos

- Python 3.9+ com o SDK da Anthropic: `pip install anthropic`
- Uma chave de API da Anthropic (crie em <https://platform.claude.com/> —
  o uso é cobrado por token; uma consulta típica custa poucos centavos de dólar)
- O acervo clonado (este repositório)

## Como usar

```bash
# modo interativo (mantém o contexto entre perguntas)
python3 assistente/assistente.py

# ou pergunta única
python3 assistente/assistente.py "Posso contratar por dispensa de licitação até qual valor?"
```

Na **primeira execução** o assistente pede a chave de API e oferece salvá-la em
`assistente/chave.txt` (arquivo local, fora do controle de versão) — nas
próximas execuções ele a encontra sozinho. Alternativamente, a variável de
ambiente `ANTHROPIC_API_KEY`, se definida, tem prioridade.

Exemplo de saída:

```
❓ É permitido pagamento antecipado a fornecedor?
  🔎 buscar_normas({"termos": "pagamento antecipado fornecedor antecipação"})
  🔎 ler_trecho({"arquivo": "normas/instrucoes-normativas/instrucao-normativa-53-2020.md"})

Sim, em caráter excepcional. A Instrução Normativa nº 53/2020 disciplina...
(resposta com citações e lista das normas consultadas)
```

## Como funciona

1. **Indexação local** — na inicialização, o script lê as 217 normas, fatia o
   texto por artigo (~3.200 trechos) e monta um índice de termos com ponderação
   IDF, insensível a acentos, com reforço para ocorrências no título/ementa e
   para normas vigentes.
2. **Ferramentas** — o Claude recebe `buscar_normas(termos)` (retorna os 12
   trechos mais relevantes com metadados) e `ler_trecho(arquivo, rotulo)`
   (texto integral do artigo ou da norma).
3. **Laço agêntico** — o SDK executa o laço de chamadas de ferramenta
   automaticamente (`tool_runner`); o modelo busca, lê, busca de novo com
   sinônimos se necessário e só então redige a resposta.
4. **Salvaguardas no prompt** — obrigação de citar dispositivo, alerta para
   normas/trechos revogados e instrução para admitir quando o acervo não
   cobre a pergunta. É apoio à pesquisa, **não substitui parecer jurídico**.

## Custos e modelo

O padrão é o modelo `claude-opus-4-8` com pensamento adaptativo, priorizando a
qualidade da resposta. Para reduzir custo em consultas simples, edite
`assistente.py` e troque o modelo por `claude-haiku-4-5` (mais rápido e
barato) ou ajuste `output_config`/`effort` conforme a documentação da API.

## Evoluções possíveis

- **Interface web** (a mesma lógica atrás de um formulário simples)
- **Busca semântica com embeddings** (ex.: Voyage AI) se as buscas por
  palavras-chave se mostrarem insuficientes para perguntas muito leigas
- **Avaliação sistemática**: monte uma lista de perguntas reais do setor com
  respostas esperadas e compare periodicamente
