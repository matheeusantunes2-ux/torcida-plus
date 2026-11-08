import {FormEvent,useCallback,useEffect,useRef,useState} from "react";
import {MessageCircle,Plus,Send,Users,RefreshCw,Wifi,WifiOff,Paperclip,Mic,Square,Video} from "lucide-react";

type Tokens={access:string;refresh:string};
type Conversation={id:number;torcida:number;tipo:"privada"|"grupo";nome:string;participantes:string[];ultima_mensagem:{id:number;autor:string;conteudo:string;criada_em:string}|null};
type Attachment={id:number;tipo:"imagem"|"video"|"audio";nome_original:string;content_type:string;tamanho:number;url:string};
type Message={id:number;autor_id:number;autor_username:string;conteudo:string;criada_em:string;anexos?:Attachment[]};
type Member={id:number;usuario:number;username:string;papel:string};
const API=import.meta.env.VITE_API_URL||"";
function currentUserId(token:string){try{const payload=token.split(".")[1].replace(/-/g,"+").replace(/_/g,"/");return Number(JSON.parse(atob(payload)).user_id)||0}catch{return 0}}

export default function Chat({tokens,onTokens,onStartCall}:{tokens:Tokens;onTokens:(v:Tokens)=>void;onStartCall:(conversationId:number)=>void}){
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
 const [showCommunity,setShowCommunity]=useState(false);
 const [teamName,setTeamName]=useState("");
 const [inviteToken,setInviteToken]=useState("");
 const [inviteLink,setInviteLink]=useState("");
 const [selectedMembers,setSelectedMembers]=useState<number[]>([]);
 const [communityBusy,setCommunityBusy]=useState(false);
 const [loading,setLoading]=useState(false);
 const [sending,setSending]=useState(false);
 const [error,setError]=useState("");
 const [connected,setConnected]=useState(false);
 const [typingUser,setTypingUser]=useState(false);
 const [readMessages,setReadMessages]=useState<number[]>([]);
 const [mediaUrls,setMediaUrls]=useState<Record<number,string>>({});
 const [uploading,setUploading]=useState(false);
 const [recording,setRecording]=useState(false);
 const recorder=useRef<MediaRecorder|null>(null);
 const audioStream=useRef<MediaStream|null>(null);
 const fileInput=useRef<HTMLInputElement|null>(null);
 const typingTimer=useRef<ReturnType<typeof setTimeout>|null>(null);
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
 useEffect(()=>{if(!selected)return;let live=true;setMessages([]);setReadMessages([]);setTypingUser(false);setError("");request("/api/chat/conversas/"+selected+"/mensagens/").then(d=>{if(live)setMessages(Array.isArray(d)?d:(d.results||[]))}).catch(e=>{if(live)setError(e.message)});
  let ws:WebSocket|null=null;
  request("/api/chat/ws-ticket/",{method:"POST"}).then(d=>{
   if(!live)return;const base=API||window.location.origin;const url=new URL(base);url.protocol=url.protocol==="https:"?"wss:":"ws:";url.pathname="/ws/chat/"+selected+"/";url.search="ticket="+encodeURIComponent(d.ticket);
   ws=new WebSocket(url.toString());socket.current=ws;
   ws.onopen=()=>setConnected(true);ws.onclose=()=>setConnected(false);ws.onerror=()=>setConnected(false);
   ws.onmessage=event=>{try{const data=JSON.parse(event.data);
    if(data.tipo==="mensagem"){
     setMessages(old=>old.some(m=>m.id===data.id)?old:[...old,data as Message]);
     if(data.autor_id!==currentUserId(tokens.access))ws?.send(JSON.stringify({acao:"lida",mensagem_id:data.id}));
    }else if(data.tipo==="digitando"&&data.usuario_id!==currentUserId(tokens.access)){
     setTypingUser(Boolean(data.digitando));
    }else if(data.tipo==="leitura"){
     setReadMessages(old=>old.includes(data.mensagem_id)?old:[...old,data.mensagem_id]);
    }else if(data.tipo==="erro")setError(data.mensagem||"Erro no chat.");
   }catch{}};
  }).catch(e=>{if(live)setError(e.message)});
  return()=>{live=false;if(typingTimer.current)clearTimeout(typingTimer.current);ws?.close();socket.current=null;setConnected(false);setTypingUser(false)};
 },[selected,request]);
 useEffect(()=>{bottom.current?.scrollIntoView({behavior:"smooth"})},[messages]);
 useEffect(()=>{let live=true;const pending=messages.flatMap(m=>m.anexos||[]).filter(a=>!mediaUrls[a.id]);pending.forEach(a=>request(a.url).then(d=>{if(live&&d.url)setMediaUrls(old=>({...old,[a.id]:d.url}))}).catch(e=>{if(live)setError(e.message)}));return()=>{live=false}},[messages,mediaUrls,request]);
 async function createConversation(e:FormEvent){e.preventDefault();setError("");const ids=kind==="privada"?[Number(participant)]:selectedMembers;if(!teamId||!ids.length){setError("Selecione a torcida e pelo menos um participante.");return}try{const data=await request("/api/chat/conversas/",{method:"POST",body:JSON.stringify({torcida:Number(teamId),tipo:kind,nome:kind==="grupo"?groupName:"",participantes:ids})});setShowCreate(false);setParticipant("");setSelectedMembers([]);setGroupName("");await loadConversations();setSelected(data.id)}catch(e){setError(e instanceof Error?e.message:"Não foi possível criar a conversa.")}}
 async function createTeam(e:FormEvent){e.preventDefault();setCommunityBusy(true);setError("");try{const slug=teamName.trim().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");const data=await request("/api/torcidas/",{method:"POST",body:JSON.stringify({nome:teamName.trim(),slug})});setTeams(v=>[...v,data]);setTeamId(String(data.id));setTeamName("");setShowCommunity(false);setError("Torcida criada! Agora gere um convite para seus participantes.")}catch(e){setError(e instanceof Error?e.message:"Não foi possível criar a torcida.")}finally{setCommunityBusy(false)}}
 async function createInvite(){if(!teamId)return;setCommunityBusy(true);setError("");try{const d=await request("/api/torcidas/"+teamId+"/convites/",{method:"POST",body:JSON.stringify({validade_dias:7,limite_usos:50})});setInviteToken(d.token);setInviteLink(window.location.origin+"/entrar-na-torcida?convite="+encodeURIComponent(d.token));}catch(e){setError(e instanceof Error?e.message:"Não foi possível gerar o convite.")}finally{setCommunityBusy(false)}}
 async function acceptInvite(e:FormEvent){e.preventDefault();setCommunityBusy(true);setError("");try{await request("/api/torcidas/convites/aceitar/",{method:"POST",body:JSON.stringify({token:inviteToken.trim()})});const t=await request("/api/torcidas/");setTeams(Array.isArray(t)?t:(t.results||[]));setInviteToken("");setError("Você entrou na torcida! Atualize a tela para carregar os novos membros.")}catch(e){setError(e instanceof Error?e.message:"Não foi possível aceitar o convite.")}finally{setCommunityBusy(false)}}
 function handleDraftChange(value:string){
  setDraft(value);
  if(socket.current?.readyState===WebSocket.OPEN){
   socket.current.send(JSON.stringify({acao:"digitando",digitando:true}));
   if(typingTimer.current)clearTimeout(typingTimer.current);
   typingTimer.current=setTimeout(()=>socket.current?.readyState===WebSocket.OPEN&&socket.current.send(JSON.stringify({acao:"digitando",digitando:false})),1200);
  }
 }
 async function sendMessage(e:FormEvent){e.preventDefault();const text=draft.trim();if(!text||!selected)return;setSending(true);setError("");try{if(socket.current?.readyState===WebSocket.OPEN){socket.current.send(JSON.stringify({conteudo:text}));socket.current.send(JSON.stringify({acao:"digitando",digitando:false}));setDraft("")}else{const data=await request("/api/chat/conversas/"+selected+"/mensagens/",{method:"POST",body:JSON.stringify({conteudo:text})});setMessages(old=>[...old,data]);setDraft("")}await loadConversations()}catch(e){setError(e instanceof Error?e.message:"Falha ao enviar mensagem.")}finally{setSending(false)}}
 async function toggleAudioRecording(){
  if(recording){recorder.current?.stop();return}
  if(!selected||uploading||sending)return;
  try{
   if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==="undefined")throw Error("Seu navegador não oferece gravação de áudio. Atualize o navegador.");
   const stream=await navigator.mediaDevices.getUserMedia({audio:true});
   audioStream.current=stream;
   const mime=["audio/webm;codecs=opus","audio/webm","audio/ogg;codecs=opus","audio/mp4"].find(t=>MediaRecorder.isTypeSupported(t));
   const mediaRecorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined);
   const chunks:BlobPart[]=[];
   recorder.current=mediaRecorder;
   mediaRecorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
   mediaRecorder.onerror=()=>{setError("Falha durante a gravação do áudio.");setRecording(false);stream.getTracks().forEach(t=>t.stop())};
   mediaRecorder.onstop=()=>{
    const type=mediaRecorder.mimeType||"audio/webm";
    const ext=type.includes("ogg")?"ogg":type.includes("mp4")?"m4a":"webm";
    const audio=new File(chunks,"mensagem-de-voz."+ext,{type});
    stream.getTracks().forEach(t=>t.stop());audioStream.current=null;recorder.current=null;setRecording(false);
    if(audio.size)void uploadAttachment(audio);
   };
   mediaRecorder.start();setRecording(true);setError("");
   window.setTimeout(()=>{if(mediaRecorder.state==="recording")mediaRecorder.stop()},120000);
  }catch(e){audioStream.current?.getTracks().forEach(t=>t.stop());audioStream.current=null;setRecording(false);setError(e instanceof Error?e.message:"Não foi possível iniciar a gravação.")}
 }
 async function uploadAttachment(file?:File){if(!file||!selected)return;setUploading(true);setError("");try{const form=new FormData();form.append("arquivo",file);if(draft.trim())form.append("conteudo",draft.trim());const data=await request("/api/chat/conversas/"+selected+"/anexos/",{method:"POST",body:form});setMessages(old=>old.some(m=>m.id===data.id)?old.map(m=>m.id===data.id?data:m):[...old,data]);setDraft("");await loadConversations()}catch(e){setError(e instanceof Error?e.message:"Não foi possível enviar a mídia.")}finally{setUploading(false);if(fileInput.current)fileInput.current.value=""}}
 useEffect(()=>()=>{if(recorder.current?.state==="recording")recorder.current.stop();audioStream.current?.getTracks().forEach(t=>t.stop())},[]);
 return <div className="chat-area"><div className="community-toolbar"><button className="outline-btn" onClick={()=>setShowCommunity(v=>!v)}><Users/> Torcidas e convites</button><button className="outline-btn" onClick={()=>setShowCreate(v=>!v)}><Plus/> Nova conversa</button></div>{showCommunity&&<section className="community-panel"><div className="community-columns"><form onSubmit={createTeam}><h3>Criar torcida</h3><label>Nome da torcida</label><input value={teamName} onChange={e=>setTeamName(e.target.value)} placeholder="Ex.: Torcida do Bairro" maxLength={120} required/><button className="primary-btn" disabled={communityBusy}>Criar torcida</button></form><form onSubmit={acceptInvite}><h3>Entrar com convite</h3><label>Código do convite</label><input value={inviteToken} onChange={e=>setInviteToken(e.target.value)} placeholder="Cole o código recebido" required/><button className="primary-btn" disabled={communityBusy}>Aceitar convite</button></form></div>{teams.length>0&&<div className="community-team-actions"><label>Minha torcida</label><select value={teamId} onChange={e=>setTeamId(e.target.value)}><option value="">Selecione</option>{teams.map(t=><option key={t.id} value={t.id}>{t.nome}</option>)}</select><button className="outline-btn" onClick={createInvite} disabled={!teamId||communityBusy}>Gerar convite para membros</button>{inviteLink&&<div className="invite-result"><p>Compartilhe este código com os participantes:</p><textarea readOnly value={inviteToken}/><button className="outline-btn" onClick={()=>navigator.clipboard?.writeText(inviteToken)}>Copiar código</button></div>}</div>}</section>}<div className="chat-layout"><aside className="chat-sidebar"><div className="chat-title"><div><h2>Mensagens</h2><small>Converse com sua torcida</small></div><button className="chat-new" onClick={()=>setShowCreate(v=>!v)} aria-label="Nova conversa"><Plus/></button></div>
 {showCreate&&<form className="chat-create" onSubmit={createConversation}><label>Torcida</label><select value={teamId} onChange={e=>{setTeamId(e.target.value);setParticipant("")}} required><option value="">Selecione</option>{teams.map(t=><option key={t.id} value={t.id}>{t.nome}</option>)}</select><label>Tipo</label><select value={kind} onChange={e=>setKind(e.target.value as "privada"|"grupo")}><option value="privada">Conversa privada</option><option value="grupo">Grupo</option></select>{kind==="grupo"&&<><label>Nome do grupo</label><input value={groupName} onChange={e=>setGroupName(e.target.value)} maxLength={120} required/></>}<label>{kind==="grupo"?"Participantes":"Participante"}</label>{kind==="privada"?<select value={participant} onChange={e=>setParticipant(e.target.value)} required><option value="">Selecione um membro</option>{members.filter(m=>m.usuario!==currentUserId(tokens.access)).map(m=><option key={m.usuario} value={m.usuario}>{m.username}</option>)}</select>:<div className="member-picker">{members.filter(m=>m.usuario!==currentUserId(tokens.access)).map(m=><label key={m.usuario}><input type="checkbox" checked={selectedMembers.includes(m.usuario)} onChange={e=>setSelectedMembers(v=>e.target.checked?[...v,m.usuario]:v.filter(id=>id!==m.usuario))}/>{m.username}</label>)}</div>}<button className="primary-btn">Criar conversa</button></form>}
 {loading&&<p className="chat-empty">Carregando conversas...</p>}{!loading&&conversations.length===0&&<p className="chat-empty">Você ainda não tem conversas. Use + para começar.</p>}
 {conversations.map(c=><button key={c.id} className={"conversation-item "+(selected===c.id?"active":"")} onClick={()=>setSelected(c.id)}><span className="conversation-avatar"><MessageCircle/></span><span><b>{c.tipo==="grupo"?(c.nome||"Grupo"):c.participantes.join(", ")}</b><small>{c.ultima_mensagem?.conteudo||"Comece uma conversa"}</small></span></button>)}
 </aside><section className="chat-main">{selected?<><header className="chat-room-head"><div><h3>{conversations.find(c=>c.id===selected)?.nome||conversations.find(c=>c.id===selected)?.participantes.join(", ")||"Conversa"}</h3><small>{typingUser?"Alguém está digitando…":connected?<><Wifi/> Conectado em tempo real</>:<><WifiOff/> Conectando ao chat...</>}</small></div><div className="chat-head-actions"><button className="chat-call" onClick={()=>onStartCall(selected)} aria-label="Iniciar chamada de voz ou vídeo"><Video/> <span>Chamada</span></button><button className="chat-refresh" onClick={()=>{loadConversations();request("/api/chat/conversas/"+selected+"/mensagens/").then(setMessages).catch(e=>setError(e.message))}} aria-label="Atualizar conversa"><RefreshCw/></button></div></header><div className="chat-messages">{messages.map(m=><article key={m.id} className={"chat-bubble "+(m.autor_id===currentUserId(tokens.access)?"mine":"")}><b>{m.autor_username}</b><p>{m.conteudo}</p>{m.anexos?.map(a=><div className="chat-attachment" key={a.id}>{mediaUrls[a.id]?(a.tipo==="imagem"?<img src={mediaUrls[a.id]} alt={a.nome_original} loading="lazy"/>:a.tipo==="audio"?<audio src={mediaUrls[a.id]} controls preload="metadata"/>:<video src={mediaUrls[a.id]} controls playsInline preload="metadata"/>):<small>Carregando mídia protegida…</small>}</div>)}<time>{new Date(m.criada_em).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}{m.autor_id===currentUserId(tokens.access)&&<span className="chat-read-status"> {readMessages.includes(m.id)?" • Lida":" • Enviada"}</span>}</time></article>)}<div ref={bottom}/></div><form className="chat-compose" onSubmit={sendMessage}><input ref={fileInput} type="file" hidden accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime" onChange={e=>uploadAttachment(e.target.files?.[0])}/><button type="button" className="chat-attach" onClick={()=>fileInput.current?.click()} disabled={uploading||sending||recording} aria-label="Anexar imagem ou vídeo"><Paperclip/></button><button type="button" className={"chat-attach "+(recording?"recording":"")} onClick={toggleAudioRecording} disabled={uploading||sending} aria-label={recording?"Parar gravação":"Gravar áudio"}>{recording?<Square/>:<Mic/>}</button><input value={draft} onChange={e=>handleDraftChange(e.target.value)} placeholder="Digite sua mensagem..." maxLength={4000}/><button disabled={sending||uploading||!draft.trim()} aria-label="Enviar mensagem"><Send/></button>{recording&&<small>Gravando áudio… toque no quadrado para enviar (máx. 2 min).</small>}{uploading&&<small>Enviando mídia…</small>}</form></>:<div className="chat-welcome"><MessageCircle/><h3>Seu espaço de resenha</h3><p>Escolha uma conversa ou crie uma nova para falar com a torcida.</p></div>}</section>{error&&<div className="chat-error">{error}</div>}</div></div>;
}
