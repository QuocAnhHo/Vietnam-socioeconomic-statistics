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
 const c=read('catalogue.json');assert.equal(c.sources.length,91);assert.equal(c.indicators.length,231);
 let count=0;const provinces=new Set(c.provinces.map(p=>p.province_code));
 for(const i of c.indicators){const rows=read('series/'+i.indicator_id+'.json');count+=rows.length;
  assert.equal(new Set(rows.map(r=>r[0]+'|'+r[1])).size,rows.length);
  for(const r of rows){assert.ok(provinces.has(r[0]));assert.ok(r[2]===null||Number.isFinite(r[2]));}
  assert.ok(i.periods.every(p=>!p.includes('20204')));
 }
 assert.equal(count,161709);assert.equal(c.indicators.filter(i=>i.section==='population').length,32);
});
test('national headline comes from supplied national source row',()=>{
 const h=read('headlines.json');assert.equal(h.population_thousand,101343.75);assert.equal(h.density,305.86);assert.equal(h.year,2024);
});
