import {FormEvent,useCallback,useEffect,useRef,useState} from "react";
import {MessageCircle,Plus,Send,Users,RefreshCw,Wifi,WifiOff} from "lucide-react";

type Tokens={access:string;refresh:string};
type Conversation={id:number;torcida:number;tipo:"privada"|"grupo";nome:string;participantes:string[];ultima_mensagem:{id:number;autor:string;conteudo:string;criada_em:string}|null};
type Message={id:number;autor_id:number;autor_username:string;conteudo:string;criada_em:string};
type Member={id:number;usuario:number;username:string;papel:string};
const API=import.meta.env.VITE_API_URL||"";

export default function Chat({tokens,onTokens}:{tokens:Tokens;onTokens:(v:Tokens)=>void}){
 const [conversations,setConversations]=useState<Conversation[]>([]);
 const [selected,setSelected]=useState<number|null>(null);
 const [messages,setMessages]=useState<Message[]>([]);
 const [members,setMembers]=useState<Member[]>([]);
 const [teams,setTeams]=useState<{id:number;nome:string}[]>([]);
 const [teamId,setTeamId]=useState("");
 const [kind,setKind]=useState<"privada"|"grupo">("privada");
 const [participant,setParticipant]=useState("");
 const [groupName,setGroupName]=useState("");
 const [draft,setDraft]=useState("");
 const [showCreate,setShowCreate]=useState(false);
 const [loading,setLoading]=useState(false);
 const [sending,setSending]=useState(false);
 const [error,setError]=useState("");
 const [connected,setConnected]=useState(false);
 const socket=useRef<WebSocket|null>(null);
 const bottom=useRef<HTMLDivElement|null>(null);
 const auth=useCallback(async()=>{
  const check=await fetch(API+"/api/auth/verify/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:tokens.access})});
  if(check.ok)return tokens.access;
  if(!tokens.refresh)throw Error("Sessão expirada. Entre novamente.");
  const response=await fetch(API+"/api/auth/refresh/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({refresh:tokens.refresh})});
  const data=await response.json();if(!response.ok)throw Error("Sua sessão expirou. Entre novamente.");
  const next={access:data.access,refresh:data.refresh||tokens.refresh};onTokens(next);return next.access;
 },[tokens,onTokens]);
 const request=useCallback(async(path:string,init:RequestInit={})=>{
  const token=await auth();const headers=new Headers(init.headers);headers.set("Authorization","Bearer "+token);
  if(init.body&&!(init.body instanceof FormData))headers.set("Content-Type","application/json");
  const response=await fetch(API+path,{...init,headers});const data=await response.json().catch(()=>({}));
  if(!response.ok)throw Error(data.detail||Object.values(data).flat().join(" ")||"Falha na comunicação.");
  return data;
 },[auth]);
 const loadConversations=useCallback(async()=>{
  const data=await request("/api/chat/conversas/");setConversations(Array.isArray(data)?data:(data.results||[]));
 },[request]);
 useEffect(()=>{let live=true;setLoading(true);Promise.all([request("/api/chat/conversas/"),request("/api/torcidas/")]).then(([c,t])=>{if(!live)return;setConversations(Array.isArray(c)?c:(c.results||[]));setTeams(Array.isArray(t)?t:(t.results||[]))}).catch(e=>{if(live)setError(e.message)}).finally(()=>{if(live)setLoading(false)});return()=>{live=false}},[request]);
 useEffect(()=>{if(!teamId){setMembers([]);return}let live=true;request("/api/torcidas/"+teamId+"/membros/").then(d=>{if(live)setMembers(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[teamId,request]);
 useEffect(()=>{if(!selected)return;let live=true;setMessages([]);setError("");request("/api/chat/conversas/"+selected+"/mensagens/").then(d=>{if(live)setMessages(Array.isArray(d)?d:(d.results||[]))}).catch(e=>{if(live)setError(e.message)});
  let ws:WebSocket|null=null;
  request("/api/chat/ws-ticket/",{method:"POST"}).then(d=>{
   if(!live)return;const base=API||window.location.origin;const url=new URL(base);url.protocol=url.protocol==="https:"?"wss:":"ws:";url.pathname="/ws/chat/"+selected+"/";url.search="ticket="+encodeURIComponent(d.ticket);
   ws=new WebSocket(url.toString());socket.current=ws;
   ws.onopen=()=>setConnected(true);ws.onclose=()=>setConnected(false);ws.onerror=()=>setConnected(false);
   ws.onmessage=event=>{try{const data=JSON.parse(event.data);if(data.tipo==="mensagem")setMessages(old=>old.some(m=>m.id===data.id)?old:[...old,data as Message]);else if(data.tipo==="erro")setError(data.mensagem||"Erro no chat.")}catch{}};
  }).catch(e=>{if(live)setError(e.message)});
  return()=>{live=false;ws?.close();socket.current=null;setConnected(false)};
 },[selected,request]);
 useEffect(()=>{bottom.current?.scrollIntoView({behavior:"smooth"})},[messages]);
 async function createConversation(e:FormEvent){e.preventDefault();setError("");const ids=kind==="privada"?[Number(participant)]:members.filter(m=>String(m.usuario)===participant).map(m=>m.usuario);if(!teamId||!ids.length){setError("Selecione a torcida e pelo menos um participante.");return}try{const data=await request("/api/chat/conversas/",{method:"POST",body:JSON.stringify({torcida:Number(teamId),tipo:kind,nome:kind==="grupo"?groupName:"",participantes:ids})});setShowCreate(false);setParticipant("");setGroupName("");await loadConversations();setSelected(data.id)}catch(e){setError(e instanceof Error?e.message:"Não foi possível criar a conversa.")}}
 async function sendMessage(e:FormEvent){e.preventDefault();const text=draft.trim();if(!text||!selected)return;setSending(true);setError("");try{if(socket.current?.readyState===WebSocket.OPEN){socket.current.send(JSON.stringify({conteudo:text}));setDraft("")}else{const data=await request("/api/chat/conversas/"+selected+"/mensagens/",{method:"POST",body:JSON.stringify({conteudo:text})});setMessages(old=>[...old,data]);setDraft("")}await loadConversations()}catch(e){setError(e instanceof Error?e.message:"Falha ao enviar mensagem.")}finally{setSending(false)}}
 return <div className="chat-layout"><aside className="chat-sidebar"><div className="chat-title"><div><h2>Mensagens</h2><small>Converse com sua torcida</small></div><button className="chat-new" onClick={()=>setShowCreate(v=>!v)} aria-label="Nova conversa"><Plus/></button></div>
 {showCreate&&<form className="chat-create" onSubmit={createConversation}><label>Torcida</label><select value={teamId} onChange={e=>{setTeamId(e.target.value);setParticipant("")}} required><option value="">Selecione</option>{teams.map(t=><option key={t.id} value={t.id}>{t.nome}</option>)}</select><label>Tipo</label><select value={kind} onChange={e=>setKind(e.target.value as "privada"|"grupo")}><option value="privada">Conversa privada</option><option value="grupo">Grupo</option></select>{kind==="grupo"&&<><label>Nome do grupo</label><input value={groupName} onChange={e=>setGroupName(e.target.value)} maxLength={120} required/></>}<label>{kind==="grupo"?"Participante inicial":"Participante"}</label><select value={participant} onChange={e=>setParticipant(e.target.value)} required><option value="">Selecione um membro</option>{members.filter(m=>m.usuario!==Number(sessionStorage.getItem("torcida_user_id"))).map(m=><option key={m.usuario} value={m.usuario}>{m.username}</option>)}</select><button className="primary-btn">Criar conversa</button></form>}
 {loading&&<p className="chat-empty">Carregando conversas...</p>}{!loading&&conversations.length===0&&<p className="chat-empty">Você ainda não tem conversas. Use + para começar.</p>}
 {conversations.map(c=><button key={c.id} className={"conversation-item "+(selected===c.id?"active":"")} onClick={()=>setSelected(c.id)}><span className="conversation-avatar"><MessageCircle/></span><span><b>{c.tipo==="grupo"?(c.nome||"Grupo"):c.participantes.join(", ")}</b><small>{c.ultima_mensagem?.conteudo||"Comece uma conversa"}</small></span></button>)}
 </aside><section className="chat-main">{selected?<><header className="chat-room-head"><div><h3>{conversations.find(c=>c.id===selected)?.nome||conversations.find(c=>c.id===selected)?.participantes.join(", ")||"Conversa"}</h3><small>{connected?<><Wifi/> Conectado em tempo real</>:<><WifiOff/> Conectando ao chat...</>}</small></div><button className="chat-refresh" onClick={()=>{loadConversations();request("/api/chat/conversas/"+selected+"/mensagens/").then(setMessages).catch(e=>setError(e.message))}}><RefreshCw/></button></header><div className="chat-messages">{messages.map(m=><article key={m.id} className={"chat-bubble "+(m.autor_id===Number(sessionStorage.getItem("torcida_user_id"))?"mine":"")}><b>{m.autor_username}</b><p>{m.conteudo}</p><time>{new Date(m.criada_em).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}</time></article>)}<div ref={bottom}/></div><form className="chat-compose" onSubmit={sendMessage}><input value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Digite sua mensagem..." maxLength={4000}/><button disabled={sending||!draft.trim()} aria-label="Enviar mensagem"><Send/></button></form></>:<div className="chat-welcome"><MessageCircle/><h3>Seu espaço de resenha</h3><p>Escolha uma conversa ou crie uma nova para falar com a torcida.</p></div>}</section>{error&&<div className="chat-error">{error}</div>}</div>;
}
