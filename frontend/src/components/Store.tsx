import { useEffect, useState, FormEvent } from "react";
import { ShoppingBag, Plus, Pencil, Trash2, RefreshCw, ShoppingCart, Package, CreditCard, QrCode, Receipt, CheckCircle2, ArrowRight } from "lucide-react";

type Props = { tokens: { access: string; refresh: string }; onTokens: (v: { access: string; refresh: string }) => void };
type Team = { id: number; nome: string };
type Product = { id: number; torcida: number; nome: string; descricao: string; categoria: string; preco: string; quantidade: number; imagem_url: string | null };
type Cart = { id: number; produto: Product; quantidade: number };
type Order = { id: number; status: string; total: string; criado_em: string; metodo_pagamento?: string; status_pagamento?: string; checkout_url?: string; itens: { id: number; nome_produto: string; quantidade: number }[] };
const API = import.meta.env.VITE_API_URL || "";
const brl = (n: string | number) => Number(n).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export default function Store({ tokens, onTokens }: Props) {
 const [teams, setTeams] = useState<Team[]>([]);
 const [team, setTeam] = useState(localStorage.getItem("torcida_loja_id") || "");
 const [products, setProducts] = useState<Product[]>([]), [cart, setCart] = useState<Cart[]>([]), [orders, setOrders] = useState<Order[]>([]);
 const [tab, setTab] = useState("Catálogo"), [loading, setLoading] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
 const [edit, setEdit] = useState<Product | null>(null), [form, setForm] = useState({ nome: "", descricao: "", categoria: "Vestuário", preco: "", quantidade: "0" }), [photo, setPhoto] = useState<File | null>(null);
 const [finalOrder, setFinalOrder] = useState<Order | null>(null), [paymentMethod, setPaymentMethod] = useState("pix");
 const [delivery, setDelivery] = useState({ nome_destinatario: "", telefone: "", cep: "", endereco: "", numero: "", complemento: "", bairro: "", cidade: "", uf: "", observacoes: "" });

 async function api(path: string, options: RequestInit = {}) {
  let token = tokens.access;
  const send = () => fetch(API + path, { ...options, headers: { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), Authorization: "Bearer " + token, ...options.headers } });
  let r = await send();
  if (r.status === 401 && tokens.refresh) {
   const x = await fetch(API + "/api/auth/refresh/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: tokens.refresh }) });
   if (x.ok) { const d = await x.json(); token = d.access; onTokens({ access: d.access, refresh: d.refresh || tokens.refresh }); r = await send(); }
  }
  if (!r.ok) { const d = await r.json().catch(() => ({})); throw Error(d.detail || Object.values(d).flat().join(" ") || "Não foi possível concluir a operação."); }
  return r.status === 204 ? null : r.json();
 }

 async function loadFor(id: string, seedIfEmpty = true) {
  if (!/^\d+$/.test(id)) return;
  setLoading(true); setError("");
  try {
   localStorage.setItem("torcida_loja_id", id);
   let [p, c] = await Promise.all([api("/api/loja/produtos/?torcida=" + id), api("/api/loja/carrinho/?torcida=" + id)]);
   let list: Product[] = Array.isArray(p) ? p : p.results || [];
   if (list.length === 0 && seedIfEmpty) {
    try {
     const seeded = await api("/api/loja/catalogo-demo/", { method: "POST", body: JSON.stringify({ torcida: Number(id) }) });
     setMessage(seeded.detail || "Catálogo de demonstração preparado.");
     p = await api("/api/loja/produtos/?torcida=" + id);
     list = Array.isArray(p) ? p : p.results || [];
    } catch (seedError) {
     setError(seedError instanceof Error ? seedError.message : "Não foi possível preparar os produtos. Verifique se você é administrador ou moderador desta torcida.");
    }
   }
   setProducts(list); setCart(Array.isArray(c) ? c : c.results || []);
  } catch (e) { setError(e instanceof Error ? e.message : "Erro ao carregar a loja."); }
  finally { setLoading(false); }
 }
 async function load() { await loadFor(team, false); }

 useEffect(() => {
  let active = true;
  (async () => {
   try {
    const data = await api("/api/torcidas/");
    const list: Team[] = Array.isArray(data) ? data : data.results || [];
    if (!active) return;
    setTeams(list);
    if (list.length === 0) { setError("Você ainda não participa de nenhuma torcida. Entre ou crie uma torcida para acessar a loja."); return; }
    const saved = list.find(t => String(t.id) === localStorage.getItem("torcida_loja_id"));
    const selected = saved || list[0];
    setTeam(String(selected.id));
    await loadFor(String(selected.id), true);
    const params = new URLSearchParams(window.location.search);
    const returnedOrderId = params.get("order_id");
    if (params.has("store_payment") && returnedOrderId) {
     const od = await api("/api/loja/pedidos/?torcida=" + selected.id);
     const listOrders: Order[] = Array.isArray(od) ? od : od.results || [];
     const returnedOrder = listOrders.find(o => String(o.id) === returnedOrderId) || null;
     setFinalOrder(returnedOrder);
     if (returnedOrder?.metodo_pagamento) setPaymentMethod(returnedOrder.metodo_pagamento);
     setTab("Finalização");
     window.history.replaceState({}, "", window.location.pathname);
    }
   } catch (e) { if (active) setError(e instanceof Error ? e.message : "Não foi possível localizar suas torcidas."); }
  })();
  return () => { active = false; };
 }, []);

 async function seedDemo() {
  if (!/^\d+$/.test(team)) { setError("Selecione uma torcida."); return; }
  setBusy(true); setError("");
  try { const d = await api("/api/loja/catalogo-demo/", { method: "POST", body: JSON.stringify({ torcida: Number(team) }) }); setMessage(d.detail || "Catálogo demonstrativo carregado."); await loadFor(team, false); }
  catch (e) { setError(e instanceof Error ? e.message : "Não foi possível carregar o catálogo."); }
  finally { setBusy(false); }
 }
 async function loadOrders() {
  try { const d = await api("/api/loja/pedidos/?torcida=" + team); const list: Order[] = Array.isArray(d) ? d : d.results || []; setOrders(list); return list; }
  catch (e) { setError(e instanceof Error ? e.message : "Erro ao carregar pedidos."); return []; }
 }
 async function beginPayment(orderId: number) {
  setBusy(true); setError("");
  try {
   const result = await api("/api/loja/pedidos/" + orderId + "/pagar/", { method: "POST", body: JSON.stringify({ metodo_pagamento: paymentMethod }) });
   if (result.pedido) setFinalOrder(result.pedido);
   if (!result.checkout_url) throw new Error("O provedor não retornou o endereço de pagamento.");
   window.location.assign(result.checkout_url);
  } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível iniciar o pagamento."); }
  finally { setBusy(false); }
 }
 async function refreshFinalOrder() {
  const list = await loadOrders();
  if (finalOrder) setFinalOrder(list.find(o => o.id === finalOrder.id) || finalOrder);
 }
 async function add(p: Product) {
  try { await api("/api/loja/carrinho/", { method: "POST", body: JSON.stringify({ produto_id: p.id, quantidade: 1 }) }); await load(); setMessage("Produto adicionado ao carrinho."); }
  catch (e) { setError(e instanceof Error ? e.message : "Erro ao adicionar produto."); }
 }
 function start(p?: Product) {
  setEdit(p || null); setForm(p ? { nome: p.nome, descricao: p.descricao, categoria: p.categoria, preco: String(p.preco), quantidade: String(p.quantidade) } : { nome: "", descricao: "", categoria: "Vestuário", preco: "", quantidade: "0" }); setPhoto(null); setTab("Gerenciar");
 }
 async function save(e: FormEvent) {
  e.preventDefault(); setBusy(true); setError("");
  try {
   const body = new FormData(); body.append("torcida", team); Object.entries(form).forEach(([k, v]) => body.append(k, v)); if (photo) body.append("imagem", photo);
   await api(edit ? "/api/loja/produtos/" + edit.id + "/" : "/api/loja/produtos/", { method: edit ? "PATCH" : "POST", body });
   setMessage("Produto salvo."); setEdit(null); setForm({ nome: "", descricao: "", categoria: "Vestuário", preco: "", quantidade: "0" }); await load();
  } catch (e) { setError(e instanceof Error ? e.message : "Erro ao salvar produto."); }
  finally { setBusy(false); }
 }
 async function remove(p: Product) {
  if (!confirm("Desativar " + p.nome + "?")) return;
  try { await api("/api/loja/produtos/" + p.id + "/", { method: "DELETE" }); await load(); }
  catch (e) { setError(e instanceof Error ? e.message : "Erro ao remover produto."); }
 }
 async function checkout(e: FormEvent) {
  e.preventDefault(); setBusy(true); setError("");
  try {
   const created: Order = await api("/api/loja/checkout/", { method: "POST", body: JSON.stringify({ torcida: Number(team), ...delivery }) });
   setFinalOrder(created); setTab("Finalização"); await load(); await loadOrders();
   setBusy(false); await beginPayment(created.id); return;
  } catch (e) { setError(e instanceof Error ? e.message : "Erro ao criar o pedido."); }
  finally { setBusy(false); }
 }
 const total = cart.reduce((s, i) => s + Number(i.produto.preco) * i.quantidade, 0);

 return <div className="store-wrap">
  <header className="store-head"><div><span className="kicker"><ShoppingBag size={14}/> LOJA OFICIAL</span><h2>Produtos da torcida</h2><p>Catálogo, estoque e pedidos em um só lugar.</p></div><button className="outline-btn" onClick={load} disabled={loading}><RefreshCw size={15}/> Atualizar</button></header>
  <div className="store-team"><label htmlFor="store-team-select">Minha torcida</label><select id="store-team-select" className="dark-input" value={team} onChange={e => { setTeam(e.target.value); setProducts([]); setCart([]); loadFor(e.target.value, true); }}><option value="">Selecione sua torcida</option>{teams.map(t => <option key={t.id} value={t.id}>{t.nome} · ID {t.id}</option>)}</select><button className="primary-btn" disabled={loading || !team} onClick={load}>Acessar loja</button><button className="outline-btn" disabled={busy || !/^\d+$/.test(team)} onClick={seedDemo}>Carregar 10 produtos fictícios</button></div>
  <nav className="store-tabs">{["Catálogo", "Carrinho", "Pedidos", "Finalização", "Gerenciar"].map(t => <button key={t} className={tab === t ? "active" : ""} onClick={() => { setTab(t); if (t === "Pedidos") loadOrders(); }}>{t}{t === "Carrinho" && cart.length ? " (" + cart.length + ")" : ""}</button>)}</nav>
  {error && <div className="error">{error}</div>}{message && <div className="notice">{message}<button onClick={() => setMessage("")}>×</button></div>}
  {tab === "Catálogo" && <>{loading ? <p>Carregando produtos...</p> : products.length === 0 ? <div className="store-empty"><Package/><h3>Catálogo vazio</h3><p>Não há produtos cadastrados para esta torcida. Se você for administrador ou moderador, use “Carregar 10 produtos fictícios”.</p></div> : <div className="store-products">{products.map(p => <article className="store-product" key={p.id}><div className="store-product-image">{p.imagem_url ? <img src={p.imagem_url} alt={p.nome}/> : <Package/>}</div><div className="store-product-info"><small>{p.categoria}</small><h3>{p.nome}</h3><p>{p.descricao}</p><strong>{brl(p.preco)}</strong><small>{p.quantidade} em estoque</small><button className="primary-btn" disabled={!p.quantidade} onClick={() => add(p)}><ShoppingCart size={15}/> Adicionar</button></div></article>)}</div>}</>}
  {tab === "Carrinho" && <section className="store-panel"><h3>Seu carrinho</h3>{cart.length === 0 ? <p>Carrinho vazio.</p> : <>{cart.map(i => <div className="store-cart-row" key={i.id}><span><b>{i.produto.nome}</b><small>{i.quantidade} × {brl(i.produto.preco)}</small></span><strong>{brl(Number(i.produto.preco) * i.quantidade)}</strong><button onClick={async () => { await api("/api/loja/carrinho/", { method: "DELETE", body: JSON.stringify({ item_id: i.id }) }); await load(); }}>Remover</button></div>)}<div className="store-total">Total <b>{brl(total)}</b></div><form className="store-delivery" onSubmit={checkout}><h3>Dados para entrega</h3><div className="payment-choice"><h4>Escolha como deseja pagar</h4><label className={paymentMethod === "pix" ? "chosen" : ""}><input type="radio" name="payment-method" value="pix" checked={paymentMethod === "pix"} onChange={()=>setPaymentMethod("pix")}/><QrCode/><span><b>Pix</b><small>Pagamento rápido</small></span></label><label className={paymentMethod === "cartao" ? "chosen" : ""}><input type="radio" name="payment-method" value="cartao" checked={paymentMethod === "cartao"} onChange={()=>setPaymentMethod("cartao")}/><CreditCard/><span><b>Cartão</b><small>Crédito ou débito, conforme disponibilidade</small></span></label><label className={paymentMethod === "boleto" ? "chosen" : ""}><input type="radio" name="payment-method" value="boleto" checked={paymentMethod === "boleto"} onChange={()=>setPaymentMethod("boleto")}/><Receipt/><span><b>Boleto</b><small>Pagamento bancário</small></span></label></div>{(["nome_destinatario", "telefone", "cep", "endereco", "numero", "complemento", "bairro", "cidade", "uf", "observacoes"] as const).map(k => <label key={k}>{k.replace(/_/g, " ")}<input className="dark-input" required={!["complemento", "observacoes"].includes(k)} value={delivery[k]} onChange={e => setDelivery(v => ({ ...v, [k]: e.target.value }))}/></label>)}<button className="primary-btn" disabled={busy}>{busy ? "Preparando checkout..." : "Revisar e pagar"}</button><small>Você será direcionado ao ambiente seguro do Mercado Pago para concluir a cobrança.</small></form></>}</section>}
  {tab === "Finalização" && <section className="store-panel store-finish"><div className="finish-icon"><CheckCircle2/></div><span className="kicker">COMPRA REGISTRADA</span><h2>Finalização do pedido</h2>{finalOrder ? <><p>Pedido <b>#{finalOrder.id}</b> · {new Date(finalOrder.criado_em).toLocaleString("pt-BR")}</p><div className="finish-summary">{finalOrder.itens?.map(i=><div key={i.id}><span>{i.quantidade} × {i.nome_produto}</span></div>)}<div className="finish-total"><span>Total</span><strong>{brl(finalOrder.total)}</strong></div></div><div className="finish-status"><span>Pagamento</span><b>{({approved:"Aprovado",pending:"Aguardando pagamento",in_process:"Em análise",rejected:"Recusado",refunded:"Estornado",cancelled:"Cancelado",nao_iniciado:"Não iniciado"} as Record<string,string>)[finalOrder.status_pagamento || "nao_iniciado"] || finalOrder.status_pagamento}</b><small>Status do pedido: {finalOrder.status}</small></div><p className="finish-help">O pagamento é processado no ambiente seguro do Mercado Pago. Após pagar, volte ao TORCIDA+ e atualize a situação.</p><div className="finish-actions"><button className="primary-btn" onClick={()=>beginPayment(finalOrder.id)} disabled={busy}><ArrowRight/> {busy ? "Abrindo pagamento..." : "Continuar para pagamento"}</button><button className="outline-btn" onClick={refreshFinalOrder}><RefreshCw/> Atualizar pagamento</button><button className="outline-btn" onClick={()=>setTab("Pedidos")}>Ver meus pedidos</button></div></> : <p>Não foi possível localizar os dados deste pedido. Consulte a aba Pedidos.</p>}</section>}
  {tab === "Pedidos" && <section className="store-panel"><h3>Meus pedidos</h3>{orders.length === 0 ? <p>Nenhum pedido.</p> : orders.map(o => <article className="store-order" key={o.id}><b>Pedido #{o.id}</b><span>{o.status}</span><strong>{brl(o.total)}</strong><small>{new Date(o.criado_em).toLocaleString("pt-BR")}</small><ul>{o.itens.map(i => <li key={i.id}>{i.quantidade} × {i.nome_produto}</li>)}</ul></article>)}</section>}
  {tab === "Gerenciar" && <section className="store-panel"><div className="store-manage-head"><h3>Gerenciar produtos</h3><button className="primary-btn" onClick={() => start()}><Plus size={15}/> Novo produto</button></div><p>Disponível somente para administradores e moderadores.</p><form className="store-edit-form" onSubmit={save}><h3>{edit ? "Editar produto" : "Cadastro de produto"}</h3>{(["nome", "descricao", "categoria", "preco", "quantidade"] as const).map(k => <label key={k}>{({ nome: "Nome", descricao: "Descrição", categoria: "Categoria", preco: "Preço (R$)", quantidade: "Quantidade" } as Record<string, string>)[k]}<input className="dark-input" required type={k === "preco" || k === "quantidade" ? "number" : "text"} min={k === "preco" ? "0.01" : k === "quantidade" ? "0" : undefined} step={k === "preco" ? "0.01" : undefined} value={form[k]} onChange={e => setForm(v => ({ ...v, [k]: e.target.value }))}/></label>)}<label>Imagem<input type="file" accept="image/*" onChange={e => setPhoto(e.target.files?.[0] || null)}/></label><button className="primary-btn" disabled={busy}>{busy ? "Salvando..." : "Salvar produto"}</button></form><div className="store-manage-list">{products.map(p => <div key={p.id}><span><b>{p.nome}</b><small>{p.quantidade} em estoque · {brl(p.preco)}</small></span><button onClick={() => start(p)}><Pencil size={16}/></button><button onClick={() => remove(p)}><Trash2 size={16}/></button></div>)}</div></section>}
 </div>;
}
