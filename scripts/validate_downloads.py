"""Reconcile exported indicator CSV cells and representative complete tables."""
from pathlib import Path
import csv,json,zipfile,io
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'public/webdata'
cat=json.loads((WEB/'catalogue.json').read_text(encoding='utf-8'));count=0
for i in cat['indicators']:
 rows=json.loads((WEB/'series'/(i['indicator_id']+'.json')).read_text(encoding='utf-8'))
 out=list(csv.DictReader((ROOT/'public/downloads/indicators'/(i['indicator_id']+'.csv')).open(encoding='utf-8-sig',newline='')))
 assert len(rows)==len(out)
 for original,exported in zip(rows,out):
  assert original[0]==exported['province_code'] and original[1]==exported['period']
  assert (float(exported['value']) if exported['value'] else None)==original[2]
 count+=len(out)
full=json.loads((WEB/'full-catalogue.json').read_text(encoding='utf-8'))
for id in ['E0201','E0301','attachment-62384']:
 s=next(x for x in full['sources'] if x['source_id']==id)
 rows=list(csv.reader((ROOT/'public'/s['download']).open(encoding='utf-8-sig',newline='')))
 original=json.loads((WEB/s['preview_file']).read_text(encoding='utf-8'))
 assert len(rows)==original['total_rows'] and rows[:len(original['rows'])]==original['rows']
sample=next(s for s in full['sources'] if s['csv_files']>10)
with zipfile.ZipFile(ROOT/'public'/sample['download']) as z:assert len(z.namelist())==sample['csv_files'] and z.testzip() is None
print('PASS:',count,'indicator observations match CSV exports; complete national/provincial tables and multi-sheet ZIP verified.')
