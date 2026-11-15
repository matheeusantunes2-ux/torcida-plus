import { useEffect, useState, FormEvent } from "react";
import { UserCircle, Camera, Save, RefreshCw } from "lucide-react";
type Props={tokens:{access:string;refresh:string};onTokens:(v:{access:string;refresh:string})=>void;api:string};
type Data={username:string;nome_exibicao:string;biografia:string;foto:string|null};
export default function Profile({tokens,onTokens,api}:Props){
 const [data,setData]=useState<Data>({username:"",nome_exibicao:"",biografia:"",foto:null});
 const [photo,setPhoto]=useState<File|null>(null),[preview,setPreview]=useState(""),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(""),[notice,setNotice]=useState("");
 async function request(init:RequestInit={}){
  let token=tokens.access;
  const send=()=>fetch(api+"/api/auth/perfil/",{...init,headers:{...(init.body instanceof FormData?{}:{"Content-Type":"application/json"}),Authorization:"Bearer "+token,...init.headers}});
  let r=await send();
  if(r.status===401&&tokens.refresh){const x=await fetch(api+"/api/auth/refresh/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({refresh:tokens.refresh})});if(x.ok){const d=await x.json();token=d.access;onTokens({access:d.access,refresh:d.refresh||tokens.refresh});r=await send();}}
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(d.detail||Object.values(d).flat().join(" ")||"Não foi possível concluir.");
  return d;
 }
 async function load(){setLoading(true);setError("");try{const d=await request();setData(d);setPreview(d.foto||"");}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar perfil.");}finally{setLoading(false);}}
 useEffect(()=>{void load();},[]);
 async function save(e:FormEvent){e.preventDefault();setBusy(true);setError("");setNotice("");try{const body=new FormData();body.append("nome_exibicao",data.nome_exibicao);body.append("biografia",data.biografia);if(photo)body.append("foto",photo);const d=await request({method:"PATCH",body});setData(d);setPreview(d.foto||"");setPhoto(null);setNotice("Perfil atualizado com sucesso.");}catch(e){setError(e instanceof Error?e.message:"Não foi possível salvar o perfil.");}finally{setBusy(false);}}
 return <section className="content-card profile-panel"><header><UserCircle/><div><h2>Meu perfil</h2><p>Atualize suas informações e sua foto de exibição.</p></div></header>{error&&<div className="error">{error}</div>}{notice&&<div className="notice">{notice}</div>}{loading?<p>Carregando perfil...</p>:<form onSubmit={save}><div className="profile-photo">{preview?<img src={preview} alt="Foto do perfil"/>:<UserCircle/>}<label htmlFor="profile-photo-input"><Camera size={15}/> Alterar foto</label><input id="profile-photo-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>{const f=e.target.files?.[0]||null;if(f&&(f.size>5*1024*1024||!["image/jpeg","image/png","image/webp"].includes(f.type))){setError(f.size>5*1024*1024?"A foto deve ter até 5 MB.":"Use JPEG, PNG ou WEBP.");e.target.value="";return;}setError("");setPhoto(f);if(f)setPreview(URL.createObjectURL(f));}}/></div><label>Nome de usuário<input className="dark-input" value={data.username} disabled/></label><label>Nome de exibição<input className="dark-input" value={data.nome_exibicao} maxLength={80} onChange={e=>setData(v=>({...v,nome_exibicao:e.target.value}))} placeholder="Como deseja aparecer para a torcida"/></label><label>Biografia<textarea className="dark-input" rows={4} value={data.biografia} maxLength={300} onChange={e=>setData(v=>({...v,biografia:e.target.value}))} placeholder="Conte um pouco sobre você"/></label><small>Imagem de até 5 MB. Formatos aceitos: JPEG, PNG e WEBP.</small><button className="primary-btn" disabled={busy}>{busy?<RefreshCw size={15}/>:<Save size={15}/>} {busy?"Salvando...":"Salvar perfil"}</button></form>}</section>;
}
