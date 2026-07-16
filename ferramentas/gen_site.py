# -*- coding: utf-8 -*-
"""Gera o site estático de busca (docs/) a partir dos arquivos .md do acervo."""
import json
import os
import re

REPO = "/home/user/Claude"
GITHUB_BLOB = "https://github.com/ojefersonn/claude/blob/main/"


def carregar_normas():
    itens = []
    indice = json.load(open("indice_gerado.json"))
    for i in indice:
        caminho = os.path.join(REPO, i["arquivo"])
        texto = open(caminho, encoding="utf-8").read()
        # remove front matter e cabeçalho; corpo começa após o primeiro '---' isolado pós-cabeçalho
        corpo = texto.split("\n---\n", 2)[-1]
        # texto puro para busca (remove marcação markdown básica)
        plano = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", corpo)
        plano = re.sub(r"[#>*_`|~]", " ", plano)
        plano = re.sub(r"\s+", " ", plano).strip()
        itens.append({
            "t": i["nome"],
            "tp": i["tipo"],
            "e": i["ementa"],
            "tm": i["temas"],
            "s": "revogada" if "Revogada" in i["situacao"] else "vigente",
            "a": i["arquivo"],
            "u": i["url"],
            "x": plano,
        })
    return itens


HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Busca de Normas — Licitações e Contratações Públicas</title>
<style>
:root{
  --bg:#f6f7f9; --card:#ffffff; --texto:#1a1d21; --sub:#5b6570; --borda:#dde2e8;
  --realce:#fff3bf; --realce-t:#5f4b00; --acento:#155e9c; --acento-fraco:#e8f1fa;
  --revogada:#b02a2a; --revogada-bg:#fdeaea;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#14171b; --card:#1d2127; --texto:#e8eaed; --sub:#9aa4af; --borda:#333a43;
    --realce:#4d4423; --realce-t:#ffe58a; --acento:#6cb2f0; --acento-fraco:#20303f;
    --revogada:#ff8080; --revogada-bg:#3a2323;
  }
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Ubuntu,sans-serif;background:var(--bg);color:var(--texto);line-height:1.55}
.wrap{max-width:900px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.35rem;margin:0 0 4px}
.sub{color:var(--sub);font-size:.9rem;margin-bottom:20px}
.busca{position:sticky;top:0;background:var(--bg);padding:8px 0 12px;z-index:5}
input[type=search]{width:100%;padding:12px 14px;font-size:1.05rem;border:1.5px solid var(--borda);border-radius:10px;background:var(--card);color:var(--texto)}
input[type=search]:focus{outline:2px solid var(--acento);border-color:transparent}
.filtros{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
select{padding:7px 10px;border:1.5px solid var(--borda);border-radius:8px;background:var(--card);color:var(--texto);font-size:.9rem;max-width:100%}
.info{color:var(--sub);font-size:.88rem;margin:10px 2px}
.res{background:var(--card);border:1px solid var(--borda);border-radius:12px;padding:14px 16px;margin-bottom:12px}
.res h3{margin:0 0 4px;font-size:1.02rem}
.res h3 a{color:var(--acento);text-decoration:none}
.res h3 a:hover{text-decoration:underline}
.ementa{font-size:.9rem;color:var(--sub);margin:2px 0 8px}
.meta{font-size:.8rem;color:var(--sub);display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.tag{background:var(--acento-fraco);color:var(--acento);border-radius:20px;padding:2px 10px}
.tag.rev{background:var(--revogada-bg);color:var(--revogada);font-weight:600}
.trecho{font-size:.88rem;margin-top:8px;border-left:3px solid var(--borda);padding-left:10px;color:var(--texto)}
mark{background:var(--realce);color:var(--realce-t);border-radius:3px;padding:0 2px}
.fonte{font-size:.8rem}
.fonte a{color:var(--sub)}
.vazio{text-align:center;color:var(--sub);padding:40px 0}
.carregando{text-align:center;color:var(--sub);padding:40px 0}
</style>
</head>
<body>
<div class="wrap">
  <h1>📚 Busca de Normas — Licitações e Contratações Públicas</h1>
  <div class="sub">__N__ normas com texto integral pesquisável · capturadas do Portal de Compras do Governo Federal e fontes oficiais · atualizado em __DATA__</div>
  <div class="busca">
    <input type="search" id="q" placeholder="Busque no texto integral: ex. pesquisa de preços, garantia contratual, art. 75…" autofocus>
    <div class="filtros">
      <select id="ftema"><option value="">Todos os temas</option></select>
      <select id="ftipo"><option value="">Todos os tipos</option></select>
      <select id="fsit"><option value="">Vigentes e revogadas</option><option value="vigente">Somente vigentes</option><option value="revogada">Somente revogadas</option></select>
    </div>
  </div>
  <div class="info" id="info"></div>
  <div id="out"><div class="carregando">Carregando acervo…</div></div>
</div>
<script>
let DADOS=[];
const $=id=>document.getElementById(id);
const norm=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const STOP=new Set(['de','da','do','das','dos','e','em','no','na','nos','nas','o','a','os','as','um','uma','para','por','com','que','ao','aos','sobre','ou','se','sua','seu']);

fetch('dados.json').then(r=>r.json()).then(d=>{
  DADOS=d.map(n=>({...n, nx:norm(n.x), nt:norm(n.t+' '+n.e)}));
  const temas=[...new Set(d.flatMap(n=>n.tm))].sort((a,b)=>a.localeCompare(b,'pt'));
  for(const t of temas){const o=document.createElement('option');o.value=t;o.textContent=t;$('ftema').appendChild(o);}
  const tipos=[...new Set(d.map(n=>n.tp))].sort((a,b)=>a.localeCompare(b,'pt'));
  for(const t of tipos){const o=document.createElement('option');o.value=t;o.textContent=t;$('ftipo').appendChild(o);}
  render();
});

function trecho(n,termos){
  const nx=n.nx; let pos=-1, termoAchado='';
  for(const t of termos){const p=nx.indexOf(t); if(p>=0&&(pos<0||p<pos)){pos=p;termoAchado=t;}}
  if(pos<0)return '';
  const ini=Math.max(0,pos-140), fim=Math.min(n.x.length,pos+260);
  let s=(ini>0?'…':'')+n.x.slice(ini,fim)+(fim<n.x.length?'…':'');
  return marcar(s,termos);
}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function marcar(s,termos){
  s=esc(s); const sN=norm(s); const marcas=[];
  for(const t of termos){let i=0; while((i=sN.indexOf(t,i))>=0){marcas.push([i,i+t.length]); i+=t.length;}}
  if(!marcas.length)return s;
  marcas.sort((a,b)=>a[0]-b[0]);
  let out='',ult=0;
  for(const [a,b] of marcas){ if(a<ult)continue; out+=s.slice(ult,a)+'<mark>'+s.slice(a,b)+'</mark>'; ult=b;}
  return out+s.slice(ult);
}
function render(){
  const q=norm($('q').value.trim());
  const termos=q.split(/\\s+/).filter(t=>t.length>1&&!STOP.has(t));
  const tema=$('ftema').value, tipo=$('ftipo').value, sit=$('fsit').value;
  let res=DADOS.filter(n=>
    (!tema||n.tm.includes(tema)) && (!tipo||n.tp===tipo) && (!sit||n.s===sit) &&
    termos.every(t=>n.nx.includes(t)||n.nt.includes(t))
  );
  // título/ementa primeiro
  if(termos.length) res.sort((a,b)=>{
    const at=termos.every(t=>a.nt.includes(t))?0:1, bt=termos.every(t=>b.nt.includes(t))?0:1;
    return at-bt || a.t.localeCompare(b.t,'pt');
  });
  $('info').textContent=res.length+' norma'+(res.length===1?'':'s')+(termos.length?' encontradas para “'+$('q').value.trim()+'”':' no acervo');
  const LIM=60;
  $('out').innerHTML=res.length?res.slice(0,LIM).map(n=>`
    <div class="res">
      <h3><a href="${GH}${n.a}" target="_blank" rel="noopener">${marcar(n.t,termos)}</a></h3>
      <div class="ementa">${marcar(n.e||'',termos)}</div>
      ${termos.length?`<div class="trecho">${trecho(n,termos)}</div>`:''}
      <div class="meta">
        <span class="tag">${esc(n.tp)}</span>
        ${n.s==='revogada'?'<span class="tag rev">REVOGADA</span>':''}
        ${n.tm.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}
        <span class="fonte"><a href="${n.u}" target="_blank" rel="noopener">fonte oficial ↗</a></span>
      </div>
    </div>`).join('')+(res.length>LIM?`<div class="vazio">… e mais ${res.length-LIM}. Refine a busca.</div>`:'')
    :'<div class="vazio">Nenhuma norma encontrada. Tente outros termos ou remova filtros.</div>';
}
const GH='https://github.com/ojefersonn/claude/blob/main/';
let deb;
$('q').addEventListener('input',()=>{clearTimeout(deb);deb=setTimeout(render,150);});
for(const id of ['ftema','ftipo','fsit'])$(id).addEventListener('change',render);
</script>
</body>
</html>
"""


def main():
    import datetime
    itens = carregar_normas()
    os.makedirs(os.path.join(REPO, "docs"), exist_ok=True)
    json.dump(itens, open(os.path.join(REPO, "docs/dados.json"), "w", encoding="utf-8"), ensure_ascii=False)
    html = HTML.replace("__N__", str(len(itens))).replace("__DATA__", datetime.date.today().strftime("%d/%m/%Y"))
    open(os.path.join(REPO, "docs/index.html"), "w", encoding="utf-8").write(html)
    tam = os.path.getsize(os.path.join(REPO, "docs/dados.json")) / 1e6
    print(f"Site gerado: docs/index.html + docs/dados.json ({tam:.1f} MB, {len(itens)} normas)")


if __name__ == "__main__":
    main()
