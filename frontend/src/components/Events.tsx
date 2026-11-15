import { useCallback, useEffect, useState, FormEvent } from "react";
import { CalendarDays, MapPin, Plus, RefreshCw, Ticket, Users, Pencil, Trash2 } from "lucide-react";

type Props = { tokens: { access: string; refresh: string }; onTokens: (v: { access: string; refresh: string }) => void; searchQuery?: string };
type Team = { id: number; nome: string };
type EventItem = { id: number; torcida: number; torcida_nome: string; titulo: string; descricao: string; tipo: string; local: string; inicio_em: string; fim_em: string | null; capacidade: number | null; valor: string; status: string; criado_por_nome: string };
const API = import.meta.env.VITE_API_URL || "";
const empty = { torcida: "", titulo: "", descricao: "", tipo: "encontro", local: "", inicio_em: "", fim_em: "", capacidade: "", valor: "0", status: "publicado" };
const money = (v: string) => Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const date = (v: string) => new Date(v).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

export default function Events({ tokens, onTokens, searchQuery = "" }: Props) {
 const [teams,setTeams]=useState<Team[]>([]);
 const [items,setItems]=useState<EventItem[]>([]);
 const [form,setForm]=useState(empty);
 const [editing,setEditing]=useState<number|null>(null);
 const [showForm,setShowForm]=useState(false);
 const [loading,setLoading]=useState(true);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [notice,setNotice]=useState("");
 const [filter,setFilter]=useState("todos");
 const [ticketStates,setTicketStates]=useState<Record<number,{pode_entrar:boolean;ingressos:any[]}>>({});
 const [ticketBusy,setTicketBusy]=useState<number|null>(null);

 const api=useCallback(async(path:string,init:RequestInit={})=>{
  let token=tokens.access;
  const send=()=>fetch(API+path,{...init,headers:{...(init.body instanceof FormData?{}:{"Content-Type":"application/json"}),Authorization:"Bearer "+token,...init.headers}});
  let response=await send();
  if(response.status===401&&tokens.refresh){
   const refreshed=await fetch(API+"/api/auth/refresh/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({refresh:tokens.refresh})});
   if(refreshed.ok){const data=await refreshed.json();token=data.access;onTokens({access:data.access,refresh:data.refresh||tokens.refresh});response=await send();}
  }
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(data.detail||Object.values(data).flat().join(" ")||"Não foi possível concluir.");
  return data;
 },[tokens.access,tokens.refresh,onTokens]);

 const load=useCallback(async()=>{
  setLoading(true);setError("");
  try{
   const [t,e]=await Promise.all([api("/api/torcidas/"),api("/api/eventos/")]);
   const teamList:Team[]=Array.isArray(t)?t:(t.results||[]);
   const eventList:EventItem[]=Array.isArray(e)?e:(e.results||[]);
   setTeams(teamList);setItems(eventList);
   setForm(v=>({...v,torcida:v.torcida||String(teamList[0]?.id||"")}));
  }catch(e){setError(e instanceof Error?e.message:"Falha ao carregar agenda.");}
  finally{setLoading(false);}
 },[api]);
 useEffect(()=>{void load();},[load]);
 useEffect(()=>{items.filter(x=>x.status==="publicado").forEach(x=>{if(!ticketStates[x.id])void loadTicket(x.id);});},[items]);


 async function loadTicket(eventId:number){
  try{const d=await api("/api/eventos/"+eventId+"/ingresso/");setTicketStates(v=>({...v,[eventId]:d}));}catch{/* O ingresso ainda não foi consultado. */}
 }
 async function buyTicket(item:EventItem){
  setTicketBusy(item.id);setError("");setNotice("");
  try{
   const d=await api("/api/eventos/"+item.id+"/ingresso/",{method:"POST",body:JSON.stringify({quantidade:1,metodo_pagamento:"pix"})});
   if(d.checkout_url){window.location.href=d.checkout_url;return;}
   setNotice("Ingresso gratuito confirmado. Guarde o código: "+d.codigo);
   await loadTicket(item.id);
  }catch(e){setError(e instanceof Error?e.message:"Não foi possível emitir o ingresso.");}
  finally{setTicketBusy(null);}
 }

 function startEdit(item:EventItem){
  setEditing(item.id);setShowForm(true);
  const localDate=(v:string)=>{const d=new Date(v);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);};
  setForm({torcida:String(item.torcida),titulo:item.titulo,descricao:item.descricao,tipo:item.tipo,local:item.local,inicio_em:localDate(item.inicio_em),fim_em:item.fim_em?localDate(item.fim_em):"",capacidade:item.capacidade?String(item.capacidade):"",valor:String(item.valor),status:item.status});
 }
 function newEvent(){setEditing(null);setForm({...empty,torcida:String(teams[0]?.id||"")});setShowForm(true);setError("");setNotice("");}
 async function save(e:FormEvent){
  e.preventDefault();setBusy(true);setError("");setNotice("");
  try{
   if(!form.titulo.trim()||!form.inicio_em)throw new Error("Informe o título e a data de início.");
   if(form.fim_em&&new Date(form.fim_em)<=new Date(form.inicio_em))throw new Error("O término precisa ser posterior ao início.");
   const payload={...form,torcida:Number(form.torcida),inicio_em:new Date(form.inicio_em).toISOString(),fim_em:form.fim_em?new Date(form.fim_em).toISOString():null,capacidade:form.capacidade?Number(form.capacidade):null,valor:Number(form.valor||0)};
   await api(editing?"/api/eventos/"+editing+"/":"/api/eventos/",{method:editing?"PATCH":"POST",body:JSON.stringify(payload)});
   setNotice(editing?"Evento atualizado.":"Evento criado na agenda.");
   setShowForm(false);setEditing(null);setForm({...empty,torcida:String(teams[0]?.id||"")});await load();
  }catch(e){setError(e instanceof Error?e.message:"Não foi possível salvar o evento.");}
  finally{setBusy(false);}
 }
 async function remove(item:EventItem){
  if(!window.confirm("Excluir o evento “"+item.titulo+"”?"))return;
  setBusy(true);setError("");setNotice("");
  try{await api("/api/eventos/"+item.id+"/",{method:"DELETE"});setItems(v=>v.filter(x=>x.id!==item.id));setNotice("Evento excluído.");}
  catch(e){setError(e instanceof Error?e.message:"Não foi possível excluir o evento.");}
  finally{setBusy(false);}
 }
 const visible=items.filter(item=>(filter==="todos"||item.status===filter)&&(!searchQuery.trim()||[item.titulo,item.descricao,item.local,item.torcida_nome].some(value=>value.toLowerCase().includes(searchQuery.trim().toLowerCase())))).sort((a,b)=>new Date(a.inicio_em).getTime()-new Date(b.inicio_em).getTime());
 return <div className="events-wrap">
  <header className="events-head"><div><span className="kicker"><CalendarDays size={14}/> AGENDA DA TORCIDA</span><h2>Jogos, encontros e caravanas</h2><p>Organize os compromissos e acompanhe a programação da torcida.</p></div><button className="primary-btn" onClick={newEvent} disabled={!teams.length}><Plus size={16}/> Criar evento</button></header>
  {error&&<div className="error">{error}</div>}{notice&&<div className="notice">{notice}</div>}
  {showForm&&<form className="content-card events-form" onSubmit={save}>
   <div className="events-form-title"><h3>{editing?"Editar evento":"Novo evento"}</h3><button type="button" className="outline-btn" onClick={()=>{setShowForm(false);setEditing(null);}}>Fechar</button></div>
   <label>Torcida<select className="dark-input" value={form.torcida} onChange={e=>setForm(v=>({...v,torcida:e.target.value}))} required>{teams.map(t=><option key={t.id} value={t.id}>{t.nome}</option>)}</select></label>
   <label>Título<input className="dark-input" value={form.titulo} maxLength={150} onChange={e=>setForm(v=>({...v,titulo:e.target.value}))} required placeholder="Ex.: Caravana para o jogo"/></label>
   <label>Descrição<textarea className="dark-input" value={form.descricao} onChange={e=>setForm(v=>({...v,descricao:e.target.value}))} rows={3}/></label>
   <div className="events-fields"><label>Tipo<select className="dark-input" value={form.tipo} onChange={e=>setForm(v=>({...v,tipo:e.target.value}))}><option value="encontro">Encontro</option><option value="jogo">Jogo</option><option value="viagem">Viagem / Caravana</option><option value="ingresso">Evento com ingresso</option></select></label><label>Status<select className="dark-input" value={form.status} onChange={e=>setForm(v=>({...v,status:e.target.value}))}><option value="rascunho">Rascunho</option><option value="publicado">Publicado</option><option value="cancelado">Cancelado</option><option value="encerrado">Encerrado</option></select></label></div>
   <label>Local<input className="dark-input" value={form.local} onChange={e=>setForm(v=>({...v,local:e.target.value}))} placeholder="Endereço ou ponto de encontro"/></label>
   <div className="events-fields"><label>Início<input className="dark-input" type="datetime-local" value={form.inicio_em} onChange={e=>setForm(v=>({...v,inicio_em:e.target.value}))} required/></label><label>Término<input className="dark-input" type="datetime-local" value={form.fim_em} onChange={e=>setForm(v=>({...v,fim_em:e.target.value}))}/></label></div>
   <div className="events-fields"><label>Capacidade (opcional)<input className="dark-input" type="number" min="1" value={form.capacidade} onChange={e=>setForm(v=>({...v,capacidade:e.target.value}))}/></label><label>Valor (R$)<input className="dark-input" type="number" min="0" step="0.01" value={form.valor} onChange={e=>setForm(v=>({...v,valor:e.target.value}))}/></label></div>
   <button className="primary-btn" disabled={busy}>{busy?"Salvando...":editing?"Salvar alterações":"Publicar evento"}</button>
   <small>O servidor permite criar e editar eventos somente para administradores e moderadores da torcida.</small>
  </form>}
  <div className="events-toolbar"><div className="events-filters">{["todos","publicado","rascunho","cancelado","encerrado"].map(f=><button key={f} className={filter===f?"active":""} onClick={()=>setFilter(f)}>{f==="todos"?"Todos":f[0].toUpperCase()+f.slice(1)}</button>)}</div><button className="outline-btn" onClick={()=>void load()} disabled={loading}><RefreshCw size={15}/> Atualizar</button></div>
  {loading?<div className="content-card">Carregando agenda...</div>:visible.length===0?<div className="content-card events-empty"><CalendarDays/><h3>Nenhum evento nesta categoria</h3><p>Quando houver jogos, encontros ou viagens cadastrados, eles aparecerão aqui.</p></div>:<div className="events-list">{visible.map(item=><article className="content-card event-card" key={item.id}><div className="event-card-top"><span className={"event-status status-"+item.status}>{item.status}</span><small>{item.torcida_nome}</small></div><h3>{item.titulo}</h3>{item.descricao&&<p>{item.descricao}</p>}<div className="event-meta"><span><CalendarDays size={15}/>{date(item.inicio_em)}</span>{item.local&&<span><MapPin size={15}/>{item.local}</span>}<span><Ticket size={15}/>{Number(item.valor)>0?money(item.valor):"Gratuito"}</span>{item.capacidade&&<span><Users size={15}/>{item.capacidade} vagas</span>}</div><div className="event-card-actions"><small>Organização: {item.criado_por_nome}</small><div>{item.status==="publicado"&&<>{ticketStates[item.id]?.pode_entrar?<><span className="ticket-confirmed"><Ticket size={14}/> Ingresso confirmado</span><small className="ticket-code">Código: {ticketStates[item.id]?.ingressos?.find((ticket:any)=>ticket.status==="pago")?.codigo||"Confirmado"}</small></>:<button className="ticket-buy-button" onClick={()=>void buyTicket(item)} disabled={ticketBusy===item.id}><Ticket size={15}/>{ticketBusy===item.id?"Preparando...":Number(item.valor)>0?"Comprar ingresso · Pix":"Emitir ingresso gratuito"}</button>}</>}{teams.length>0&&<button className="outline-btn" onClick={()=>startEdit(item)}><Pencil size={14}/> Editar</button>}<button className="outline-btn" onClick={()=>void remove(item)} disabled={busy}><Trash2 size={14}/> Excluir</button></div></div></article>)}</div>}
 </div>;
}
