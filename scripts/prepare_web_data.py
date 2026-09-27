"""Prepare the website from the committed, validated data. Python standard library only."""
from pathlib import Path
import csv,json,re,hashlib
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public'/'webdata';OUT.mkdir(parents=True,exist_ok=True)
def read(name):return list(csv.DictReader((ROOT/'data'/name).open(encoding='utf-8-sig')))
def save(name,obj):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
sources=read('sources.csv'); indicators=read('indicators.csv'); rows=read('observations.csv')
groups=defaultdict(list)
for r in rows:groups[r['indicator_id']].append([r['province_code'],r['period'],float(r['value']) if r['value'] else None,r['period_status'],r['period_type']])
labels={
'E0201':{'Area (Km2(*)':'Land area','Average population (Thous. pers.)':'Average population','Population density (Person/km2)':'Population density'},
'E0203-07':{'Total':'Average population · total','Male':'Male population','Female':'Female population','Urban':'Urban population','Rural':'Rural population'},
'E0209':{'Total':'Sex ratio'},'E0212-14':{'Crude birth rate':'Crude birth rate','Crude death rate':'Crude death rate','Natural increase rate':'Natural increase rate'},
'E0216':{'Total':'Total fertility rate'},'E0218':{'Total':'Infant mortality rate'},'E0219':{'Total':'Under-five mortality rate'},'E0220':{'Total':'Population growth rate'},
'E0221-23':{'Immigration rate':'In-migration rate','Emigration rate':'Out-migration rate','Net - emigration rate':'Net migration rate'},'E0225':{'Total':'Life expectancy at birth'},'E0227':{'Total':'Literacy rate · ages 15+'},
'E0228':{'Total':'Registered marriages','1st marriage':'First marriages','2nd marriage and subsequent marriages':'Second and subsequent marriages'},
'E0230':{'Total':'Mean age at marriage'},'E0231':{'Total':'Finalised divorces','Provincial level':'Finalised divorces · provincial courts','District level':'Finalised divorces · district courts'},
'E0233':{'Total':'Birth registration · children under 5'},'E0234':{'Total':'Registered deaths','Timely registration':'Deaths registered on time','Late registration':'Deaths registered late'}}
for s in sources:
 s['title']=re.split(r' by Cities,| by Province, city| by Items and| by item and',s['title'])[0].replace('(*)','').strip()
 ss=[i for i in indicators if i['source_id']==s['source_id']]
 s['indicators']=[i['indicator_id'] for i in ss]
 s['periods']=sorted({r[1] for i in ss for r in groups[i['indicator_id']] if r[4]!='unresolved_source_period'})
 s['observations']=sum(len(groups[i['indicator_id']]) for i in ss)
 for i in ss:
  i['label']=labels.get(i['source_id'],{}).get(i['breakdown'],s['title']+(' · '+i['breakdown'] if i['breakdown']!='Total' else ''))
  i['periods']=sorted({r[1] for r in groups[i['indicator_id']] if r[4]!='unresolved_source_period'})
  i['unit_display']={'Thous. persons':'thousand people','thousand persons':'thousand people','Age':'years','Case':'cases','Person':'people','‰':'per 1,000 people','Males per 100 females':'males per 100 females','Children per woman':'children per woman','Infant deaths per 1000 live births':'deaths per 1,000 live births','Under five deaths per 1000 live births':'deaths per 1,000 live births','persons per km2':'people per km²','km2':'km²'}.get(i['unit'],i['unit'])
  if i['source_id']=='E0221-23':i['note']='Migration rates retain the source measure and scale. The source calls the net series “Net - emigration rate”; no sign inversion is applied.'
  save('series/'+i['indicator_id']+'.json',groups[i['indicator_id']])
save('catalogue.json',{'sources':sources,'indicators':indicators,'provinces':read('provinces.csv'),'snapshot':'September 2026','observations':len(rows)})
# Exact, reviewed name crosswalk to the 2020 63-province reference map.
geo=json.loads((ROOT/'map_sources/provinces.geojson').read_text(encoding='utf-8'))
known={x['province_code'] for x in read('provinces.csv')};cross=[]
for f in geo['features']:
 n=f['properties']['shapeName']; key=re.sub('[^A-Z0-9]','',n.upper())
 if n in ['Hai Phong city','Da Nang city','Can Tho city']:key=key.removesuffix('CITY')
 code='VN_SRC_'+key;assert code in known,(n,code)
 f['properties']={'name':n,'code':code}
 cross.append({'map_name':n,'province_code':code,'match':'normalised exact name'})
assert len(geo['features'])==63 and len({f['properties']['code'] for f in geo['features']})==63
# Round coordinate precision only; retain all rings and source polygons.
def rounding(x):return [rounding(v) for v in x] if isinstance(x,list) else round(x,5) if isinstance(x,float) else x
for f in geo['features']:f['geometry']['coordinates']=rounding(f['geometry']['coordinates'])
save('provinces.geojson',geo)
cross.append({'map_name':'Thua Thien Hue','province_code':'VN_SRC_HUE','match':'display alias only; no data aggregation','source':'https://xaydungchinhsach.chinhphu.vn/nghi-quyet-so-175-2024-qh15-thanh-lap-thanh-pho-hue-truc-thuoc-trung-uong-119241205102339073.htm'})
save('geography-crosswalk.json',cross)
save('map-metadata.json',json.loads((ROOT/'map_sources/metadata.json').read_text(encoding='utf-8')))
# Homepage national figure comes from the original national row, not a provincial sum.
p=ROOT/'data/sources/population/E0201.csv';raw=list(csv.reader(p.read_bytes().rstrip(b'\x00').decode('iso-8859-15').splitlines()))
h=raw[2];country=next(r for r in raw if r and r[0].strip()=='WHOLE COUNTRY')
stats={h[j]:float(country[j]) for j in range(1,len(h)) if h[j].startswith('2024')}
save('headlines.json',{'year':2024,'population_thousand':stats['2024 Average population (Thous. pers.)'],'density':stats['2024 Population density (Person/km2)'],'source_id':'E0201','source_url':next(s['source_url'] for s in sources if s['source_id']=='E0201')})
report={'source_observations':len(rows),'series_files':len(groups),'map_features':len(geo['features']),'matched_map_names':63,'population_series':sum(i['section']=='population' for i in indicators),'sha256_source_observations':hashlib.sha256((ROOT/'data/observations.csv').read_bytes()).hexdigest()}
save('build-validation.json',report);print(json.dumps(report))
