"""Index official English NSO archive entries; leave publications on NSO servers."""
from pathlib import Path
import urllib.request,urllib.error,json,re,html,time
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'qa'/'nso-pages';CACHE.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'public/webdata'
START='2021-09-29';END='2026-09-29'
ARCHIVES={'publication':'Publications','monthly-report':'Socio-economic reports','cpi':'CPI, gold & USD indexes','iip':'Industrial production','import-export':'Exports & imports'}
def fetch(url):
 import hashlib
 p=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.html')
 if p.exists():return p.read_text(encoding='utf-8')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:s=r.read().decode('utf-8')
   p.write_text(s,encoding='utf-8');return s
  except Exception:
   if attempt==2:raise
   time.sleep(2)
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def archive(slug):
 rows=[];page=1
 while True:
  url='https://www.nso.gov.vn/en/'+slug+'/' + ('?paged='+str(page) if page>1 else '')
  text=fetch(url)
  entries=re.findall(r'<a\s+href="([^"]+)"[^>]*>\s*(?:</p>\s*)?<section class="item">(.*?)</section>',text,re.S)
  if not entries:raise ValueError('No archive entries '+url)
  dates=[]
  for link,body in entries:
   title=re.search(r'<h3[^>]*>(.*?)</h3>',body,re.S);date=re.search(r'Date of issue:\s*(\d{2})/(\d{2})/(\d{4})',body)
   if not title or not date:raise ValueError('Missing title/date '+link)
   d,m,y=date.groups();date=f'{y}-{m}-{d}';dates.append(date)
   if START<=date<=END:rows.append({'title':clean(title.group(1)),'date':date,'url':html.unescape(link),'category':ARCHIVES[slug],'archive':slug})
  print(slug,page,len(rows),flush=True)
  if min(dates)<START or not re.search(r'[?&]paged='+str(page+1)+r'\b',html.unescape(text)):break
  page+=1
 return rows
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=3) as pool:groups=list(pool.map(archive,ARCHIVES))
 rows=list({r['url']:r for group in groups for r in group}.values())
 rows.sort(key=lambda r:r['date'],reverse=True)
 result={'checked':'2026-09-29','from':START,'to':END,'coverage':'Entries in the English NSO publication and four statistical release archives, by issue date. Links open the corresponding NSO publication/download page.','items':rows}
 (OUT/'publications.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('TOTAL',len(rows),flush=True)
