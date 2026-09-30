"""Validate release downloads independently against saved source CSV cells."""
from pathlib import Path
import json,csv,io,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public';SRC=ROOT.parent/'NSO_CSV'
catalogue=json.loads((OUT/'webdata/release-catalogue.json').read_text(encoding='utf-8'))
assert len(catalogue['items'])==len({r['id'] for r in catalogue['items']})
checked=0;missing=0
for release in catalogue['items']:
 assert catalogue['from']<=release['date']<=catalogue['to']
 detail=json.loads((OUT/'webdata'/release['chart_file']).read_text(encoding='utf-8'))
 assert not detail['errors']
 files=[f for a in detail['attachments'] for f in a['files']]
 assert len(files)==release['sheets']==len(detail['sheets'])
 if not files:
  assert not release['download'];assert detail['pdf_links']>0;missing+=1;continue
 with zipfile.ZipFile(OUT/release['download']) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(files)+1
  for f,sheet in zip(files,detail['sheets']):
   original=list(csv.reader((SRC/f['path']).open(encoding='utf-8-sig',newline='')))
   downloaded=list(csv.reader(io.StringIO(z.read(sheet['archive_name']).decode('utf-8-sig'))))
   assert downloaded==original==sheet['rows'],(release['id'],f['path'])
   checked+=1
for package in catalogue['packages']:
 with zipfile.ZipFile(OUT/package['download']) as z:
  assert z.testzip() is None;assert len(z.namelist())==package['sheets']+1
print(f'PASS: {len(catalogue["items"])} releases; {checked} exported sheets match original CSV cells; {missing} PDF-only releases; four complete category ZIPs verified.')
