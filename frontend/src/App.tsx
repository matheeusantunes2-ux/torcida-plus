import { useEffect, useState } from "react";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";
import { PhoneCall, Video, Mic, ShieldCheck, Users, ArrowLeft, LoaderCircle } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "";
type RoomToken = { server_url: string; room: string; token: string; expires_in: number; provider: string };

export default function App() {
  const [conversationId, setConversationId] = useState("1");
  const [token, setToken] = useState<RoomToken | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [access, setAccess] = useState(localStorage.getItem("torcida_access") || "");
  const [authInput, setAuthInput] = useState("");

  useEffect(() => { if (access) localStorage.setItem("torcida_access", access); }, [access]);

  async function startCall() {
    if (!access.trim()) { setError("Informe seu token de acesso da API para iniciar a chamada."); return; }
    if (!/^\d+$/.test(conversationId)) { setError("Informe um número válido de conversa."); return; }
    setBusy(true); setError("");
    try {
      const response = await fetch(`${API}/api/chat/conversas/${conversationId}/chamada/token/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${access}`, "Content-Type": "application/json" }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Não foi possível entrar na chamada.");
      setToken(data as RoomToken);
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao conectar."); }
    finally { setBusy(false); }
  }

  if (token) return <main className="call-screen">
    <header className="call-top"><button className="icon-btn" onClick={() => setToken(null)} aria-label="Voltar"><ArrowLeft /></button><div><b>TORCIDA+ AO VIVO</b><span>Sala {token.room}</span></div><span className="secure"><ShieldCheck size={16}/> Acesso autorizado</span></header>
    <section className="conference"><LiveKitRoom serverUrl={token.server_url} token={token.token} connect={true} audio={true} video={true} onDisconnected={() => setToken(null)}><VideoConference /></LiveKitRoom></section>
    <p className="call-note">A chamada usa a infraestrutura LiveKit configurada pelo administrador. A criptografia ponta a ponta ainda não está habilitada.</p>
  </main>;

  return <main className="page">
    <nav className="nav"><div className="brand-mark">T+</div><div className="brand">TORCIDA<span>+</span></div><div className="nav-right"><span className="status-dot"/> Comunidade conectada</div></nav>
    <section className="hero">
      <div className="eyebrow"><span/> CONEXÃO DA TORCIDA</div>
      <h1>A arquibancada<br/><em>também é aqui.</em></h1>
      <p>Entre em uma chamada, reúna sua galera e viva cada conversa de qualquer lugar.</p>
      <div className="call-card">
        <div className="card-head"><div className="video-icon"><Video/></div><div><h2>Iniciar chamada</h2><p>Converse por áudio e vídeo com sua torcida.</p></div></div>
        <label htmlFor="conversation">ID da conversa</label>
        <input id="conversation" inputMode="numeric" value={conversationId} onChange={e=>setConversationId(e.target.value)} placeholder="Ex.: 12"/>
        <label htmlFor="access">Token de acesso (JWT)</label>
        <input id="access" type="password" autoComplete="off" value={authInput || access} onChange={e=>{setAuthInput(e.target.value);setAccess(e.target.value);}} placeholder="Cole seu token de acesso"/>
        <button className="start-btn" onClick={startCall} disabled={busy}>{busy ? <LoaderCircle className="spin"/> : <PhoneCall size={18}/>} {busy ? "Conectando..." : "Entrar na chamada"}</button>
        {error && <div className="error" role="alert">{error}</div>}
        <div className="features"><span><Mic size={15}/> Áudio</span><span><Video size={15}/> Vídeo</span><span><Users size={15}/> Grupo</span></div>
      </div>
    </section>
    <footer><ShieldCheck size={16}/> Sua participação é validada pela API TORCIDA+ <span>•</span> Chamadas com LiveKit</footer>
  </main>;
}