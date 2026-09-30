import React,{useEffect,useState} from 'react';
import {ChevronRight,ArrowRight,Search} from 'lucide-react';
import {loadData,format,TOPICS} from './data';
import {StatisticsLayout,SUBJECT_GROUPS,RELEASES,topics,topicLabel} from './StatisticsNavigation';
const descriptions=Object.fromEntries(TOPICS.map(t=>[t[0],t[2]]));
const releaseDescriptions={
 'monthly-report':'Monthly economic and social statistics, with all available spreadsheet tables.',
 cpi:'Consumer prices, gold prices and US dollar exchange-rate indexes.',
 iip:'Industrial production indexes and source breakdowns.',
 'import-export':'Preliminary merchandise trade values and related tables.'
};
export function StatisticsCatalogue({params}){
 const[data,setData]=useState(null),[releases,setReleases]=useState(null),[error,setError]=useState('');
 const topic=params.get('topic')||'',group=params.get('group')||'',search=params.get('q')||'';
 const landing=!topic&&!search&&params.get('view')!=='datasets';
 const[q,setQ]=useState(search),[page,setPage]=useState(1),[year,setYear]=useState('all'),[activeGroup,setActiveGroup]=useState(group||'people');
 useEffect(()=>{loadData('full-catalogue.json').then(setData).catch(e=>setError(e.message));loadData('release-catalogue.json').then(setReleases).catch(e=>setError(e.message))},[]);
 useEffect(()=>{setQ(search);setPage(1);setYear('all');if(!landing)window.scrollTo(0,0)},[topic,search,landing]);
 useEffect(()=>setPage(1),[q,year]);
 function scrollToGroup(id){
  setActiveGroup(id);
  requestAnimationFrame(()=>document.getElementById('statistics-section-'+id)?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'}));
 }
 useEffect(()=>{if(landing&&group)scrollToGroup(group)},[group,landing]);
 useEffect(()=>{
  if(!landing)return;
  let frame=0;
  function update(){
   const sections=[...document.querySelectorAll('[data-statistics-section]')];
   let current=sections[0];for(const section of sections)if(section.getBoundingClientRect().top<=155)current=section;
   if(window.scrollY+window.innerHeight>=document.documentElement.scrollHeight-8)current=sections.at(-1);
   if(current)setActiveGroup(current.dataset.statisticsSection);frame=0;
  }
  function schedule(){if(!frame)frame=requestAnimationFrame(update)}
  window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);schedule();
  return()=>{window.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule);cancelAnimationFrame(frame)};
 },[landing]);
 const sources=(data?.sources||[]).filter(s=>topics.some(t=>t[0]===s.section));
 const isRelease=RELEASES.some(t=>t[0]===topic),pack=releases?.packages?.find(p=>p.archive===topic);
 const collection=isRelease?(releases?.items||[]).filter(s=>s.archive===topic):sources.filter(s=>!topic||s.section===topic);
 const filtered=collection.filter(s=>(!isRelease||year==='all'||s.date.startsWith(year))&&(s.title+' '+(s.source_id||'')).toLowerCase().includes(q.toLowerCase()));
 const size=25,pages=Math.max(1,Math.ceil(filtered.length/size));
 return <main className="statistics-page"><div className="wrap statistics-breadcrumb breadcrumb"><a href="#/">Home</a><ChevronRight size={14}/>{landing?'Statistics':<><a href="#/statistics">Statistics</a><ChevronRight size={14}/>{topic?topicLabel(topic):'Search results'}</>}</div>
 <StatisticsLayout topic={topic} activeGroup={activeGroup} landing={landing} onGroup={scrollToGroup}>
 <h1>{landing?'Statistics':topic?topicLabel(topic):'Search statistics'}</h1>
 {landing?<><p className="intro">Browse statistics by subject. Select a topic to explore its datasets, charts and complete downloads.</p><form className="statistics-landing-search catalogue-search" onSubmit={e=>{e.preventDefault();location.hash='/statistics?q='+encodeURIComponent(q)+'&view=datasets'}}><Search size={19}/><input aria-label="Search all statistics" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search datasets or indicators…"/><button type="submit">Search</button></form>
 {SUBJECT_GROUPS.map(([id,label,children])=><section className="statistics-category" id={'statistics-section-'+id} data-statistics-section={id} key={id} aria-labelledby={'statistics-heading-'+id}><h2 id={'statistics-heading-'+id}>{label}</h2><div className="statistics-topic-cards">{children.map(([tid,title])=><a className="statistics-topic-card" href={'#/statistics?topic='+tid} key={tid}><h3>{title}</h3><p>{descriptions[tid]}</p><ArrowRight size={21} aria-hidden="true"/></a>)}</div></section>)}
 {RELEASES.map(([id,label])=><section className="statistics-category" id={'statistics-section-'+id} data-statistics-section={id} key={id} aria-labelledby={'statistics-heading-'+id}><h2 id={'statistics-heading-'+id}>{label}</h2><div className="statistics-topic-cards"><a className="statistics-topic-card statistics-release-card" href={'#/statistics?topic='+id}><h3>Browse releases and data</h3><p>{releaseDescriptions[id]}</p><span>Five years of releases and complete data downloads</span><ArrowRight size={21} aria-hidden="true"/></a></div></section>)}
 </>:<><a className="text-link statistics-back" href="#/statistics">Browse all topics</a><p className="intro">{isRelease?releaseDescriptions[topic]:descriptions[topic]||'Find datasets by their original NSO titles or table IDs.'}</p>
 {isRelease&&<div className="release-category-tools"><label>Issue year<select aria-label="Release year" value={year} onChange={e=>setYear(e.target.value)}><option value="all">All years</option>{[...new Set((releases?.items||[]).filter(r=>r.archive===topic).map(r=>r.date.slice(0,4)))].sort().reverse().map(y=><option key={y}>{y}</option>)}</select></label>{pack&&<a className="button secondary" href={import.meta.env.BASE_URL+pack.download} download>Download all five years (CSV ZIP)</a>}</div>}
 <div className="catalogue-search"><Search size={19}/><input aria-label="Search datasets" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search original NSO titles or table IDs…"/></div>
 {error?<p role="alert">{error}</p>:!data||(isRelease&&!releases)?<p role="status">Loading statistics…</p>:<><div className="catalogue-toolbar"><p role="status">{format(filtered.length,0)} {isRelease?'releases':'datasets'}</p><span>{size} per page</span></div><div className="compact-dataset-list">{filtered.slice((page-1)*size,page*size).map(s=><a className="compact-dataset-row" key={s.source_id||s.id} href={isRelease?'#/release/'+s.id:'#/dataset/'+s.source_id}><div><h3>{s.title}</h3><p>{isRelease?s.date:[s.source_id,s.periods?.length?s.periods[0]+'–'+s.periods.at(-1):'',s.chart_series?`${s.chart_series} series`:'Source table'].filter(Boolean).join(' · ')}</p></div><ChevronRight size={18}/></a>)}</div>{!filtered.length&&<p className="empty">No datasets match your search.</p>}<div className="pagination"><button className="button secondary" disabled={page<=1} onClick={()=>setPage(page-1)}>Previous</button><span>Page {page} of {pages}</span><button className="button secondary" disabled={page>=pages} onClick={()=>setPage(page+1)}>Next</button></div></>}
 </>}
 </StatisticsLayout></main>;
}
