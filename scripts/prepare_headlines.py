"""Reviewed headline values, latest available NSO reference periods as of 2026-09-29."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'NSO_CSV'
def grid(p,encoding='utf-8-sig'):return list(csv.reader((SRC/p).open(encoding=encoding,newline='')))
pop=grid('population/E0201.csv','iso-8859-15');h=pop[2];r=next(r for r in pop if r and r[0].strip()=='WHOLE COUNTRY');population=float(r[h.index('2025 Average population (Thous. pers.)')])/1000
gdp=grid('national_account/E0301.csv','iso-8859-15');gdp_pc=float(next(r for r in gdp if r and 'foreign currency' in r[0])[-1])
trade_url='https://www.nso.gov.vn/en/data-and-statistics/2026/03/exports-and-imports-value-by-months-of-2026/'
monthly='https://www.nso.gov.vn/en/data-and-statistics/2026/09/report-socio-economic-performance-in-august-and-8-months-of-2026/'
quarter='https://www.nso.gov.vn/en/data-and-statistics/2026/08/report-socio-economic-performance-in-second-quarter-and-the-first-half-of-2026/'
cpi='https://www.nso.gov.vn/en/data-and-statistics/2026/09/consumer-price-index-gold-price-index-and-us-dollar-price-index-in-august-and-eight-months-of-2026/'
items=[
 {'id':'population','label':'Population','value':population,'unit':'million people','period':'2025 · annual average','basis':'National total from table E0201.','source_url':'https://www.nso.gov.vn/en/px-web?pxid=E0201&theme=Population%20and%20Employment'},
 {'id':'gdp_per_capita','label':'GDP per capita','value':gdp_pc,'unit':'USD per person','decimals':0,'period':'2025 · estimated','basis':'Current prices; average exchange rate. Table E0301.','source_url':'https://www.nso.gov.vn/en/px-web?pxid=E0301&theme=National%20Accounts%20and%20State%20budget'},
 {'id':'gdp_growth','label':'GDP growth','value':8.39,'prefix':'+','unit':'% year on year','period':'Q2 2026 · estimated','basis':'Latest quarter versus Q2 2025. First-half growth: 8.18%.','source_url':quarter},
 {'id':'fdi','label':'FDI investment · YTD','value':17.25,'unit':'billion USD disbursed','period':'January–August 2026 · estimated','basis':'Realised inward FDI. Registered inward investment: USD 40.63 billion.','source_url':monthly},
]
for filename,id,label in [('data_attachments/2026/62384_E01_2026/001_1.csv','exports','Exports · YTD'),('data_attachments/2026/62385_E02_2026/001_2.csv','imports','Imports · YTD')]:
 rows=grid(filename);assert ('Exports' if id=='exports' else 'Imports').lower() in rows[0][0].lower(),rows[0]
 row=next(r for r in rows if r and r[0].strip()=='Total');value=float(row[-1])/1_000_000
 items.append({'id':id,'label':label,'value':value,'unit':'billion USD','period':'January–August 2026 · preliminary','basis':('Goods, FOB valuation.' if id=='exports' else 'Goods, CIF valuation.')+' Release dated 19 September 2026.','source_url':trade_url,'source_file':filename,'source_value_thousand_usd':row[-1]})
items.append({'id':'cpi','label':'Consumer price index','value':104.89,'unit':'index · August 2025 = 100','period':'August 2026','basis':'Equivalent to +4.89% year on year; +0.47% month on month. Index rebased from NSO’s reported annual change.','source_url':cpi})
(ROOT/'public/webdata/latest-headlines.json').write_text(json.dumps({'checked':'2026-09-29','items':items},ensure_ascii=False,indent=2),encoding='utf-8')
print([(i['id'],i['value']) for i in items])
