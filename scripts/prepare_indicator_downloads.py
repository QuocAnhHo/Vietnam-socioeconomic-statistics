"""Create complete, same-origin CSV downloads for every dashboard indicator."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'public/webdata';OUT=ROOT/'public/downloads/indicators';OUT.mkdir(parents=True,exist_ok=True)
cat=json.loads((WEB/'catalogue.json').read_text(encoding='utf-8'));sources={s['source_id']:s for s in cat['sources']};names={p['province_code']:p['province_name'] for p in cat['provinces']}
fields=['indicator_id','section','indicator','breakdown','province_code','province','period','period_type','value','unit','period_status','source_id','source_url','geography_version']
for i in cat['indicators']:
 rows=json.loads((WEB/'series'/(i['indicator_id']+'.json')).read_text(encoding='utf-8'))
 with (OUT/(i['indicator_id']+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.writer(f);writer.writerow(fields)
  writer.writerows([i['indicator_id'],i['section'],i['label'],i['breakdown'],r[0],names[r[0]],r[1],r[4],r[2],i['unit'],r[3],i['source_id'],sources[i['source_id']]['source_url'],'source_reported_unharmonized'] for r in rows)
print('Complete indicator downloads:',len(cat['indicators']))
