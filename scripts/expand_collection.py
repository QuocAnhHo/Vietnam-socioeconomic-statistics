"""Package the existing complete CSV collection and extend provincial dashboard data.
No network downloads; source values and all original sheets are preserved.
"""
from pathlib import Path
import csv,io,json,re,hashlib,zipfile,sys,collections,shutil
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'NSO_CSV';OUT=ROOT/'public/webdata';DOWNLOAD=ROOT/'public/downloads';DOWNLOAD.mkdir(exist_ok=True)
from province_source_parser import norm,period,unit_for
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def grid(x):
 b=(SRC/x['path']).read_bytes().rstrip(b'\x00');enc='utf-8-sig' if 'UTF' in x['encoding'].upper() else 'iso-8859-15'
 return list(csv.reader(io.StringIO(b.decode(enc))))
def encoded(rows):
 f=io.StringIO(newline='');w=csv.writer(f);w.writerows(rows);return f.getvalue().encode('utf-8-sig')
cat=read(SRC/'data_catalog.csv');groups=collections.defaultdict(list)
for x in cat:groups[(x['source_kind'],x['id'])].append(x)
topics={'population','employment','national_account','banking_insurance_budget','education','health_culture_environment','administration_land_climate','agriculture','investment','industry','enterprises','trade_services','prices'}
def section(x):
 if x['section'] in topics:return x['section']
 raw=norm(x['section'])
 for terms,s in [('nationalaccounts','national_account'),('population','population'),('enterprise','enterprises'),('investment','investment'),('industry|congnghiep','industry'),('agriculture|nongnghiep','agriculture'),('education|giaoduc','education'),('health|yte','health_culture_environment'),('administrative','administration_land_climate'),('trade|touris|transport|thuongmai','trade_services'),('cpi','prices')]:
  if re.search(terms,raw):return s
 t=(x['section']+' '+x['title']).lower()
 for terms,s in [('national account|domestic product','national_account'),('cpi|consumer price|producer price|spatial cost','prices'),('enterprise','enterprises'),('population','population'),('employment|labour','employment'),('investment|construction','investment'),('industry|industrial','industry'),('agriculture|forestry|fishery','agriculture'),('trade|touris|transport|postal','trade_services'),('education','education'),('health|living standard|culture','health_culture_environment'),('administrative|climate','administration_land_climate')]:
  if re.search(terms,t):return s
 return 'nsdp' if x['source_kind']=='NSDP' else 'other_collection'
full=[];manifest=[]
if '--catalogue-only' in sys.argv:
 data=json.loads((OUT/'full-catalogue.json').read_text(encoding='utf-8'))
 for s in data['sources']:s['section']=section(groups[(s['source_kind'],s['original_id'])][0])
 save(OUT/'full-catalogue.json',data);print('Catalogue topics refreshed');sys.exit(0)
for (kind,id),xs in ([] if '--dashboard-only' in sys.argv else groups.items()):
 x=xs[0];sid=id if kind=='PX-Web' else ('attachment-' if kind=='Excel attachment' else 'vi-' if kind=='PX-Web Vietnamese' else 'nsdp-')+re.sub(r'[^a-zA-Z0-9_-]','_',id)
 ext='csv' if len(xs)==1 else 'zip';target=DOWNLOAD/(sid+'.'+ext)
 if len(xs)==1:
  rows=grid(x);target.write_bytes(encoded(rows))
 else:
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
   for j,a in enumerate(xs):
    # Preserve original sheet names; prefix avoids duplicate names across workbooks in an attachment.
    z.writestr(f'{j+1:04d}-'+Path(a['path']).name,encoded(grid(a)))
  rows=grid(x)
 title=x['title'];header=next((j for j,r in enumerate(rows) if len(r)>1),0)
 if kind.startswith('PX-Web') and rows and len(rows[0])==1:title=rows[0][0]
 periods=sorted(set(re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',' '.join(' '.join(r) for r in rows[:header+2]))))
 entry={'source_id':sid,'original_id':id,'title':title,'section':section(x),'source_kind':kind,'source_url':x['source_url'],'data_url':x['data_url'],'periods':periods,'sheets':len(xs),'download':'downloads/'+target.name,'download_format':ext.upper(),'bytes':target.stat().st_size,'preview_file':'tables/'+sid+'.json','csv_files':len(xs)}
 # Native tables can be browsed in full; attachment previews are deliberately bounded and labelled.
 preview=rows if kind.startswith('PX-Web') or kind=='NSDP' else rows[:40]
 save(OUT/entry['preview_file'],{'rows':preview,'total_rows':len(rows),'preview_only':len(preview)<len(rows),'sheet':x['sheet'],'sheets':[a['sheet'] or Path(a['path']).stem for a in xs],'columns':max(map(len,rows),default=0)})
 full.append(entry);manifest.extend({'dataset':sid,'path':a['path'],'sha256':a['sha256']} for a in xs)
assert len({s['source_id'] for s in full})==len(full)
if '--dashboard-only' not in sys.argv:
 save(OUT/'full-catalogue.json',{'sources':full,'csv_files':len(cat),'snapshot':'2026-09-27','scope':'Complete downloaded collection; national, regional, provincial and other source breakdowns retained.'})
 save(ROOT/'collection_manifest.json',manifest)
else:full=json.loads((OUT/'full-catalogue.json').read_text(encoding='utf-8'))['sources']
print('Complete collection:',len(full),'datasets,',len(cat),'CSV files',flush=True)

# Existing validated seven-section package remains authoritative and unchanged.
dashboard=json.loads((OUT/'catalogue.json').read_text(encoding='utf-8'))
existing={s['source_id'] for s in dashboard['sources']};geo={norm(p['province_name']):p for p in dashboard['provinces']};geo['hochiminh']=geo['hochiminhcity'];geo['tphochiminh']=geo['hochiminhcity']
metadata={x['id']:x for x in read(ROOT/'collection_metadata.csv')};issues=[];added=0
for x in cat:
 if x['source_kind']!='PX-Web' or x['section'] not in topics or x['id'] in existing:continue
 rows=grid(x);title=rows[0][0];hi=next(j for j,r in enumerate(rows) if len(r)>1);headers=rows[hi];meta=metadata.get(x['id'],{});nstub=int(meta.get('stub_columns') or 1)
 if re.search(r'\bstation|\briver',title,re.I):continue
 # A name match alone is not geographic evidence: the fruit "longan" collides with Long An.
 if not re.search(r'provinc|cities|localit',title+' '+' '.join(headers[:nstub]),re.I):continue
 matches=[]
 for r in rows[hi+1:]:
  found=[(j,geo[norm(v)]) for j,v in enumerate(r[:nstub]) if norm(v) in geo]
  if len(found)==1:matches.append((r,*found[0]))
 if not matches:continue
 series={};bad=None
 for r,geocol,g in matches:
  if len(r)!=len(headers):bad='Unequal row width';break
  for ci in range(nstub,len(headers)):
   try:p,y,kind,variant,status,basis=period(headers[ci],title)
   except ValueError as e:bad=str(e);break
   other=' · '.join(v.strip() for j,v in enumerate(r[:nstub]) if j!=geocol)
   variant=' · '.join(v for v in [other,variant if variant!='Total' else ''] if v) or 'Total'
   iid=x['id'].lower().replace('-','_')+'_'+hashlib.sha256(variant.encode()).hexdigest()[:10]
   unit,ub=unit_for(x['id'],variant,meta.get('unit',''))
   if 'Mill. USD' in variant:unit,ub='million USD','column_header'
   elif variant=='Number of projects':unit,ub='projects','column_header'
   if x['id']=='E1114':unit,ub='index (Ha Noi = 100)','source_title'
   if iid not in series:series[iid]={'indicator_id':iid,'section':x['section'],'source_id':x['id'],'indicator':title,'label':title+(' · '+variant if variant!='Total' else ''),'breakdown':variant,'unit':unit,'unit_display':unit or 'Unit not specified by source','unit_basis':ub,'default_dashboard_eligible':str(bool(unit)).lower(),'quality_flags':'' if unit else 'unit_unavailable','rows':[]}
   raw=r[ci].strip()
   try:v=float(raw);assert __import__('math').isfinite(v)
   except (ValueError,AssertionError):v=None
   series[iid]['rows'].append([g['province_code'],p,v,status,kind])
  if bad:break
 if bad:issues.append({'source_id':x['id'],'reason':bad});continue
 inds=[];allperiods=set();count=0
 for iid,i in series.items():
  rr=i.pop('rows');keys=[(r[0],r[1]) for r in rr]
  if len(set(keys))!=len(keys):raise ValueError('Duplicate dashboard observations '+iid)
  i['periods']=sorted({r[1] for r in rr if r[4]!='unresolved_source_period'});allperiods.update(i['periods']);count+=len(rr)
  save(OUT/'series'/f'{iid}.json',rr);dashboard['indicators'].append(i);inds.append(iid)
 dashboard['sources'].append({'source_id':x['id'],'section':x['section'],'title':title,'source_url':x['source_url'],'indicators':inds,'periods':sorted(allperiods),'observations':count,'quality_flags':''})
 dashboard['observations']+=count;added+=len(inds)
save(OUT/'catalogue.json',dashboard)
save(OUT/'collection-validation.json',{'datasets':len(full),'source_csv_files':len(cat),'packaged_csv_files':sum(s['csv_files'] for s in full),'dashboard_indicators':len(dashboard['indicators']),'dashboard_observations':dashboard['observations'],'added_indicators':added,'excluded_dashboard_tables':issues,'sections':dict(collections.Counter(i['section'] for i in dashboard['indicators']))})
print('Dashboard:',len(dashboard['indicators']),'indicators;',dashboard['observations'],'observations; issues:',issues,flush=True)
