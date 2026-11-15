import {useCallback,useEffect,useState} from "react";
import {BadgeCheck,Copy,RefreshCw,Users,WalletCards,ShieldCheck,Clock3,CheckCircle2,AlertCircle} from "lucide-react";
import "./Membership.css";

type Torcida={id:number;nome:string;slug?:string};
type Plan={id:number;nome:string;descricao:string;valor:string;duracao_dias:number};
type Association={id:number;torcida:string;torcida_id:number;plano:string;valor:string;status:string;inicio_em?:string|null;fim_em?:string|null};
type Pending={id:number;username:string;plano:string;valor:string;status:string;criado_em:string};

export default function Membership({tokens,api}:{tokens:{access:string;refresh:string};api:string}){
 const [torcidas,setTorcidas]=useState<Torcida[]>([]),[selected,setSelected]=useState(""),[plans,setPlans]=useState<Plan[]>([]),[mine,setMine]=useState<Association[]>([]),[pending,setPending]=useState<Pending[]>([]);
 const [qr,setQr]=useState<{qr_token:string;validade_segundos:number;associacao_id:number;torcida:string}|null>(null);
 const [busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(""),[notice,setNotice]=useState("");
 const auth={Authorization:"Bearer "+tokens.access};
 const parse=async(r:Response)=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||Object.values(d).flat().join(" ")||"Não foi possível concluir.");return d};
 const load=useCallback(async()=>{
  setLoading(true);setError("");
  try{
   const [t,m]=await Promise.all([fetch(api+"/api/torcidas/",{headers:auth}),fetch(api+"/api/torcidas/associacoes/minhas/",{headers:auth})]);
   const td=await parse(t),md=await parse(m);setTorcidas(Array.isArray(td)?td:(td.results||[]));setMine(Array.isArray(md)?md:(md.results||[]));
  }catch(e){setError(e instanceof Error?e.message:"Falha ao carregar associações.");}finally{setLoading(false);}
 },[api,tokens.access]);
 useEffect(()=>{void load()},[load]);
 const loadPlans=async(id:string)=>{setSelected(id);setPlans([]);setQr(null);if(!id)return;try{const d=await parse(await fetch(api+"/api/torcidas/"+id+"/associacoes/planos/"));setPlans(d)}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar planos.");}};
 const apply=async(plan:Plan)=>{if(!selected)return;setBusy(true);setError("");setNotice("");try{const d=await parse(await fetch(api+"/api/torcidas/"+selected+"/associacoes/solicitar/",{method:"POST",headers:{...auth,"Content-Type":"application/json"},body:JSON.stringify({plano_id:plan.id})}));setNotice(d.mensagem||"Solicitação enviada.");await load();}catch(e){setError(e instanceof Error?e.message:"Falha ao solicitar associação.");}finally{setBusy(false);}};
 const getQr=async(a:Association)=>{setBusy(true);setError("");try{const d=await parse(await fetch(api+"/api/torcidas/associacoes/"+a.id+"/carteirinha-qr/",{headers:auth}));setQr(d);window.setTimeout(()=>setQr(current=>current?.associacao_id===a.id?null:current),d.validade_segundos*1000);}catch(e){setError(e instanceof Error?e.message:"Não foi possível emitir a carteirinha.");}finally{setBusy(false);}};
 const loadPending=async(id:string)=>{try{const d=await parse(await fetch(api+"/api/torcidas/"+id+"/associacoes/",{headers:auth}));setPending(d.filter((a:Pending)=>a.status==="pendente"));}catch{setPending([]);}};
 const decide=async(id:number,approve:boolean,paid=false)=>{if(!selected)return;setBusy(true);try{await parse(await fetch(api+"/api/torcidas/"+selected+"/associacoes/"+id+"/",{method:"PATCH",headers:{...auth,"Content-Type":"application/json"},body:JSON.stringify({status:approve?"ativa":"cancelada",...(paid?{confirmacao_pagamento:true}:{})})}));setNotice(approve?"Associação ativada.":"Solicitação cancelada.");await load();await loadPending(selected);}catch(e){setError(e instanceof Error?e.message:"Não foi possível atualizar a associação.");}finally{setBusy(false);}};
 const copy=async()=>{if(!qr)return;try{await navigator.clipboard.writeText(qr.qr_token);setNotice("Código temporário copiado.");}catch{setError("Não foi possível copiar o código neste navegador.");}};
 return <main className="membership-page">
  <header className="membership-hero"><div className="membership-hero-icon"><WalletCards/></div><div><span>TORCIDA+ · ÁREA DO ASSOCIADO</span><h2>Associados e carteirinha</h2><p>Consulte planos, solicite adesão e apresente sua credencial digital.</p></div><button onClick={()=>void load()} aria-label="Atualizar"><RefreshCw/></button></header>
  {error&&<div className="membership-alert error"><AlertCircle/>{error}</div>}{notice&&<div className="membership-alert success"><CheckCircle2/>{notice}</div>}
  <section className="membership-section"><div className="membership-section-title"><div><span>01 · ADESÃO</span><h3>Encontrar planos</h3></div><Users/></div>
   <label className="membership-label">Selecione sua torcida</label><select className="membership-select" value={selected} onChange={e=>{void loadPlans(e.target.value);void loadPending(e.target.value)}}><option value="">Escolha uma torcida</option>{torcidas.map(t=><option key={t.id} value={t.id}>{t.nome}</option>)}</select>
   {selected&&<div className="membership-plans">{plans.length?plans.map(p=><article className="membership-plan" key={p.id}><div><span className="membership-plan-tag">{p.valor==="0.00"||Number(p.valor)===0?"PLANO GRATUITO":"PLANO DE ASSOCIAÇÃO"}</span><h4>{p.nome}</h4><p>{p.descricao||"Faça parte oficialmente da torcida."}</p><small>Validade: {p.duracao_dias} dias</small></div><div className="membership-plan-action"><b>{Number(p.valor)===0?"Gratuito":Number(p.valor).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}</b><button disabled={busy} onClick={()=>void apply(p)}>{busy?"Enviando...":"Solicitar adesão"}</button></div></article>):<p className="membership-empty">Nenhum plano ativo disponível nesta torcida.</p>}</div>}
  </section>
  <section className="membership-section"><div className="membership-section-title"><div><span>02 · MINHA CONTA</span><h3>Minhas associações</h3></div><BadgeCheck/></div>
   {loading?<p className="membership-empty">Carregando...</p>:mine.length===0?<p className="membership-empty">Você ainda não possui solicitações de associação.</p>:<div className="membership-associations">{mine.map(a=><article className="membership-association" key={a.id}><div className="membership-association-mark"><ShieldCheck/></div><div className="membership-association-info"><b>{a.torcida}</b><span>{a.plano} · {Number(a.valor)===0?"Gratuito":Number(a.valor).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}</span><small className={"membership-status "+a.status}>{a.status==="ativa"?"Associado ativo":a.status==="pendente"?"Aguardando aprovação":a.status==="expirada"?"Associação expirada":"Cancelada"}</small>{a.fim_em&&<small>Válida até {new Date(a.fim_em).toLocaleDateString("pt-BR")}</small>}</div>{a.status==="ativa"&&<button className="membership-credential-button" disabled={busy} onClick={()=>void getQr(a)}><WalletCards/> Carteirinha</button>}</article>)}</div>}
   {qr&&<article className="membership-credential"><div className="credential-head"><div><span>CREDENCIAL TEMPORÁRIA</span><h4>{qr.torcida}</h4></div><Clock3/><b>{qr.validade_segundos}s</b></div><p>Este código é assinado e expira automaticamente. Apresente-o ao responsável pela validação.</p><code>{qr.qr_token}</code><button onClick={()=>void copy()}><Copy/> Copiar código de validação</button></article>}
  </section>
  {selected&&<section className="membership-section"><div className="membership-section-title"><div><span>03 · DIRETORIA</span><h3>Solicitações pendentes</h3></div><ShieldCheck/></div><p className="membership-manager-hint">Área disponível somente para administradores da torcida.</p><button className="membership-secondary" onClick={()=>void loadPending(selected)}>Atualizar solicitações</button>{pending.length>0&&pending.map(p=><article className="membership-pending" key={p.id}><div><b>@{p.username}</b><span>{p.plano} · {Number(p.valor).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}</span></div><button disabled={busy} onClick={()=>void decide(p.id,true,Number(p.valor)>0)}>Aprovar</button><button className="reject" disabled={busy} onClick={()=>void decide(p.id,false)}>Recusar</button></article>)}</section>}
 </main>;
}
