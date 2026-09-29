from collect_publications import fetch,OUT
import json,re,html
from concurrent.futures import ThreadPoolExecutor
p=OUT/'publications.json';data=json.loads(p.read_text(encoding='utf-8'));items=[i for i in data['items'] if i['archive']=='publication']
def verify(i):
 s=fetch(i['url']);title=re.search(r'<h1[^>]*>(.*?)</h1>',s,re.S)
 if not title:raise ValueError('Missing publication title '+i['url'])
 links=[html.unescape(x) for x in re.findall(r'''(?:href|src)=["']([^"']+)''',s) if re.search(r'\.(pdf|zip|xlsx?|docx?)(?:[?#]|$)',x,re.I)]
 return {'url':i['url'],'title_found':True,'download_links':list(dict.fromkeys(links))}
with ThreadPoolExecutor(max_workers=4) as pool:verified=list(pool.map(verify,items))
(OUT/'publication-validation.json').write_text(json.dumps({'checked':'2026-09-29','entries':verified},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Publication pages verified',len(verified),'with visible file links',sum(bool(r['download_links']) for r in verified))
