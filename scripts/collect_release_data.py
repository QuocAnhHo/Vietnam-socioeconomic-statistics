"""Match five years of official release spreadsheets to saved CSVs before downloading."""
from pathlib import Path
import json,csv,io,re,html,hashlib,zipfile,sys,threading,urllib.parse,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from collect_publications import fetch
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'NSO_CSV';OUT=ROOT/'public';QA=ROOT/'qa/release-review';QA.mkdir(parents=True,exist_ok=True)
RECORDS=json.loads((SRC/'_audit/attachment_results.json').read_text(encoding='utf-8'));BY_ID={r['id']:r for r in RECORDS}
def canon(u):return urllib.parse.unquote(html.unescape(u)).split('?')[0].replace('http://','https://')
EXISTING={canon(r['source_url']):r for r in RECORDS};LOCK=threading.Lock()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def files_for(url):
 r=EXISTING.get(canon(url))
 if r and r['status']=='duplicate':r=BY_ID.get(r['duplicate_of'])
 if r and r['status']=='converted' and all((SRC/f['path']).exists() for f in r['files']):
  return r['files'],'reused',r.get('source_sha256','')
 # Missing files alone are fetched. Conversion uses cached source values, never formulas.
 key=hashlib.sha256(url.encode()).hexdigest()[:16];mp=QA/(key+'-attachment.json')
 with LOCK:
  if mp.exists():
   d=json.loads(mp.read_text(encoding='utf-8'));return d['files'],'reused',d['sha256']
  sys.path.insert(0,str(ROOT.parent/'scripts'))
  from download_nso_attachments import convert
  req=urllib.request.Request(urllib.parse.quote(url,safe=':/?=&%+'),headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=60) as response:blob=response.read()
  cache=QA/(key+Path(urllib.parse.urlparse(url).path).suffix);cache.write_bytes(blob)
  files=convert(blob,SRC/'release_additions'/key,url)
  if not files:raise ValueError('No readable sheets: '+url)
  digest=hashlib.sha256(blob).hexdigest();save(mp,{'url':url,'files':files,'sha256':digest})
  return files,'downloaded',digest
def process(item):
 rid=item['archive']+'-'+hashlib.sha256(item['url'].encode()).hexdigest()[:12];mp=QA/(rid+'.json')
 if mp.exists():
  old=json.loads(mp.read_text(encoding='utf-8'))
  if not old.get('errors'):return old
 result={**item,'id':rid,'attachments':[],'errors':[],'sheets':[],'series':[],'reason':'These release spreadsheets retain their original multi-row headings. Select a sheet, its column-label row and a numeric value column to chart the original observations.'}
 try:
  text=fetch(item['url']);links=re.findall(r'''(?:href|src)=["']([^"']+)["']''',text,re.I)
  urls=list(dict.fromkeys(urllib.parse.urljoin(item['url'],html.unescape(u)) for u in links if re.search(r'\.(?:xlsx?|csv|zip)(?:[?#]|$)',u,re.I)))
  urls=[u for u in urls if urllib.parse.urlparse(u).hostname in ['www.nso.gov.vn','nso.gov.vn']]
  result['spreadsheet_links']=urls;result['pdf_links']=sum(bool(re.search(r'\.pdf(?:[?#]|$)',u,re.I)) for u in links)
  for ai,url in enumerate(urls):
   try:
    files,action,digest=files_for(url)
    attachment={'url':url,'action':action,'sha256':digest,'files':files};result['attachments'].append(attachment)
    for si,f in enumerate(files):
     rows=list(csv.reader((SRC/f['path']).open(encoding='utf-8-sig',newline='')))
     result['sheets'].append({'name':Path(urllib.parse.urlparse(url).path).name+' · '+f.get('sheet',str(si+1)),'rows':rows,'archive_name':f'{ai+1:02d}-{si+1:03d}-'+Path(f['path']).name,'source_url':url})
   except Exception as e:result['errors'].append({'url':url,'error':str(e)})
 except Exception as e:result['errors'].append({'url':item['url'],'error':str(e)})
 save(mp,result);return result
def csvbytes(rows):
 s=io.StringIO(newline='');csv.writer(s).writerows(rows);return s.getvalue().encode('utf-8-sig')
def main():
 publication=json.loads((OUT/'webdata/publications.json').read_text(encoding='utf-8'))
 items=[r for r in publication['items'] if r['archive']!='publication' and '2021-09-30'<=r['date']<='2026-09-30']
 results=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  futures=[pool.submit(process,r) for r in items]
  for f in as_completed(futures):
   r=f.result();results.append(r)
   if len(results)%10==0 or r['errors']:print('Reviewed',len(results),'/',len(items),'errors',sum(len(x['errors']) for x in results),flush=True)
 results.sort(key=lambda r:r['date'],reverse=True);catalogue=[];category_packages=[]
 for r in results:
  name='downloads/releases/'+r['id']+'.zip';r['download']=name if r['sheets'] else None
  if r['sheets']:
   p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
   with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for sheet in r['sheets']:z.writestr(sheet['archive_name'],csvbytes(sheet['rows']))
    z.writestr('sources.csv',csvbytes([['file','source_url','release_url','issue_date']]+[[s['archive_name'],s['source_url'],r['url'],r['date']] for s in r['sheets']]))
  r['chart_file']='release-details/'+r['id']+'.json';r['source_id']=r['id'];r['source_url']=r['url']
  r['coverage_note']='No spreadsheet attachment is linked from this release page.' if not r['sheets'] else 'All sheets from the linked spreadsheet attachments are included.'
  save(OUT/'webdata'/r['chart_file'],r)
  catalogue.append({k:r[k] for k in ['id','title','date','url','archive','download','chart_file','coverage_note'] }|{'sheets':len(r['sheets']),'errors':len(r['errors'])})
 for archive in ['monthly-report','cpi','iip','import-export']:
  group=[r for r in results if r['archive']==archive];name='downloads/releases/'+archive+'-2021-2026.zip';p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
  included=set();manifest=[['file','release_url','issue_date','spreadsheet_url']]
  with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
   for r in group:
    for s in r['sheets']:
     key=(s['source_url'],s['archive_name'])
     if key in included:continue
     included.add(key);filename=r['date']+'-'+r['id']+'/'+s['archive_name'];z.writestr(filename,csvbytes(s['rows']));manifest.append([filename,r['url'],r['date'],s['source_url']])
   z.writestr('sources.csv',csvbytes(manifest))
  category_packages.append({'archive':archive,'download':name,'releases':len(group),'sheets':len(included)})
 summary={'enabled':True,'from':'2021-09-30','to':'2026-09-30','checked':'2026-09-30','items':catalogue,'packages':category_packages}
 save(OUT/'webdata/release-catalogue.json',summary)
 audit={'releases':len(results),'with_spreadsheets':sum(bool(r['sheets']) for r in results),'sheets':sum(len(r['sheets']) for r in results),'reused_attachments':sum(a['action']=='reused' for r in results for a in r['attachments']),'downloaded_attachments':sum(a['action']=='downloaded' for r in results for a in r['attachments']),'errors':[e for r in results for e in r['errors']],'packages':category_packages}
 save(OUT/'webdata/release-validation.json',audit);print(json.dumps(audit),flush=True)
 if audit['errors']:raise SystemExit('Release review has unresolved errors; rerun to retry failed entries.')
if __name__=='__main__':main()
