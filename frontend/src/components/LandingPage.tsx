import {ArrowRight, ShieldCheck, ShoppingBag, Ticket, Users, Zap, Menu, X, CheckCircle2, Smartphone, BarChart3} from "lucide-react";
import {useState} from "react";
import "./LandingPage.css";

type Props={onJoin:()=>void;onBusiness:()=>void;onLogin:()=>void};
export default function LandingPage({onJoin,onBusiness,onLogin}:Props){
 const [menu,setMenu]=useState(false);
 return <main className="marketing">
  <header className="marketing-header">
   <a className="marketing-brand" href="#" aria-label="TORCIDA+ início"><span className="brand-mark">T+</span><span>TORCIDA<span className="brand-plus">+</span><small>PAIXÃO QUE ORGANIZA</small></span></a>
   <nav className={menu?"marketing-nav is-open":"marketing-nav"}><a href="#recursos" onClick={()=>setMenu(false)}>Plataforma</a><a href="#torcedor" onClick={()=>setMenu(false)}>Para o torcedor</a><a href="#diretoria" onClick={()=>setMenu(false)}>Para diretorias</a><a href="#seguranca" onClick={()=>setMenu(false)}>Segurança</a></nav>
   <div className="marketing-actions"><button className="marketing-login" onClick={onLogin}>Entrar</button><button className="marketing-cta small" onClick={onBusiness}>Sou diretoria <ArrowRight size={16}/></button></div>
   <button className="marketing-menu" aria-label="Abrir menu" onClick={()=>setMenu(v=>!v)}>{menu?<X/>:<Menu/>}</button>
  </header>
  <section className="marketing-hero">
   <div className="hero-copy"><span className="marketing-eyebrow"><span/> A NOVA CENTRAL DA SUA TORCIDA</span>
    <h1>A paixão é gigante.<br/><em>A gestão também.</em></h1>
    <p>Comunidade, associados, produtos oficiais e eventos em um só lugar. Mais conexão para o torcedor. Mais organização e oportunidades para a diretoria.</p>
    <div className="hero-actions"><button className="marketing-cta" onClick={onJoin}>Tornar-se sócio <ArrowRight/></button><button className="marketing-secondary" onClick={onBusiness}>Levar para minha torcida <Users/></button></div>
    <div className="hero-trust"><span><ShieldCheck/> Acesso protegido</span><span><Smartphone/> Feito para celular</span><span><Zap/> Tudo conectado</span></div>
   </div>
   <div className="hero-visual" aria-label="Prévia ilustrativa da plataforma">
    <div className="visual-glow"/><div className="device-frame"><div className="device-top"><span>9:41</span><span>● ● ●</span></div><div className="device-brand"><b>T+</b><span>TORCIDA<span>+</span></span><i>●</i></div>
     <div className="device-banner"><small>JUNTOS SOMOS MAIS FORTES</small><strong>A arquibancada<br/>é aqui.</strong><span>Comunidade • Loja • Eventos</span></div>
     <div className="device-stats"><div><b>01</b><small>Sua torcida</small></div><div><b>∞</b><small>Possibilidades</small></div></div>
     <div className="device-section-title">Explore a plataforma <span>VER TUDO</span></div><div className="device-tiles"><div><Users/><b>Comunidade</b></div><div><ShoppingBag/><b>Loja oficial</b></div><div><Ticket/><b>Eventos</b></div></div>
     <div className="device-bottom"><span>⌂<small>Início</small></span><span>▣<small>Loja</small></span><span>◉<small>Eventos</small></span><span>◎<small>Carteira</small></span></div>
    </div><div className="floating-card card-one"><span className="floating-icon"><CheckCircle2/></span><span><b>Uma plataforma</b><small>Experiência integrada</small></span></div><div className="floating-card card-two"><span className="floating-icon"><ShieldCheck/></span><span><b>Gestão organizada</b><small>Permissões por função</small></span></div>
   </div>
  </section>
  <section className="marketing-proof" aria-label="Benefícios da plataforma"><div><b>01</b><span>Uma comunidade<br/>mais conectada</span></div><div><b>02</b><span>Operação em um<br/>só ambiente</span></div><div><b>03</b><span>Experiência mobile<br/>em primeiro lugar</span></div><div><b>04</b><span>Ferramentas para<br/>crescer com controle</span></div></section>
  <section className="marketing-section" id="recursos"><div className="section-heading"><span className="marketing-eyebrow">UM ECOSSISTEMA COMPLETO</span><h2>Tudo que move a torcida.<br/><em>Em um só lugar.</em></h2><p>Ferramentas conectadas para aproximar pessoas e simplificar a operação.</p></div>
   <div className="feature-grid"><article><span><Users/></span><h3>Comunidade</h3><p>Feed, publicações, conversas e notificações para manter todo mundo por dentro.</p></article><article><span><ShoppingBag/></span><h3>Loja oficial</h3><p>Vitrine de produtos, pedidos e estoque conectado à operação comercial.</p></article><article><span><Ticket/></span><h3>Eventos e ingressos</h3><p>Divulgação, venda e organização de eventos da torcida.</p></article><article><span><BarChart3/></span><h3>Gestão e resultados</h3><p>Visibilidade para acompanhar atividades, vendas e operação da organização.</p></article></div>
  </section>
  <section className="audience-section" id="torcedor"><div className="audience-panel fan-panel"><span className="marketing-eyebrow">PARA QUEM VIVE A TORCIDA</span><h2>Mais perto.<br/><em>Mais participação.</em></h2><p>Acompanhe novidades, participe da comunidade, descubra produtos e encontre os próximos eventos.</p><ul><li><CheckCircle2/> Conteúdo e comunicados em um só feed</li><li><CheckCircle2/> Loja e novidades da torcida</li><li><CheckCircle2/> Eventos e informações importantes</li></ul><button className="marketing-cta" onClick={onJoin}>Quero participar <ArrowRight/></button></div>
   <div className="audience-panel leader-panel" id="diretoria"><span className="marketing-eyebrow">PARA QUEM FAZ ACONTECER</span><h2>Mais controle.<br/><em>Mais possibilidades.</em></h2><p>Centralize processos, organize equipes e construa uma operação mais profissional para sua torcida.</p><ul><li><CheckCircle2/> Administração e permissões</li><li><CheckCircle2/> Loja, pedidos e estoque</li><li><CheckCircle2/> Eventos e visão operacional</li></ul><button className="marketing-secondary light" onClick={onBusiness}>Levar para minha torcida <ArrowRight/></button></div>
  </section>
  <section className="security-section" id="seguranca"><div><span className="marketing-eyebrow">CONFIANÇA EM CADA ETAPA</span><h2>Uma experiência conectada.<br/><em>Com responsabilidade.</em></h2><p>O TORCIDA+ evolui com controle de acesso, proteção das sessões e atenção à privacidade. Recursos e status de segurança são apresentados com transparência.</p></div><div className="security-points"><div><ShieldCheck/><span><b>Controle de acesso</b><small>Permissões aplicadas no servidor.</small></span></div><div><Zap/><span><b>Pagamentos verificados</b><small>Confirmação por integração segura, quando disponível.</small></span></div><div><Users/><span><b>Privacidade</b><small>Dados tratados conforme finalidade e regras aplicáveis.</small></span></div></div></section>
  <section className="marketing-final"><span className="marketing-eyebrow">A PRÓXIMA FASE COMEÇA AGORA</span><h2>Sua torcida merece<br/><em>uma estrutura à altura.</em></h2><p>Entre para a comunidade ou apresente a plataforma à sua diretoria.</p><div className="hero-actions"><button className="marketing-cta" onClick={onJoin}>Tornar-se sócio <ArrowRight/></button><button className="marketing-secondary" onClick={onBusiness}>Levar para minha torcida <Users/></button></div></section>
  <footer className="marketing-footer"><a className="marketing-brand" href="#"><span className="brand-mark">T+</span><span>TORCIDA<span className="brand-plus">+</span><small>PAIXÃO QUE ORGANIZA</small></span></a><span>© {new Date().getFullYear()} TORCIDA+. Todos os direitos reservados.</span><button onClick={onLogin}>Acessar plataforma</button></footer>
 </main>;
}
