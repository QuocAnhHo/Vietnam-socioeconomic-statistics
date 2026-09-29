import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {ranked,periodRows,mapCode,mapAllowed,csvText} from '../src/data.js';
const read=n=>JSON.parse(fs.readFileSync(new URL('../public/webdata/'+n,import.meta.url),'utf8'));
test('population source values and complete 2024 map coverage',()=>{
 const rows=read('series/e0201_1deb527311.json');const current=periodRows(rows,'2024');
 assert.equal(current.length,63);assert.equal(current.find(r=>r[0]==='VN_SRC_HANOI')[2],8717.63);
 assert.equal(ranked(current)[0][0],'VN_SRC_HOCHIMINHCITY');assert.equal(ranked(current)[0][2],9543.63);
 const map=read('provinces.geojson');assert.equal(map.features.length,63);
 assert.deepEqual(new Set(current.map(r=>mapCode(r[0]))),new Set(map.features.map(f=>f.properties.code)));
});
test('missing data and negative rates retain their meaning',()=>{
 const rows=[['a','2024',null],['b','2024',0],['c','2024',-2],['d','2024',3]];
 assert.deepEqual(ranked(rows).map(r=>r[0]),['d','b','c']);
 assert.match(csvText(['value'],[[null],[0],[-2]]),/""\r\n"0"\r\n"-2"$/);
});
test('historical geography limits prevent current map implication',()=>{
 assert.equal(mapAllowed('2024'),true);assert.equal(mapAllowed('2009'),true);
 assert.equal(mapAllowed('2008'),false);assert.equal(mapAllowed('2025'),false);
 assert.equal(mapAllowed('Prel. 20204'),false);assert.equal(mapCode('VN_SRC_HUE'),'VN_SRC_THUATHIENHUE');
});
test('all catalogue series exist and observation totals reconcile',()=>{
 const c=read('catalogue.json');assert.equal(c.indicators.length,364);assert.equal(new Set(c.indicators.map(i=>i.section)).size,13);
 assert.ok(!c.indicators.some(i=>['E0637','E0638'].includes(i.source_id)),'Longan fruit must not be classified as Long An province');
 let count=0;const provinces=new Set(c.provinces.map(p=>p.province_code));
 for(const i of c.indicators){const rows=read('series/'+i.indicator_id+'.json');count+=rows.length;
  assert.equal(new Set(rows.map(r=>r[0]+'|'+r[1])).size,rows.length);
  for(const r of rows){assert.ok(provinces.has(r[0]));assert.ok(r[2]===null||Number.isFinite(r[2]));}
  assert.ok(i.periods.every(p=>!p.includes('20204')));
 }
 assert.equal(count,283619);assert.equal(count,c.observations);assert.equal(c.indicators.filter(i=>i.section==='population').length,32);
});
test('national headline comes from supplied national source row',()=>{
 const h=read('latest-headlines.json');const items=Object.fromEntries(h.items.map(i=>[i.id,i]));assert.equal(h.items.length,7);assert.equal(items.population.value,102.34532);assert.equal(items.gdp_per_capita.value,5025.85);assert.equal(items.exports.value,374.836705918);assert.equal(items.imports.value,395.29826637);assert.match(items.cpi.unit,/2025 = 100/);
});
test('complete catalogue retains national data and packages every CSV',()=>{
 const c=read('full-catalogue.json');assert.equal(c.sources.length,4025);assert.equal(c.sources.reduce((n,s)=>n+s.csv_files,0),16588);
 assert.equal(c.sources.find(s=>s.source_id==='PLE0301').section,'national_account');
 for(const s of c.sources){assert.ok(fs.existsSync(new URL('../public/'+s.download,import.meta.url)));assert.ok(fs.existsSync(new URL('../public/webdata/'+s.preview_file,import.meta.url)));}
 const rows=read('tables/E0201.json').rows;assert.ok(rows.some(r=>r[0]?.trim()==='WHOLE COUNTRY'));assert.ok(rows.some(r=>r[0]?.trim()==='Red River Delta'));assert.ok(rows[2].some(v=>v.includes('2025 Average population')));
});
test('publication index is dated, unique and points to official detail pages',()=>{
 const p=read('publications.json');assert.equal(p.items.length,226);assert.equal(new Set(p.items.map(i=>i.url)).size,p.items.length);
 for(const i of p.items){assert.ok(i.date>=p.from&&i.date<=p.to);assert.ok(i.url.startsWith('https://www.nso.gov.vn/en/'));assert.ok(i.title);}
 assert.equal(p.items.filter(i=>i.category==='Publications').length,40);
});
