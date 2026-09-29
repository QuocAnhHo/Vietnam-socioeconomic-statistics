"""Source period, unit and name parsing; no aggregation or rescaling."""
import re,unicodedata

def norm(s):
 s=unicodedata.normalize('NFKD',s.replace('Đ','D').replace('đ','d').replace('Ð','D').replace('ð','d'))
 return re.sub('[^a-z0-9]','',s.encode('ascii','ignore').decode().lower())

PERIOD=re.compile(r'(?<!\d)(?:\d{1,2}/\d{1,2}/(?:19|20)\d{2}|(?:19|20)\d{2}\s*(?:over|/|-)\s*(?:(?:19|20)\d{2})|(?:19|20)\d{2})(?!\d)')

def period(header,title):
 m=PERIOD.search(header)
 if not m:
  m=PERIOD.search(title)
  if not m:
   bad=re.search(r'(?:Prel\.?\s*)?\d{5,}',header,re.I)
   if bad:return bad.group(),'', 'unresolved_source_period',header[bad.end():].strip() or 'Total','preliminary' if 'prel' in header.lower() else 'not_specified','malformed_source_header'
   raise ValueError('No period: '+header+' '+title)
  raw=m.group(); variant=header.strip();basis='table_title'
 else:raw=m.group();variant=(header[:m.start()]+header[m.end():]).strip();basis='column_header'
 status='preliminary' if re.search('prel',header,re.I) else 'estimated' if re.search(r'\bEst\.',header,re.I) else ('footnoted' if '*' in header else 'not_specified')
 variant=re.sub(r'\b(?:Prel|Est)\.?','',variant,flags=re.I).strip(' *') or 'Total'
 years=re.findall(r'(?:19|20)\d{2}',raw)
 if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}',raw):
  d,mo,y=raw.split('/');p=f'{y}-{int(mo):02}-{int(d):02}';kind='point_in_time'
 elif len(years)==2:
  kind='comparison' if ('over' in raw or '/' in raw) else 'academic_year'
  p=re.sub(r'\s+','',raw) if kind=='academic_year' else '/'.join(years)
 else:p=raw;kind='annual'
 return p,years[0],kind,variant,status,basis

def unit_for(id,v,default):
 fixes={'E0101':'administrative units','E0310':'index (previous year = 100)','E1319':'pupils per class','E1320':'pupils per teacher','E1437':'index','E1439':'index','E1484':'persons'}
 if id in fixes:return fixes[id],'indicator_definition'
 if id=='E0201':
  return ('km2' if v.startswith('Area') else 'thousand persons' if 'population (Thous' in v else 'persons per km2'),'column_header'
 if id=='E1303':return ({'School':'schools','Class':'classes'}.get(v,'thousand pupils' if 'Thous' in v else 'persons')),'column_header'
 units=re.findall(r'\(([^()]*)\)',v)
 for u in reversed(units):
  if re.search(r'%|person|pers\.|case|dongs?|dong|copies|unit|ton|zone|cluster|time|pupil|km|ha|bed',u,re.I):return u.strip(),'column_header'
 if default and default!='a':
  try:default=default.encode('latin1').decode('utf-8')
  except (UnicodeEncodeError,UnicodeDecodeError):pass
  return default,'download_metadata'
 return '', 'not_available'
