import { FormEvent, useState } from "react";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";
import { PhoneCall, Video, ShieldCheck, Users, ArrowLeft, LoaderCircle, LogOut } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "";
type RoomToken = { server_url: string; room: string; token: string };
type Tokens = { access: string; refresh: string };

export default function App() {
  const [tokens, setTokens] = useState<Tokens>(() => ({
    access: sessionStorage.getItem("torcida_access") || "",
    refresh: sessionStorage.getItem("torcida_refresh") || ""
  }));
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [conversationId, setConversationId] = useState("1");
  const [room, setRoom] = useState<RoomToken | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function saveTokens(value: Tokens) {
    setTokens(value);
    if (value.access) sessionStorage.setItem("torcida_access", value.access);
    else sessionStorage.removeItem("torcida_access");
    if (value.refresh) sessionStorage.setItem("torcida_refresh", value.refresh);
    else sessionStorage.removeItem("torcida_refresh");
  }

  async function result(response: Response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail || Object.values(data).flat().join(" ");
      throw new Error(typeof detail === "string" ? detail : "Não foi possível concluir.");
    }
    return data;
  }

  async function authenticate(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      if (mode === "register") {
        await result(await fetch(API + "/api/auth/cadastro/", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: username.trim(), email: email.trim(), password })
        }));
        setMode("login"); setMessage("Cadastro realizado. Entre com seus dados.");
      } else {
        const data = await result(await fetch(API + "/api/auth/login/", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: username.trim(), password })
        }));
        saveTokens({ access: data.access, refresh: data.refresh });
        setPassword(""); setMessage("Login realizado.");
      }
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao autenticar."); }
    finally { setBusy(false); }
  }

  async function validAccess() {
    const check = await fetch(API + "/api/auth/verify/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: tokens.access })
    });
    if (check.ok) return tokens.access;
    if (!tokens.refresh) throw new Error("Sessão expirada. Entre novamente.");
    const data = await result(await fetch(API + "/api/auth/refresh/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh })
    }));
    saveTokens({ access: data.access, refresh: data.refresh || tokens.refresh });
    return data.access as string;
  }

  async function startCall() {
    if (!/^\\d+$/.test(conversationId)) { setError("Informe um ID de conversa válido."); return; }
    setBusy(true); setError("");
    try {
      const access = await validAccess();
      const data = await result(await fetch(API + "/api/chat/conversas/" + conversationId + "/chamada/token/", {
        method: "POST", headers: { Authorization: "Bearer " + access }
      }));
      setRoom(data as RoomToken);
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao iniciar chamada."); }
    finally { setBusy(false); }
  }

  function logout() { saveTokens({ access: "", refresh: "" }); setRoom(null); setMessage("Você saiu da conta."); }

  if (room) return <main className="call-screen">
    <header className="call-top"><button className="icon-btn" onClick={() => setRoom(null)} aria-label="Voltar"><ArrowLeft /></button><div><b>TORCIDA+ AO VIVO</b><span>Sala {room.room}</span></div><span className="secure"><ShieldCheck size={16}/> Acesso autorizado</span></header>
    <section className="conference"><LiveKitRoom serverUrl={room.server_url} token={room.token} connect audio video onDisconnected={() => setRoom(null)}><VideoConference /></LiveKitRoom></section>
    <p className="call-note">A criptografia ponta a ponta ainda não está habilitada nesta chamada.</p>
  </main>;

  return <main className="page">
    <nav className="nav"><div className="brand-mark">T+</div><div className="brand">TORCIDA<span>+</span></div>{tokens.access && <button className="logout" onClick={logout}><LogOut size={15}/> Sair</button>}</nav>
    <section className="hero">
      <div className="intro"><div className="eyebrow"><span/> CONEXÃO DA TORCIDA</div><h1>A arquibancada<br/><em>também é aqui.</em></h1><p>Entre na comunidade, reúna sua galera e viva cada conversa.</p></div>
      <div className="call-card">
        {!tokens.access ? <>
          <div className="card-head"><div className="video-icon"><ShieldCheck/></div><div><h2>{mode === "login" ? "Bem-vindo de volta" : "Crie sua conta"}</h2><p>{mode === "login" ? "Acesse sua conta TORCIDA+." : "Faça parte da sua comunidade."}</p></div></div>
          <div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => {setMode("login");setError("");}}>Entrar</button><button className={mode === "register" ? "active" : ""} onClick={() => {setMode("register");setError("");}}>Cadastrar</button></div>
          <form onSubmit={authenticate}>
            <label htmlFor="username">Usuário</label><input id="username" autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} required minLength={3}/>
            {mode === "register" && <><label htmlFor="email">E-mail</label><input id="email" type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} required/></>}
            <label htmlFor="password">Senha</label><input id="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={e=>setPassword(e.target.value)} required minLength={8}/>
            <button className="start-btn" type="submit" disabled={busy}>{busy ? <LoaderCircle className="spin"/> : <ShieldCheck size={18}/>} {busy ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}</button>
          </form>
        </> : <>
          <div className="card-head"><div className="video-icon"><Video/></div><div><h2>Iniciar chamada</h2><p>Reúna sua torcida por áudio e vídeo.</p></div></div>
          <label htmlFor="conversation">ID da conversa</label><input id="conversation" inputMode="numeric" value={conversationId} onChange={e=>setConversationId(e.target.value)}/>
          <button className="start-btn" onClick={startCall} disabled={busy}>{busy ? <LoaderCircle className="spin"/> : <PhoneCall size={18}/>} {busy ? "Conectando..." : "Entrar na chamada"}</button>
          <div className="features"><span><Video size={15}/> Vídeo</span><span><Users size={15}/> Grupo</span></div>
        </>}
        {error && <div className="error" role="alert">{error}</div>}{message && <div className="notice" role="status">{message}</div>}
      </div>
    </section>
    <footer><ShieldCheck size={16}/> Autenticação pela API TORCIDA+ <span>•</span> Chamadas LiveKit</footer>
  </main>;
}
