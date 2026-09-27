export const REPO='https://github.com/QuocAnhHo/Vietnam-socio-economics-statistics';
export const RELEASE=`${REPO}/releases/tag/data-2026-09-28`;
export const RAW='https://raw.githubusercontent.com/QuocAnhHo/Vietnam-socio-economics-statistics/main/data/';
export const TOPICS=[['population','Population','People, births, migration and households'],['employment','Employment','Labour force, jobs and participation'],['national_account','National accounts','Provincial output and GRDP per capita'],['banking_insurance_budget','Insurance & public finance','Social, health and unemployment insurance'],['education','Education','Schools, teachers and students'],['health_culture_environment','Health, society & environment','Health services, living conditions and environment'],['administration_land_climate','Administration & land','Administrative units and land use']];
export const DEFAULT_INDICATOR='e0201_1deb527311';
const cache=new Map();
export async function loadData(file){if(!cache.has(file))cache.set(file,fetch(`${import.meta.env.BASE_URL}webdata/${file}`).then(r=>{if(!r.ok)throw new Error('Could not load this dataset. Please try again.');return r.json()}).catch(e=>{cache.delete(file);throw e}));return cache.get(file)}
export function format(v,max=2){return v==null?'Not available':new Intl.NumberFormat('en-GB',{maximumFractionDigits:max}).format(v)}
export function periodRows(rows,period){return rows.filter(r=>r[1]===period)}
export function ranked(rows){return rows.filter(r=>r[2]!=null).slice().sort((a,b)=>b[2]-a[2]||a[0].localeCompare(b[0]))}
export function csvText(headers,rows){const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';return '\uFEFF'+[headers,...rows].map(r=>r.map(q).join(',')).join('\r\n')}
export function downloadCSV(name,headers,rows){const blob=new Blob([csvText(headers,rows)],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000)}
export function mapCode(code){return code==='VN_SRC_HUE'?'VN_SRC_THUATHIENHUE':code}
export function mapAllowed(year){return /^\d{4}$/.test(year)&&Number(year)>=2009&&Number(year)<=2024}
export function route(){let [path,query='']=location.hash.slice(1).split('?');return {path:path||'/',params:new URLSearchParams(query)}}
export function go(path,params={}){const q=new URLSearchParams(Object.entries(params).filter(([,v])=>v!=null&&v!==''));location.hash=path+(q.size?'?'+q:'')}
