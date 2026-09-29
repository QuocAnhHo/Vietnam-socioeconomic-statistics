from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'public/webdata/catalogue.json';c=json.loads(p.read_text(encoding='utf-8'))
original={i['indicator_id'] for i in __import__('csv').DictReader((ROOT/'data/indicators.csv').open(encoding='utf-8-sig'))}
for i in c['indicators']:
 if i['indicator_id'] in original:continue
 title=re.split(r' by Cities,| by Province, city| by Items and| by Items,| by item and',i['indicator'])[0].strip()
 i['label']=title+(' · '+i['breakdown'] if i['breakdown']!='Total' else '')
for s in c['sources']:s['title']=re.split(r' by Cities,| by Province, city| by Items and| by item and',s['title'])[0].strip()
p.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Metadata refined; indicators',len(c['indicators']))
