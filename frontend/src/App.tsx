import {FormEvent,useEffect,useState} from "react";
import {LiveKitRoom,RoomAudioRenderer,VideoConference,useLocalParticipant} from "@livekit/components-react";
import Chat from "./components/Chat";
import Store from "./components/Store";
import "@livekit/components-styles";
import {Home,MessageCircle,CalendarDays,ShoppingCart,Menu,Search,Bell,UserCircle,ShieldCheck,Video,Phone,PhoneOff,Mic,MicOff,ArrowLeft,LoaderCircle,LogOut,Heart,MessageSquare,Share2,Users,Ticket,Settings,ChevronRight,Flame,FileUp,MonitorUp,MonitorOff} from "lucide-react";
const API=import.meta.env.VITE_API_URL||"";
type Comment={id:number;autor_username:string;autor_nome_exibicao?:string;texto:string;criado_em:string}; type Post={id:number;torcida:number;autor_username:string;autor_nome_exibicao?:string;texto:string;criada_em:string;autor_foto?:string|null;imagem?:string|null;total_curtidas:number;total_comentarios:number;curtida_pelo_usuario:boolean}; type Notice={id:number;tipo:string;texto:string;referencia:string;ator_username:string|null;criada_em:string;lida_em:string|null}; type Tokens={access:string;refresh:string}; type Room={server_url:string;room:string;token:string;mode:"voice"|"video"|"meeting"}; type Tab="Início"|"Chat"|"Eventos"|"Loja"|"Notificações"|"Mais";
function MeetingPresentationControls(){
 const {localParticipant,isScreenShareEnabled}=useLocalParticipant();
 const [busy,setBusy]=useState(false);
 const [notice,setNotice]=useState("Compartilhe sua tela para mostrar slides, vídeos ou documentos aos participantes.");
 const inputId="torcida-meeting-presentation-file";
 async function toggleShare(){
  setBusy(true);
  try{await localParticipant.setScreenShareEnabled(!isScreenShareEnabled);setNotice(isScreenShareEnabled?"Compartilhamento de tela encerrado.":"Tela compartilhada. Abra o slide, vídeo ou documento que deseja apresentar.");}
  catch(e){setNotice(e instanceof Error?e.message:"Não foi possível compartilhar a tela neste dispositivo.");}
  finally{setBusy(false);}
 }
 function openPresentation(file?:File){
  if(!file)return;
  const url=URL.createObjectURL(file);
  const opened=window.open(url,"_blank");
  if(!opened){URL.revokeObjectURL(url);setNotice("O navegador bloqueou a nova aba. Permita pop-ups ou abra o arquivo pelo gerenciador de arquivos.");return;}
  opened.opener=null;
  window.setTimeout(()=>URL.revokeObjectURL(url),10*60*1000);
  setNotice("Arquivo aberto. Agora toque em Compartilhar tela e selecione a janela/aba do documento. Para PPT/PPTX, use um visualizador compatível.");
 }
 return <section className="meeting-presentation-toolbar">
  <div><b>Apresentação da reunião</b><small>{notice}</small></div>
  <div className="meeting-presentation-actions">
   <input id={inputId} type="file" accept=".pdf,.ppt,.pptx,.odp,.doc,.docx,.xls,.xlsx,.mp4,.webm,.mov,.jpg,.jpeg,.png" onChange={e=>{openPresentation(e.target.files?.[0]);e.currentTarget.value="";}}/>
   <label htmlFor={inputId} className="meeting-file-button"><FileUp/> Abrir arquivo</label>
   <button type="button" className={isScreenShareEnabled?"meeting-stop-share":"meeting-share"} onClick={()=>void toggleShare()} disabled={busy}>{isScreenShareEnabled?<MonitorOff/>:<MonitorUp/>}{busy?" Aguarde...":isScreenShareEnabled?" Parar apresentação":" Compartilhar tela"}</button>
  </div>
  <p>O chat da reunião fica no painel do LiveKit. O compartilhamento depende do suporte do navegador/dispositivo; no Android pode ser necessário abrir o arquivo em outro app e iniciar a captura de tela.</p>
 </section>;
}

function VoiceCallControls({onHangup}:{onHangup:()=>void}){
 const {localParticipant,isMicrophoneEnabled}=useLocalParticipant();
 const [micBusy,setMicBusy]=useState(false);
 const [micError,setMicError]=useState("");
 async function toggleMicrophone(){
  setMicBusy(true);setMicError("");
  try{await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);}
  catch(e){setMicError(e instanceof Error?e.message:"Não foi possível acessar o microfone.");}
  finally{setMicBusy(false);}
 }
 return <section className="voice-call-panel">
  <RoomAudioRenderer/>
  <div className="voice-call-avatar"><Phone/></div>
  <span className="voice-call-kicker">TORCIDA+ · AO VIVO</span>
  <h1>Chamada de voz</h1>
  <p>Conversa por áudio em tempo real. Mantenha o aplicativo aberto durante a chamada.</p>
  <div className="voice-call-actions">
   <button type="button" className={isMicrophoneEnabled?"voice-mic-on":"voice-mic-off"} onClick={()=>void toggleMicrophone()} disabled={micBusy}>
    {isMicrophoneEnabled?<Mic/>:<MicOff/>}<span>{micBusy?"Aguarde...":isMicrophoneEnabled?"Microfone ligado":"Microfone desligado"}</span>
   </button>
   <button type="button" className="voice-hangup" onClick={onHangup}><PhoneOff/><span>Encerrar chamada</span></button>
  </div>
  {micError&&<p className="voice-call-error">{micError}</p>}
  <small className="voice-call-security">A criptografia ponta a ponta ainda não está habilitada nesta chamada.</small>
 </section>;
}

export default function App(){
const [tokens,setTokens]=useState<Tokens>(()=>({access:sessionStorage.getItem("torcida_access")||"",refresh:sessionStorage.getItem("torcida_refresh")||""}));
const [posts,setPosts]=useState<Post[]>([]),[newPost,setNewPost]=useState(""),[postImage,setPostImage]=useState<File|null>(null),[torcidaId,setTorcidaId]=useState(""),[publishing,setPublishing]=useState(false),[feedLoading,setFeedLoading]=useState(false),[feedError,setFeedError]=useState(""),[feedNotice,setFeedNotice]=useState(""),[comments,setComments]=useState<Record<number,Comment[]>>({}),[openComments,setOpenComments]=useState<number|null>(null),[commentDrafts,setCommentDrafts]=useState<Record<number,string>>({}),[commentBusy,setCommentBusy]=useState<number|null>(null),[notices,setNotices]=useState<Notice[]>([]),[unread,setUnread]=useState(0),[noticeLoading,setNoticeLoading]=useState(false),[noticeError,setNoticeError]=useState("");
const [mode,setMode]=useState<"login"|"register">("login"),[username,setUsername]=useState(""),[email,setEmail]=useState(""),[password,setPassword]=useState(""),[tab,setTab]=useState<Tab>(()=>new URLSearchParams(window.location.search).has("store_payment")?"Loja":"Início"),[room,setRoom]=useState<Room|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(""),[message,setMessage]=useState("");
const [moreSection,setMoreSection]=useState<"menu"|"perfil"|"pelotoes"|"configuracoes"|"admin"|"moderacao">("menu");
const [menuOpen,setMenuOpen]=useState(false);
function save(v:Tokens){setTokens(v);v.access?sessionStorage.setItem("torcida_access",v.access):sessionStorage.removeItem("torcida_access");v.refresh?sessionStorage.setItem("torcida_refresh",v.refresh):sessionStorage.removeItem("torcida_refresh")}
async function result(r:Response){const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||Object.values(d).flat().join(" ")||"Não foi possível concluir.");return d}
async function authenticate(e:FormEvent){e.preventDefault();setBusy(false);setError("");setMessage("");if(username.trim().length<3){setError("O usuário precisa ter pelo menos 3 caracteres.");return}if(password.length<8){setError("A senha precisa ter pelo menos 8 caracteres.");return}if(!API){setError("Servidor não configurado neste APK. O endereço da API (VITE_API_URL) precisa ser configurado e o aplicativo recompilado.");return}setBusy(true);try{if(mode==="register"){await result(await fetch(API+"/api/auth/cadastro/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:username.trim(),email:email.trim(),password})}));setMode("login");setMessage("Cadastro realizado. Entre com seus dados.")}else{const d=await result(await fetch(API+"/api/auth/login/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:username.trim(),password})}));save({access:d.access,refresh:d.refresh});setPassword("");setTab("Início")}}catch(x){setError(x instanceof Error?x.message:"Falha ao autenticar.")}finally{setBusy(false)}}
async function access(){const r=await fetch(API+"/api/auth/verify/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:tokens.access})});if(r.ok)return tokens.access;if(!tokens.refresh)throw Error("Sessão expirada. Entre novamente.");const d=await result(await fetch(API+"/api/auth/refresh/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({refresh:tokens.refresh})}));save({access:d.access,refresh:d.refresh||tokens.refresh});return d.access as string}
async function sharePost(post:Post){
 const url=window.location.origin+window.location.pathname+"#publicacao-"+post.id;
 const title="Publicação no TORCIDA+";
 const text=(post.texto||"Confira esta publicação da torcida.").slice(0,240);
 try{
  if(typeof navigator.share==="function")await navigator.share({title,text,url});
  else if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(url);
  else {const field=document.createElement("textarea");field.value=url;field.setAttribute("readonly","");field.style.position="absolute";field.style.left="-9999px";document.body.appendChild(field);field.select();const copied=document.execCommand("copy");document.body.removeChild(field);if(!copied)throw new Error("Seu aparelho não permite compartilhar automaticamente.");}
  setFeedNotice(typeof navigator.share==="function"?"Compartilhamento aberto.":"Link da publicação copiado para compartilhar.");
 }catch(e){if(e instanceof Error&&e.name==="AbortError")return;setFeedError(e instanceof Error?e.message:"Não foi possível compartilhar esta publicação.");}
}
async function publish(e:FormEvent){e.preventDefault();if(!torcidaId.trim()||!/^\d+$/.test(torcidaId)){setFeedError("Informe o ID de uma torcida da qual você participa.");return}if(!newPost.trim()&&!postImage){setFeedError("Escreva algo ou escolha uma imagem.");return}setPublishing(true);setFeedError("");setFeedNotice("");try{const t=await access();const body=new FormData();body.append("torcida",torcidaId);body.append("texto",newPost.trim());if(postImage)body.append("imagem",postImage);const r=await fetch(API+"/api/comunidade/publicacoes/",{method:"POST",headers:{Authorization:"Bearer "+t},body});await result(r);setNewPost("");setFeedNotice("Publicação enviada! Ela ficará visível para todos após a aprovação do administrador.");setPostImage(null);const input=document.getElementById("post-image") as HTMLInputElement|null;if(input)input.value=""}catch(e){setFeedError(e instanceof Error?e.message:"Não foi possível publicar.")}finally{setPublishing(false)}}
async function toggleLike(id:number){try{const t=await access();const current=await result(await fetch(API+"/api/comunidade/publicacoes/"+id+"/curtida/",{headers:{Authorization:"Bearer "+t}}));const liked=Boolean(current.curtida_pelo_usuario);const updated=await result(await fetch(API+"/api/comunidade/publicacoes/"+id+"/curtida/",{method:liked?"DELETE":"POST",headers:{Authorization:"Bearer "+t}}));setPosts(items=>items.map(p=>p.id===id?{...p,curtida_pelo_usuario:!liked,total_curtidas:updated.total_curtidas}:p))}catch(e){setFeedError(e instanceof Error?e.message:"Falha ao curtir.")}}
async function loadComments(id:number){try{const t=await access();const data=await result(await fetch(API+"/api/comunidade/publicacoes/"+id+"/comentarios/",{headers:{Authorization:"Bearer "+t}}));setComments(v=>({...v,[id]:Array.isArray(data)?data:(data.results||[])}));setOpenComments(id)}catch(e){setFeedError(e instanceof Error?e.message:"Falha ao carregar comentários.")}}
async function sendComment(id:number){const texto=(commentDrafts[id]||"").trim();if(!texto)return;setCommentBusy(id);try{const t=await access();const c=await result(await fetch(API+"/api/comunidade/publicacoes/"+id+"/comentarios/",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+t},body:JSON.stringify({texto})}));setComments(v=>({...v,[id]:[...(v[id]||[]),c]}));setCommentDrafts(v=>({...v,[id]:""}));setPosts(v=>v.map(p=>p.id===id?{...p,total_comentarios:p.total_comentarios+1}:p))}catch(e){setFeedError(e instanceof Error?e.message:"Falha ao comentar.")}finally{setCommentBusy(null)}}
async function call(conversationId:number,mode:"voice"|"video"|"meeting"){setBusy(true);setError("");try{const t=await access();const d=await result(await fetch(API+"/api/chat/conversas/"+conversationId+"/chamada/token/",{method:"POST",headers:{Authorization:"Bearer "+t}}));setRoom({...d,mode} as Room)}catch(x){setError(x instanceof Error?x.message:"Falha ao iniciar chamada.")}finally{setBusy(false)}}
useEffect(()=>{if(!tokens.access||tab!=="Notificações")return;let active=true;setNoticeLoading(true);setNoticeError("");access().then(t=>fetch(API+"/api/comunidade/notificacoes/",{headers:{Authorization:"Bearer "+t}})).then(async r=>{const d=await result(r);return d}).then(d=>{if(active){setNotices(d.results||[]);setUnread(d.nao_lidas||0)}}).catch(e=>{if(active)setNoticeError(e instanceof Error?e.message:"Falha ao carregar notificações.")}).finally(()=>{if(active)setNoticeLoading(false)});return()=>{active=false}},[tokens.access,tab]);
useEffect(()=>{if(!tokens.access)return;let active=true;const refreshUnread=async()=>{try{const t=await access();const r=await fetch(API+"/api/comunidade/notificacoes/",{headers:{Authorization:"Bearer "+t}});const d=await result(r);if(active){setUnread(d.nao_lidas||0);if(tab==="Notificações")setNotices(d.results||[])}}catch{/* Mantém o último contador válido durante falhas temporárias. */}};refreshUnread();const timer=window.setInterval(refreshUnread,45000);return()=>{active=false;window.clearInterval(timer)}},[tokens.access,tab]);
async function markNoticeRead(id:number){try{const t=await access();await result(await fetch(API+"/api/comunidade/notificacoes/"+id+"/ler/",{method:"POST",headers:{Authorization:"Bearer "+t}}));setNotices(v=>v.map(n=>n.id===id?{...n,lida_em:new Date().toISOString()}:n));setUnread(v=>Math.max(0,v-1))}catch(e){setNoticeError(e instanceof Error?e.message:"Falha ao marcar notificação.")}}
async function openNotice(n:Notice){await markNoticeRead(n.id);if(n.referencia?.startsWith("moderacao:publicacao:"))setTab("Mais");}
async function markAllNoticesRead(){try{const t=await access();await result(await fetch(API+"/api/comunidade/notificacoes/ler-todas/",{method:"POST",headers:{Authorization:"Bearer "+t}}));setNotices(v=>v.map(n=>({...n,lida_em:n.lida_em||new Date().toISOString()})));setUnread(0)}catch(e){setNoticeError(e instanceof Error?e.message:"Falha ao marcar notificações.")}}
useEffect(()=>{if(!tokens.access||tab!=="Início")return;let active=true;setFeedLoading(true);setFeedError("");fetch(API+"/api/comunidade/publicacoes/",{headers:{Authorization:"Bearer "+tokens.access}}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||"Não foi possível carregar o feed.");return Array.isArray(d)?d:(d.results||[])}).then(data=>{if(active)setPosts(data)}).catch(e=>{if(active)setFeedError(e instanceof Error?e.message:"Falha ao carregar publicações.")}).finally(()=>{if(active)setFeedLoading(false)});return()=>{active=false}},[tokens.access,tab]);
function logout(){save({access:"",refresh:""});setRoom(null);setTab("Início")}
if(room)return <main className="call-screen"><header className="call-top"><button className="icon-btn" onClick={()=>setRoom(null)} aria-label="Voltar e encerrar chamada"><ArrowLeft/></button><b>{room.mode==="meeting"?"REUNIÃO TORCIDA+":"TORCIDA+ AO VIVO"} · {room.room}</b></header>{room.mode==="voice"?<section className="voice-call-stage"><LiveKitRoom serverUrl={room.server_url} token={room.token} connect audio video={false} onDisconnected={()=>setRoom(null)}><VoiceCallControls onHangup={()=>setRoom(null)}/></LiveKitRoom></section>:<><section className="conference"><LiveKitRoom serverUrl={room.server_url} token={room.token} connect audio video onDisconnected={()=>setRoom(null)}>{room.mode==="meeting"&&<MeetingPresentationControls/>}<VideoConference/></LiveKitRoom></section><p className="call-note">{room.mode==="meeting"?"Reunião com vídeo, chat integrado e compartilhamento de tela.":"Criptografia ponta a ponta ainda não habilitada nesta chamada."}</p></>}</main>;
if(!tokens.access)return <main className="auth-page"><section className="auth-panel"><div className="crest"><b>★</b><div className="crest-shield"><Users/><strong>TORCIDA<span>+</span></strong></div></div><h1>Conectando a nação<br/>em um só <em>lugar!</em></h1><div className="auth-box"><h2>{mode==="login"?"Entre para a torcida":"Crie sua conta"}</h2><p>A arquibancada também é aqui.</p><div className="auth-tabs"><button className={mode==="login"?"active":""} onClick={()=>setMode("login")}>Entrar</button><button className={mode==="register"?"active":""} onClick={()=>setMode("register")}>Criar conta</button></div><form noValidate onSubmit={authenticate}><label>Usuário</label><input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required minLength={3}/>{mode==="register"&&<><label>E-mail</label><input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></>}<label>Senha</label><input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==="login"?"current-password":"new-password"} required minLength={8}/><button type="submit" className="primary-btn" disabled={busy}>{busy?<LoaderCircle className="spin"/>:null}{busy?"Aguarde...":mode==="login"?"Entrar com E-mail":"Criar minha conta"}</button></form>{error&&<div className="error">{error}</div>}{message&&<div className="notice">{message}</div>}<small>TORCIDA+ · A paixão nos conecta.</small></div></section></main>;
const nav=[{name:"Início" as Tab,icon:Home},{name:"Chat" as Tab,icon:MessageCircle},{name:"Eventos" as Tab,icon:CalendarDays},{name:"Loja" as Tab,icon:ShoppingCart},{name:"Notificações" as Tab,icon:Bell},{name:"Mais" as Tab,icon:Menu}];
return <main className="app-shell"><header className="app-header"><button className="sidebar-toggle" aria-label="Abrir menu de navegação" aria-expanded={menuOpen} onClick={()=>setMenuOpen(v=>!v)}><Menu/></button><div className="wordmark">TORCIDA<span>+</span></div><div className="header-actions"><button><Search/></button><button aria-label="Notificações" onClick={()=>setTab("Notificações")}><Bell/>{unread>0&&<i className="notification-badge">{unread>99?"99+":unread}</i>}</button><button className="avatar-mini">M</button></div></header><nav aria-label="Navegação principal" className={"desktop-tabs "+(menuOpen?"open":"")}>{nav.map(n=><button className={tab===n.name?"selected":""} onClick={()=>{setTab(n.name);setMenuOpen(false)}} key={n.name}><n.icon/>{n.name}{n.name==="Notificações"&&unread>0?<i className="sidebar-badge">{unread>99?"99+":unread}</i>:null}</button>)}</nav>{menuOpen&&<button className="sidebar-backdrop" aria-label="Fechar menu" onClick={()=>setMenuOpen(false)}/>}<section className="dashboard"><div className="welcome-row"><div><span className="kicker"><Flame/> A PAIXÃO NOS UNE</span><h1>{tab==="Início"?"Fala, torcedor!":tab}</h1><p>Fique por dentro de tudo que acontece na sua torcida.</p></div><button className="outline-btn" onClick={logout}><LogOut/> Sair</button></div>
{tab==="Início"&&<><div className="featured-banner"><span className="live-pill">● DESTAQUE DA TORCIDA</span><h2>A arquibancada<br/>é nossa casa.</h2><p>Notícias, resenha e emoção em um só lugar.</p><button onClick={()=>setTab("Chat")}>Entrar na conversa <ChevronRight/></button></div><div className="section-title"><h2>Movimento da torcida</h2><span>VER TUDO ›</span></div><form className="content-card publish-form" onSubmit={publish}><h2>Compartilhe com a torcida</h2><label htmlFor="torcida-id">ID da sua torcida</label><input id="torcida-id" className="dark-input" inputMode="numeric" placeholder="ID da comunidade" value={torcidaId} onChange={e=>setTorcidaId(e.target.value)} required/><textarea aria-label="Texto da publicação" placeholder="O que está acontecendo na arquibancada?" value={newPost} onChange={e=>setNewPost(e.target.value)} maxLength={5000}/><label htmlFor="post-image" className="file-label">Adicionar foto (JPEG, PNG ou WEBP · até 5 MB)</label><input id="post-image" type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>{const file=e.target.files?.[0]||null;if(file&&(file.size>5*1024*1024||!["image/jpeg","image/png","image/webp"].includes(file.type))){setFeedError(file.size>5*1024*1024?"A imagem deve ter no máximo 5 MB.":"Formato inválido. Use JPEG, PNG ou WEBP.");e.target.value="";setPostImage(null);return;}setFeedError("");setPostImage(file);}}/><button className="primary-btn" disabled={publishing}>{publishing?"Publicando...":"Publicar"}</button></form>{feedNotice&&<div className="content-card"><p>{feedNotice}</p></div>}{feedLoading&&<div className="content-card">Carregando publicações da sua torcida...</div>}{feedError&&<div className="content-card"><p>{feedError}</p></div>}{!feedLoading&&!feedError&&posts.length===0&&<div className="content-card"><h3>Seu feed está começando!</h3><p>Quando houver publicações nas torcidas das quais você participa, elas aparecerão aqui.</p></div>}{posts.map(post=><article className="feed-card" id={"publicacao-"+post.id} key={post.id}><div className="post-head">{post.autor_foto?<img className="post-avatar-img" src={post.autor_foto} alt=""/>:<div className="post-avatar">{(post.autor_nome_exibicao||post.autor_username||"T").slice(0,2).toUpperCase()}</div>}<div><b>{post.autor_nome_exibicao||post.autor_username}</b><small>@{post.autor_username} · {new Date(post.criada_em).toLocaleString("pt-BR")}</small></div></div><p className="post-copy">{post.texto}</p>{post.imagem&&<img className="post-image" src={post.imagem} alt="Imagem da publicação"/>}<div className="post-actions"><button className={post.curtida_pelo_usuario?"liked":""} onClick={()=>toggleLike(post.id)}><Heart/> {post.total_curtidas||0} Curtir</button><button onClick={()=>openComments===post.id?setOpenComments(null):loadComments(post.id)}><MessageSquare/> {post.total_comentarios||0} Comentários</button><button onClick={()=>void sharePost(post)} aria-label={"Compartilhar publicação de "+(post.autor_nome_exibicao||post.autor_username)}><Share2/> Compartilhar</button></div>{openComments===post.id&&<div className="comments-panel">{(comments[post.id]||[]).map(c=><div className="comment-row" key={c.id}><b>{c.autor_nome_exibicao||c.autor_username}</b><span>{c.texto}</span></div>)}<div className="comment-compose"><input value={commentDrafts[post.id]||""} onChange={e=>setCommentDrafts(v=>({...v,[post.id]:e.target.value}))} placeholder="Escreva um comentário..." maxLength={2000}/><button onClick={()=>sendComment(post.id)} disabled={commentBusy===post.id||!(commentDrafts[post.id]||"").trim()}>{commentBusy===post.id?"...":"Enviar"}</button></div></div>}</article>)}<div className="quick-grid"><button onClick={()=>setTab("Chat")}><MessageCircle/><b>Chat da torcida</b><small>Converse com a galera</small></button><button onClick={()=>setTab("Eventos")}><Ticket/><b>Próximos eventos</b><small>Jogos e caravanas</small></button><button onClick={()=>setTab("Loja")}><ShoppingCart/><b>Loja da torcida</b><small>Produtos e materiais</small></button></div></>}
{tab==="Notificações"&&<div className="content-card"><div className="notification-heading"><h2>Notificações</h2><button className="outline-btn" onClick={markAllNoticesRead} disabled={!unread}>Marcar todas como lidas</button></div>{noticeLoading&&<p>Carregando notificações...</p>}{noticeError&&<div className="error">{noticeError}</div>}{!noticeLoading&&notices.length===0&&!noticeError&&<p>Você está em dia! Nenhuma notificação por enquanto.</p>}{notices.map(n=><button className={"notification-row "+(!n.lida_em?"unread":"")} key={n.id} onClick={()=>openNotice(n)}><span className="notification-icon">{n.tipo==="curtida"?"♥":n.tipo==="comentario"?"✎":n.tipo==="publicacao_pendente"?"✓":"●"}</span><span><b>{n.ator_username||"TORCIDA+"}</b><small>{n.texto}</small><small>{new Date(n.criada_em).toLocaleString("pt-BR")}</small></span>{!n.lida_em&&<i/>}</button>)}</div>}
{tab==="Chat"&&<Chat tokens={tokens} onTokens={save} onStartCall={(id,mode)=>void call(id,mode)}/>}
{tab==="Eventos"&&<div className="quick-grid"><div className="content-card"><CalendarDays/><h3>Jogos e encontros</h3><p>Confira os próximos eventos da sua comunidade.</p><small className="coming">Módulo em desenvolvimento</small></div><div className="content-card"><Users/><h3>Caravanas</h3><p>Organize viagens e reúna sua torcida.</p><small className="coming">Módulo em desenvolvimento</small></div></div>}
{tab==="Loja"&&<Store tokens={tokens} onTokens={save}/>}
{tab==="Mais"&&<div style={{display:"grid",gap:14}}>
{moreSection==="menu"?<div className="quick-grid">
<button className="content-card" style={{textAlign:"left",cursor:"pointer"}} onClick={()=>setMoreSection("perfil")}><UserCircle/><b>Meu perfil</b><small>Dados e conta</small></button>
<button className="content-card" style={{textAlign:"left",cursor:"pointer"}} onClick={()=>setMoreSection("torcidas")}><Users/><b>Minhas torcidas</b><small>Comunidades que participo</small></button>
<button className="content-card" style={{textAlign:"left",cursor:"pointer"}} onClick={()=>setMoreSection("configuracoes")}><Settings/><b>Configurações</b><small>Privacidade e segurança</small></button>
<button className="content-card" style={{textAlign:"left",cursor:"pointer"}} onClick={()=>setMoreSection("admin")}><ShieldCheck/><b>Painel administrativo</b><small>Gestão da plataforma</small></button>
<button className="content-card" style={{textAlign:"left",cursor:"pointer"}} onClick={()=>setMoreSection("moderacao")}><ShieldCheck/><b>Moderação</b><small>Aprovação de publicações</small></button>
</div>:<>
<button className="outline-btn" style={{justifySelf:"start"}} onClick={()=>setMoreSection("menu")}><ArrowLeft/> Voltar</button>
{moreSection==="perfil"&&<section className="content-card"><h2><UserCircle/> Meu perfil</h2><p>Sua sessão está ativa no TORCIDA+.</p><p>Para proteger sua conta, não compartilhe sua senha ou códigos de acesso.</p><button className="outline-btn" onClick={()=>setMoreSection("configuracoes")}>Ir para segurança da conta</button></section>}
{moreSection==="torcidas"&&<TorcidasPanel tokens={tokens} api={API}/>}
{moreSection==="configuracoes"&&<section className="content-card"><h2><Settings/> Configurações e segurança</h2><p>Gerencie o acesso à sua conta neste dispositivo.</p><div style={{display:"grid",gap:10,marginTop:14}}><div><b>Sessão</b><small style={{display:"block",opacity:.75}}>Sua conta está conectada neste aparelho.</small></div><button className="outline-btn" onClick={logout}><LogOut/> Encerrar sessão neste dispositivo</button></div></section>}
{moreSection==="admin"&&<PlatformAdminPanel tokens={tokens} api={API}/>}
{moreSection==="moderacao"&&<ModeracaoPanel tokens={tokens} api={API}/>}
</>}
</div>}</section><nav className="mobile-nav">{nav.filter(n=>n.name!=="Mais").map(n=><button className={tab===n.name?"selected":""} onClick={()=>setTab(n.name)} key={n.name}><n.icon/><span>{n.name}</span></button>)}<button onClick={()=>setMenuOpen(true)}><Menu/><span>Menu</span></button></nav><footer className="app-footer"><ShieldCheck/> TORCIDA+ 2.0.0 · A paixão nos conecta.</footer></main>
}


function PlatformAdminPanel({tokens,api}:{tokens:Tokens;api:string}){
 const [overview,setOverview]=useState<any>(null),[users,setUsers]=useState<any[]>([]),[torcidas,setTorcidas]=useState<any[]>([]);
 const [query,setQuery]=useState(""),[filter,setFilter]=useState("todos"),[page,setPage]=useState(1),[count,setCount]=useState(0);
 const [loading,setLoading]=useState(false),[denied,setDenied]=useState(false),[error,setError]=useState(""),[userBusy,setUserBusy]=useState<number|null>(null),[notice,setNotice]=useState("");
 const [managedTorcida,setManagedTorcida]=useState<number|null>(null),[managedMembers,setManagedMembers]=useState<any[]>([]),[memberLoading,setMemberLoading]=useState(false),[memberBusy,setMemberBusy]=useState<number|null>(null);
 const [audit,setAudit]=useState<any[]>([]),[auditOpen,setAuditOpen]=useState(false),[auditLoading,setAuditLoading]=useState(false);
 async function get(path:string){const r=await fetch(api+path,{headers:{Authorization:"Bearer "+tokens.access}});const d=await r.json().catch(()=>({}));if(!r.ok){const e=new Error(d.detail||"Falha ao consultar painel administrativo.");(e as any).status=r.status;throw e;}return d;}
 async function loadUsers(p=page,q=query,f=filter){const params=new URLSearchParams({page:String(p)});if(q.trim())params.set("q",q.trim());if(f!=="todos")params.set("status",f);const d=await get("/api/auth/platform-admin/users/?"+params.toString());setUsers(d.results||[]);setCount(d.count||0);}
 async function load(){if(!tokens.access)return;setLoading(true);setError("");setDenied(false);try{const [o,t]=await Promise.all([get("/api/auth/platform-admin/overview/"),get("/api/auth/platform-admin/torcidas/")]);setOverview(o);setTorcidas(t.results||[]);await loadUsers(1,query,filter);setPage(1);}catch(e){if((e as any)?.status===403)setDenied(true);else setError(e instanceof Error?e.message:"Falha ao carregar painel.");}finally{setLoading(false);}}
 useEffect(()=>{load()},[tokens.access]);
 async function search(e:FormEvent){e.preventDefault();setLoading(true);setError("");try{await loadUsers(1,query,filter);setPage(1);}catch(e){setError(e instanceof Error?e.message:"Falha ao pesquisar.");}finally{setLoading(false);}}
 async function changePage(next:number){setLoading(true);try{await loadUsers(next);setPage(next);}catch(e){setError(e instanceof Error?e.message:"Falha ao mudar página.");}finally{setLoading(false);}}
 async function editTorcida(t:any){const nome=window.prompt("Nome da torcida:",t.nome);if(nome===null)return;const slug=window.prompt("Identificador (slug):",t.slug);if(slug===null)return;const cor=window.prompt("Cor principal hexadecimal:",t.cor_principal||"#202020");if(cor===null)return;setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/torcidas/"+t.id+"/",{method:"PATCH",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokens.access},body:JSON.stringify({nome,slug,cor_principal:cor})});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Não foi possível editar a torcida.");setTorcidas(items=>items.map(item=>item.id===t.id?{...item,...d}:item));setNotice(d.detail||"Torcida atualizada.");}catch(e){setError(e instanceof Error?e.message:"Falha ao editar torcida.");}}
 async function deleteTorcida(t:any){if(!window.confirm("Excluir a torcida "+t.nome+"? Esta ação só será permitida se não houver integrantes nem publicações."))return;setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/torcidas/"+t.id+"/",{method:"DELETE",headers:{Authorization:"Bearer "+tokens.access}});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Não foi possível excluir a torcida.");setTorcidas(items=>items.filter(item=>item.id!==t.id));setOverview((o:any)=>o?{...o,torcidas_total:Math.max(0,o.torcidas_total-1)}:o);setNotice(d.detail||"Torcida excluída.");}catch(e){setError(e instanceof Error?e.message:"Falha ao excluir torcida.");}}
 async function loadAudit(){setAuditLoading(true);setError("");try{const d=await get("/api/auth/platform-admin/audit/");setAudit(d.results||[]);setAuditOpen(true);}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar histórico.");}finally{setAuditLoading(false);}}
 async function loadManagedMembers(id:number){setManagedTorcida(id);setMemberLoading(true);setError("");try{const d=await get("/api/torcidas/"+id+"/membros/");setManagedMembers(Array.isArray(d)?d:(d.results||[]));}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar responsáveis.");}finally{setMemberLoading(false);}}
 async function setMemberRole(m:any,papel:string){if(!managedTorcida)return;const label=papel==="admin"?"administrador da torcida":papel==="moderador"?"moderador":"membro";if(!window.confirm("Definir @"+m.username+" como "+label+"?"))return;setMemberBusy(m.id);setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/torcidas/"+managedTorcida+"/membros/"+m.id+"/",{method:"PATCH",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokens.access},body:JSON.stringify({papel})});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Não foi possível alterar a responsabilidade.");setManagedMembers(v=>v.map(x=>x.id===m.id?{...x,...d}:x));setNotice(d.detail||"Responsabilidade atualizada.");}catch(e){setError(e instanceof Error?e.message:"Falha ao atualizar responsável.");}finally{setMemberBusy(null);}}
 async function removeManagedMember(m:any){if(!managedTorcida||!window.confirm("Remover @"+m.username+" desta torcida?"))return;setMemberBusy(m.id);setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/torcidas/"+managedTorcida+"/membros/"+m.id+"/",{method:"DELETE",headers:{Authorization:"Bearer "+tokens.access}});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Não foi possível remover o integrante.");setManagedMembers(v=>v.filter(x=>x.id!==m.id));setNotice(d.detail||"Integrante removido.");}catch(e){setError(e instanceof Error?e.message:"Falha ao remover integrante.");}finally{setMemberBusy(null);}}
 async function resetUserPassword(u:any){const first=window.prompt("Defina uma nova senha para @"+u.username+" (mínimo de 8 caracteres):");if(first===null)return;if(first.length<8){setError("A nova senha precisa ter pelo menos 8 caracteres.");return;}const second=window.prompt("Digite novamente a nova senha para confirmar:");if(second===null)return;if(first!==second){setError("As senhas não conferem. Nenhuma alteração foi feita.");return;}if(!window.confirm("Confirmar a redefinição da senha de @"+u.username+"? A senha atual não será exibida."))return;setUserBusy(u.id);setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/users/"+u.id+"/reset-password/",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokens.access},body:JSON.stringify({new_password:first})});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(Array.isArray(d.detail)?d.detail.join(" "):d.detail||"Não foi possível redefinir a senha.");setNotice(d.detail||"Senha redefinida com sucesso.");}catch(e){setError(e instanceof Error?e.message:"Falha ao redefinir senha.");}finally{setUserBusy(null);}}
 async function changeUserStatus(u:any){const next=!u.is_active;const action=next?"reativar":"bloquear";if(!window.confirm("Deseja "+action+" a conta @"+u.username+"?"))return;setUserBusy(u.id);setError("");setNotice("");try{const r=await fetch(api+"/api/auth/platform-admin/users/"+u.id+"/status/",{method:"PATCH",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokens.access},body:JSON.stringify({is_active:next})});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Não foi possível alterar a conta.");setUsers(items=>items.map(item=>item.id===u.id?{...item,is_active:d.is_active}:item));setNotice(d.detail||"Status atualizado.");}catch(e){setError(e instanceof Error?e.message:"Falha ao alterar usuário.");}finally{setUserBusy(null);}}
 if(denied)return <section className="content-card" style={{gridColumn:"1 / -1"}}><h2><ShieldCheck/> Administração global</h2><p>Área exclusiva do administrador global do TORCIDA+.</p></section>;
 return <section className="content-card" style={{gridColumn:"1 / -1"}}>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,flexWrap:"wrap"}}><div><h2><ShieldCheck/> Painel administrativo global</h2><p>Visão geral de usuários, comunidades e moderação da plataforma.</p></div><button className="outline-btn" onClick={load} disabled={loading}>{loading?"Atualizando...":"Atualizar dados"}</button></div>
  {error&&<p className="error">{error}</p>}{loading&&!overview&&<p>Carregando painel...</p>}
  {overview&&<>
   <div className="quick-grid" style={{marginTop:14}}>
    {[[overview.usuarios_total,"Usuários cadastrados"],[overview.usuarios_ativos,"Usuários ativos"],[overview.usuarios_bloqueados,"Contas bloqueadas"],[overview.torcidas_total,"Torcidas"],[overview.integrantes_total,"Vínculos de membros"],[overview.publicacoes_pendentes,"Publicações pendentes"],[overview.publicacoes_aprovadas,"Publicações aprovadas"],[overview.publicacoes_rejeitadas,"Publicações rejeitadas"]].map(([value,label])=><div className="content-card" key={String(label)}><b style={{fontSize:26}}>{value}</b><small style={{display:"block",opacity:.75}}>{label}</small></div>)}
   </div>
   <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,flexWrap:"wrap",marginTop:18}}><div><h3>Histórico de auditoria</h3><p>Registro de ações administrativas com responsável, data e detalhes.</p></div><button className="outline-btn" onClick={()=>auditOpen?setAuditOpen(false):loadAudit()} disabled={auditLoading}>{auditLoading?"Carregando...":auditOpen?"Ocultar histórico":"Consultar histórico"}</button></div>
   {auditOpen&&<div style={{overflowX:"auto",marginTop:10}}>{audit.length===0?<p>Nenhuma ação registrada ainda.</p>:<table style={{width:"100%",borderCollapse:"collapse",minWidth:650}}><thead><tr><th align="left">Data</th><th align="left">Responsável</th><th align="left">Ação</th><th align="left">Descrição</th></tr></thead><tbody>{audit.map(a=><tr key={a.id} style={{borderTop:"1px solid #444"}}><td style={{padding:"9px 6px"}}>{new Date(a.criado_em).toLocaleString("pt-BR")}</td><td>@{a.ator}</td><td>{a.acao.replaceAll("_"," ")}</td><td>{a.descricao}</td></tr>)}</tbody></table>}</div>}
   <h3 style={{marginTop:22}}>Gestão de usuários</h3>
   <form onSubmit={search} style={{display:"flex",gap:8,flexWrap:"wrap",margin:"12px 0"}}><input className="dark-input" style={{flex:"1 1 180px"}} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar por usuário ou e-mail"/><select className="dark-input" value={filter} onChange={e=>setFilter(e.target.value)}><option value="todos">Todos</option><option value="ativos">Ativos</option><option value="bloqueados">Bloqueados</option></select><button className="primary-btn">Pesquisar</button></form>
   <div style={{overflowX:"auto"}}><table style={{width:"100%",borderCollapse:"collapse",minWidth:560}}><thead><tr><th align="left">Usuário</th><th align="left">E-mail</th><th align="left">Status</th><th align="left">Torcidas</th><th align="left">Cadastro</th><th align="left">Ações</th></tr></thead><tbody>{users.map(u=><tr key={u.id} style={{borderTop:"1px solid #444"}}><td style={{padding:"10px 6px"}}>@{u.username}{u.is_superuser&&<small style={{display:"block"}}>Administrador global</small>}</td><td>{u.email||"—"}</td><td>{u.is_active?"Ativo":"Bloqueado"}</td><td>{u.total_torcidas}</td><td>{u.date_joined?new Date(u.date_joined).toLocaleDateString("pt-BR"):"—"}</td><td>{!u.is_superuser&&<div style={{display:"flex",gap:6,flexWrap:"wrap"}}><button className="outline-btn" disabled={userBusy===u.id} onClick={()=>changeUserStatus(u)}>{userBusy===u.id?"Aguarde...":u.is_active?"Bloquear":"Reativar"}</button><button className="outline-btn" disabled={userBusy===u.id} onClick={()=>resetUserPassword(u)}>Redefinir senha</button></div>}</td></tr>)}</tbody></table></div>{notice&&<p className="notice">{notice}</p>}
   <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginTop:12}}><small>{count} usuário(s) · Página {page} de {Math.max(1,Math.ceil(count/30))}</small><div style={{display:"flex",gap:8}}><button className="outline-btn" disabled={page<=1||loading} onClick={()=>changePage(page-1)}>Anterior</button><button className="outline-btn" disabled={page>=Math.ceil(count/30)||loading} onClick={()=>changePage(page+1)}>Próxima</button></div></div>
   <h3 style={{marginTop:24}}>Comunidades cadastradas</h3>
   {torcidas.length===0?<p>Nenhuma torcida cadastrada.</p>:torcidas.map(t=><div key={t.id} style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,flexWrap:"wrap",padding:"12px 0",borderTop:"1px solid #444"}}><div><b>{t.nome}</b><small style={{display:"block",opacity:.7}}>/{t.slug} · ID {t.id}</small><small>{t.total_membros} membros · {t.total_publicacoes} publicações</small></div><div style={{display:"flex",gap:8,flexWrap:"wrap"}}><button className="outline-btn" onClick={()=>loadManagedMembers(t.id)}>Responsáveis</button><button className="outline-btn" onClick={()=>editTorcida(t)}>Editar</button><button className="outline-btn" onClick={()=>deleteTorcida(t)}>Excluir</button></div></div>)}
   {managedTorcida!==null&&<section style={{marginTop:18,padding:14,border:"1px solid #555",borderRadius:12}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,flexWrap:"wrap"}}><h3>Responsáveis da torcida #{managedTorcida}</h3><button className="outline-btn" onClick={()=>{setManagedTorcida(null);setManagedMembers([]);}}>Fechar</button></div><p>Defina administradores e moderadores. Cada torcida precisa manter pelo menos um administrador.</p>{memberLoading&&<p>Carregando integrantes...</p>}{!memberLoading&&managedMembers.length===0&&<p>Nenhum integrante vinculado.</p>}{managedMembers.map(m=><div key={m.id} style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,flexWrap:"wrap",padding:"10px 0",borderTop:"1px solid #444"}}><div><b>@{m.username}</b><small style={{display:"block",opacity:.7}}>{m.papel==="admin"?"Administrador":m.papel==="moderador"?"Moderador":"Membro"}</small></div><div style={{display:"flex",gap:6,flexWrap:"wrap"}}><select className="dark-input" value={m.papel} disabled={memberBusy===m.id} onChange={e=>setMemberRole(m,e.target.value)}><option value="admin">Administrador</option><option value="moderador">Moderador</option><option value="membro">Membro</option></select><button className="outline-btn" disabled={memberBusy===m.id} onClick={()=>removeManagedMember(m)}>Remover</button></div></div>)}</section>}
  </>}
 </section>;
}

function TorcidasPanel({tokens,api}:{tokens:Tokens;api:string}){
 const [items,setItems]=useState<any[]>([]);
 const [nome,setNome]=useState("Tropa do Matheus");
 const [slug,setSlug]=useState("tropa-do-matheus");
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState("");
 const [notice,setNotice]=useState("");
 const [invite,setInvite]=useState("");
 const [createdToken,setCreatedToken]=useState("");
 const [inviteTarget,setInviteTarget]=useState<number|null>(null);
 const [selectedTorcida,setSelectedTorcida]=useState<number|null>(null);
 const [members,setMembers]=useState<any[]>([]);
 const [membersLoading,setMembersLoading]=useState(false);
 const [memberBusy,setMemberBusy]=useState<number|null>(null);
 async function showMembers(id:number){setSelectedTorcida(id);setMembersLoading(true);setError("");try{const d=await request("/api/torcidas/"+id+"/membros/");setMembers(Array.isArray(d)?d:(d.results||[]));}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar membros.");}finally{setMembersLoading(false);}}
 async function changeMember(id:number,papel:string){setMemberBusy(id);setError("");try{const d=await request("/api/torcidas/"+selectedTorcida+"/membros/"+id+"/","PATCH",{papel});setMembers(v=>v.map(m=>m.id===id?d:m));setNotice("Permissão do integrante atualizada.");}catch(e){setError(e instanceof Error?e.message:"Falha ao atualizar integrante.");}finally{setMemberBusy(null);}}
 async function removeMember(id:number){if(!window.confirm("Deseja realmente remover este integrante da torcida?"))return;setMemberBusy(id);setError("");try{await request("/api/torcidas/"+selectedTorcida+"/membros/"+id+"/","DELETE");setMembers(v=>v.filter(m=>m.id!==id));setNotice("Integrante removido.");}catch(e){setError(e instanceof Error?e.message:"Falha ao remover integrante.");}finally{setMemberBusy(null);}}
 async function request(path:string,method="GET",body?:any){
  const r=await fetch(api+path,{method,headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokens.access},...(body?{body:JSON.stringify(body)}:{})});
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(d.detail||Object.values(d).flat().join(" ")||"Não foi possível concluir.");
  return d;
 }
 async function load(){setLoading(true);setError("");try{const d=await request("/api/torcidas/");setItems(Array.isArray(d)?d:(d.results||[]));}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar torcidas.");}finally{setLoading(false);}}
 useEffect(()=>{load()},[tokens.access]);
 async function create(e:FormEvent){e.preventDefault();setError("");setNotice("");try{const clean=slug.trim().toLowerCase().replace(/[^a-z0-9-]/g,"-").replace(/-+/g,"-").replace(/^-|-$/g,"");const d=await request("/api/torcidas/","POST",{nome:nome.trim(),slug:clean,cor_principal:"#202020"});setItems(v=>[d,...v]);setNotice("Pelotão criado! Você foi cadastrado como administrador.");}catch(e){setError(e instanceof Error?e.message:"Falha ao criar pelotão.");}}
 async function createInvite(id:number){setError("");setNotice("");try{const d=await request("/api/torcidas/"+id+"/convites/","POST",{validade_dias:7,limite_usos:20,papel:"membro"});setCreatedToken(d.token);setInviteTarget(id);setNotice("Convite do pelotão criado. Compartilhe o código com os integrantes.");}catch(e){setError(e instanceof Error?e.message:"Falha ao criar convite.");}}
 async function acceptInvite(e:FormEvent){e.preventDefault();setError("");setNotice("");try{await request("/api/torcidas/convites/aceitar/","POST",{token:invite.trim()});setInvite("");setNotice("Você entrou no pelotão pelo convite.");await load();}catch(e){setError(e instanceof Error?e.message:"Convite inválido.");}}
 return <div className="content-card" style={{gridColumn:"1 / -1"}}>
  <h2><Users/> Meus pelotões</h2>
  <p>Organize os pelotões da torcida principal, acompanhe os integrantes e envie convites.</p>
  <form onSubmit={create} style={{display:"grid",gap:10,marginTop:14}}>
   <label>Nome do pelotão</label><input className="dark-input" value={nome} onChange={e=>{setNome(e.target.value);setSlug(e.target.value.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,""));}} required maxLength={120}/>
   <label>Identificador</label><input className="dark-input" value={slug} onChange={e=>setSlug(e.target.value)} required maxLength={140}/>
   <button className="primary-btn" disabled={loading}>Criar pelotão</button>
  </form>
  <form onSubmit={acceptInvite} style={{display:"grid",gap:10,marginTop:18}}>
   <label>Entrar com código de convite</label><input className="dark-input" value={invite} onChange={e=>setInvite(e.target.value)} placeholder="Cole o código recebido"/>
   <button className="outline-btn" disabled={!invite.trim()}>Aceitar convite</button>
  </form>
  <div style={{marginTop:18}}><h3>Pelotões da torcida</h3>{loading&&<p>Carregando...</p>}{!loading&&items.length===0&&<p>Nenhum pelotão vinculado a esta conta ainda.</p>}
   {items.map(t=><div key={t.id} style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,padding:"12px 0",borderBottom:"1px solid #333"}}><div><b>{t.nome}</b><small style={{display:"block",opacity:.7}}>ID {t.id} · {t.slug}</small></div><div style={{display:"flex",gap:8,flexWrap:"wrap"}}><button className="outline-btn" onClick={()=>showMembers(t.id)}>Ver membros</button><button className="outline-btn" onClick={()=>createInvite(t.id)}>Gerar convite</button></div></div>)}
  </div>
  {selectedTorcida!==null&&<section style={{marginTop:18,padding:14,border:"1px solid #444",borderRadius:12}}>
   <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10}}><h3>Integrantes do pelotão #{selectedTorcida}</h3><button className="outline-btn" onClick={()=>setSelectedTorcida(null)}>Fechar</button></div>
   {membersLoading&&<p>Carregando integrantes...</p>}
   {!membersLoading&&members.length===0&&<p>Nenhum integrante encontrado.</p>}
   {members.map(m=><div key={m.id} style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,padding:"10px 0",borderBottom:"1px solid #333",flexWrap:"wrap"}}>
    <div><b>@{m.username}</b><small style={{display:"block",opacity:.7}}>{m.papel==="admin"?"Administrador":m.papel==="moderador"?"Moderador":"Membro"}</small></div>
    {m.papel!=="admin"&&<div style={{display:"flex",gap:6,flexWrap:"wrap"}}><button className="outline-btn" disabled={memberBusy===m.id} onClick={()=>changeMember(m.id,m.papel==="moderador"?"membro":"moderador")}>{m.papel==="moderador"?"Rebaixar":"Promover"}</button><button className="outline-btn" disabled={memberBusy===m.id} onClick={()=>removeMember(m.id)}>Remover</button></div>}
   </div>)}
  </section>}
  {createdToken&&<div className="notice" style={{marginTop:12,overflowWrap:"anywhere"}}><b>Código de convite</b><p>{createdToken}</p><button className="outline-btn" onClick={()=>navigator.clipboard?.writeText(createdToken)}>Copiar código</button></div>}
  {error&&<div className="error" style={{marginTop:12}}>{error}</div>}{notice&&<div className="notice" style={{marginTop:12}}>{notice}</div>}
 </div>;
}


function ModeracaoPanel({tokens,api}:{tokens:Tokens;api:string}){
 const [items,setItems]=useState<any[]>([]);
 const [loading,setLoading]=useState(false);
 const [busy,setBusy]=useState<number|null>(null);
 const [error,setError]=useState("");
 const [notice,setNotice]=useState("");
 const [accessDenied,setAccessDenied]=useState(false);
 async function request(path:string,method="GET"){
  const r=await fetch(api+path,{method,headers:{Authorization:"Bearer "+tokens.access}});
  const d=await r.json().catch(()=>({}));
  if(!r.ok){const message=d.detail||Object.values(d).flat().join(" ")||"Não foi possível concluir.";const e=new Error(message);(e as any).status=r.status;throw e;}
  return d;
 }
 async function load(){
  if(!tokens.access)return;
  setLoading(true);setError("");setAccessDenied(false);
  try{const d=await request("/api/comunidade/publicacoes/?status=pendente");setItems(Array.isArray(d)?d:(d.results||[]));}
  catch(e){if((e as any)?.status===403){setAccessDenied(true);setItems([]);}else setError(e instanceof Error?e.message:"Falha ao carregar fila.");}
  finally{setLoading(false);}
 }
 useEffect(()=>{load()},[tokens.access]);
 async function decide(id:number,action:"aprovar"|"rejeitar"){
  if(action==="rejeitar"&&!window.confirm("Rejeitar esta publicação?"))return;
  setBusy(id);setError("");setNotice("");
  try{await request("/api/comunidade/publicacoes/"+id+"/"+action+"/","POST");setItems(v=>v.filter(p=>p.id!==id));setNotice(action==="aprovar"?"Publicação aprovada e liberada no feed.":"Publicação rejeitada.");}
  catch(e){setError(e instanceof Error?e.message:"Não foi possível moderar a publicação.");}
  finally{setBusy(null);}
 }
 return <section className="content-card" style={{gridColumn:"1 / -1"}}>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,flexWrap:"wrap"}}>
   <div><h2><ShieldCheck/> Central de moderação</h2><p>Revise as publicações antes que apareçam para os integrantes.</p></div>
   <button className="outline-btn" onClick={load} disabled={loading}>{loading?"Atualizando...":"Atualizar fila"}</button>
  </div>
  {accessDenied&&<p>Área restrita ao administrador global do TORCIDA+.</p>}
  {loading&&<p>Carregando publicações pendentes...</p>}
  {!loading&&!accessDenied&&items.length===0&&<p>Nenhuma publicação aguardando aprovação.</p>}
  {items.map(p=><article key={p.id} style={{borderTop:"1px solid #444",padding:"14px 0",marginTop:10}}>
   <div style={{display:"flex",justifyContent:"space-between",gap:10,flexWrap:"wrap"}}><b>{p.autor_nome_exibicao||p.autor_username||"Integrante"} · {p.torcida_nome||("Torcida #"+p.torcida)}</b><small>{new Date(p.criada_em).toLocaleString("pt-BR")}</small></div>
   <p style={{whiteSpace:"pre-wrap"}}>{p.texto}</p>
   {p.imagem&&<img src={p.imagem} alt="Imagem enviada para aprovação" style={{maxWidth:"100%",maxHeight:280,objectFit:"contain",borderRadius:10}}/>}
   <div style={{display:"flex",gap:8,flexWrap:"wrap",marginTop:12}}>
    <button className="primary-btn" disabled={busy===p.id} onClick={()=>decide(p.id,"aprovar")}>{busy===p.id?"Aguarde...":"Aprovar publicação"}</button>
    <button className="outline-btn" disabled={busy===p.id} onClick={()=>decide(p.id,"rejeitar")}>Rejeitar</button>
   </div>
  </article>)}
  {error&&<p className="error">{error}</p>}{notice&&<p className="notice">{notice}</p>}
 </section>;
}
