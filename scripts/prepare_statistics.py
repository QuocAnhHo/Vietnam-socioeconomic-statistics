"""Build chartable source series without restricting geography or aggregating values."""
from pathlib import Path
import csv,json,re,math,collections,zipfile,io
from province_source_parser import period,unit_for
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'public/webdata'; SRC=ROOT.parent/'NSO_CSV'
def save(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def number(s):
 try:
  v=float(str(s).strip());return v if math.isfinite(v) else None
 except (ValueError,TypeError):return None
def build_chart(rows,source,meta):
 native=source['source_kind'].startswith('PX-Web')
 if not rows:return {'series':[],'reason':'The source sheet contains no rows.'}
 if native:
  hi=next((j for j,r in enumerate(rows) if len(r)>1),0)
  stub=int(meta.get('stub_columns') or 1)
 else:
  # Only use explicitly selected source columns for irregular spreadsheets.
  return {'series':[],'reason':'This spreadsheet has a multi-row or mixed-unit layout. Select a numeric column in the source table chart below; its original labels and units are preserved.'}
 header=rows[hi];series=collections.OrderedDict();expected=0
 yearcol=next((j for j,h in enumerate(header[:stub]) if re.search(r'^(year|years|năm|thời gian)$',h.strip(),re.I)),None)
 for ri,row in enumerate(rows[hi+1:],hi+1):
  if len(row)!=len(header):continue
  for ci in range(stub,len(header)):
   raw=row[ci];v=number(raw)
   if v is not None:expected+=1
   try:
    ph=row[yearcol] if yearcol is not None else header[ci]
    p,y,kind,variant,status,basis=period(ph,'')
   except ValueError:continue
   parts=[x.strip() for j,x in enumerate(row[:stub]) if j!=yearcol and x.strip()]
   if yearcol is not None:parts.append(header[ci])
   elif variant!='Total':parts.append(variant)
   label=' · '.join(parts) or source['title']
   unit,ub=unit_for(source['original_id'],label,meta.get('unit',''))
   if 'ICOR' in label:unit='ratio'
   key=(label,unit)
   if key not in series:series[key]={'label':label,'unit':unit or 'See the source definition for units','unit_known':bool(unit),'points':[]}
   series[key]['points'].append([p,v,status,ri,ci])
 result=list(series.values());valid=[]
 for s in result:
  if not any(p[1] is not None for p in s['points']):continue
  if len({p[0] for p in s['points']})!=len(s['points']):
   # Do not silently merge distinct observations with duplicate labels.
   return {'series':[],'reason':'The source has repeated period labels. Use the source column chart to inspect values without combining observations.'}
  s['points'].sort(key=lambda p:p[0]);valid.append(s)
 count=sum(p[1] is not None for s in valid for p in s['points'])
 return {'series':valid,'numeric_cells':expected,'charted_cells':count,'reason':'' if valid else 'No unambiguous time series was identified. Use the source column chart to inspect the table.'}
def main():
 full=json.loads((OUT/'full-catalogue.json').read_text(encoding='utf-8'))
 metadata={r['id']:r for r in csv.DictReader((ROOT/'collection_metadata.csv').open(encoding='utf-8-sig'))}
 originals={(r['source_kind'],r['id']):r for r in csv.DictReader((SRC/'data_catalog.csv').open(encoding='utf-8-sig'))}
 audit=[]
 for s in full['sources']:
  original=originals.get((s['source_kind'],s['original_id']))
  if original:
   s.setdefault('csv_title',s['title']);s['title']=original['title']
  if s['section'] in ['nsdp','other_collection']:continue
  data=json.loads((OUT/s['preview_file']).read_text(encoding='utf-8'))
  meta=metadata.get(s['original_id'],{})
  chart=build_chart(data['rows'],s,meta)
  if not chart['series']:
   path=ROOT/'public'/s['download'];sheets=[]
   if path.suffix=='.zip':
    with zipfile.ZipFile(path) as z:
     for name in z.namelist():
      if name.endswith('.csv'):sheets.append({'name':name,'rows':list(csv.reader(io.StringIO(z.read(name).decode('utf-8-sig'))))})
   else:sheets=[{'name':data.get('sheet') or s['title'],'rows':list(csv.reader(path.open(encoding='utf-8-sig',newline='')))}]
   chart['sheets']=sheets
  chart['source_id']=s['source_id'];chart['title']=s['title'];chart['source_title']=s.get('csv_title',s['title']);chart['unit']=meta.get('unit','')
  chart['notes']=[r[0] for r in data['rows'] if len(r)==1 and r[0]!=data['rows'][0][0]]
  s['chart_file']='charts/'+s['source_id']+'.json'
  periods=sorted({p[0] for series in chart['series'] for p in series['points']})
  if periods:s['periods']=periods
  s['chart_series']=len(chart['series'])
  save(OUT/s['chart_file'],chart)
  audit.append({'id':s['source_id'],'series':len(chart['series']),'numeric_cells':chart.get('numeric_cells'),'charted_cells':chart.get('charted_cells'),'fallback_reason':chart['reason']})
 save(OUT/'full-catalogue.json',full);save(OUT/'statistics-audit.json',audit)
 print('Reviewed',len(audit),'datasets;',sum(bool(s['series']) for s in audit),'with automatic time series;',sum(s['series'] for s in audit),'series')
if __name__=='__main__':main()
