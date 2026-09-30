import React,{useEffect,useState} from 'react';
import {ChevronDown,Menu} from 'lucide-react';
export const SUBJECT_GROUPS=[
 ['people','Population and employment',[['population','Population'],['employment','Employment']]],
 ['accounts','National accounts and finance',[['national_account','National accounts'],['banking_insurance_budget','Banking, insurance and State budget']]],
 ['economy','Economy',[['agriculture','Agriculture, Forestry and Fishery'],['investment','Investment and Construction'],['industry','Industry'],['enterprises','Enterprises'],['trade_services','Trade and Tourism'],['prices','Prices']]],
 ['society','Society, environment and territory',[['education','Science and technology, education'],['health_culture_environment','Health, Culture, Sport, Living standards, Social order, Safety and Environment'],['administration_land_climate','Administrative unit, Land and Climate']]],
];
export const RELEASES=[['monthly-report','Socio-economic monthly report'],['cpi','CPI, gold and USD price indexes'],['iip','Index of Industrial Production'],['import-export','Preliminary Exports and Imports']];
export const topics=SUBJECT_GROUPS.flatMap(g=>g[2]);
export const topicLabel=id=>topics.find(t=>t[0]===id)?.[1]||RELEASES.find(t=>t[0]===id)?.[1]||id;
export const groupForTopic=topic=>SUBJECT_GROUPS.find(g=>g[2].some(t=>t[0]===topic))?.[0]||topic;

export function StatisticsLayout({children,topic='',activeGroup='',landing=false,onGroup}){
 const selected=topic?groupForTopic(topic):activeGroup;
 const[expanded,setExpanded]=useState(()=>topic?{[groupForTopic(topic)]:true}:{});
 const[mobileOpen,setMobileOpen]=useState(false);
 useEffect(()=>{if(topic)setExpanded(old=>({...old,[groupForTopic(topic)]:true}));setMobileOpen(false)},[topic]);
 function visit(e,id){setMobileOpen(false);if(landing&&onGroup){e.preventDefault();onGroup(id)}}
 return <div className="wrap statistics-layout"><aside className="statistics-sidebar"><div className="statistics-nav-panel"><button className="statistics-mobile-toggle" aria-expanded={mobileOpen} aria-controls="statistics-navigation" onClick={()=>setMobileOpen(!mobileOpen)}><Menu size={19}/>Browse statistics<ChevronDown size={18}/></button><h2 className="statistics-nav-title">Browse statistics</h2><nav id="statistics-navigation" aria-label="Statistics topics" className={mobileOpen?'is-open':''}>
 <a className="statistics-overview-link" href="#/statistics" onClick={e=>{setMobileOpen(false);if(landing){e.preventDefault();window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}}} aria-current={landing?'page':undefined}>All statistics</a>
 {SUBJECT_GROUPS.map(([id,label,children])=><div className={'statistics-nav-group '+(selected===id?'is-active':'')} key={id}><div className="statistics-nav-row"><a href={'#/statistics?group='+id} onClick={e=>visit(e,id)} aria-current={selected===id?'location':undefined}>{label}</a><button aria-label={`${expanded[id]?'Collapse':'Expand'} ${label}`} aria-expanded={!!expanded[id]} aria-controls={'statistics-submenu-'+id} onClick={()=>setExpanded(old=>({...old,[id]:!old[id]}))}><ChevronDown size={17}/></button></div><ul id={'statistics-submenu-'+id} hidden={!expanded[id]}>{children.map(([tid,title])=><li key={tid}><a href={'#/statistics?topic='+tid} aria-current={topic===tid?'page':undefined} onClick={()=>setMobileOpen(false)}>{title}</a></li>)}</ul></div>)}
 <p className="statistics-nav-caption">Statistical releases</p>{RELEASES.map(([id,label])=><div className={'statistics-nav-group '+(selected===id?'is-active':'')} key={id}><div className="statistics-nav-row release-row"><a href={landing?'#/statistics?group='+id:'#/statistics?topic='+id} onClick={e=>visit(e,id)} aria-current={selected===id?(landing?'location':'page'):undefined}>{label}</a></div></div>)}
 </nav></div></aside><div className="statistics-content">{children}</div></div>;
}
