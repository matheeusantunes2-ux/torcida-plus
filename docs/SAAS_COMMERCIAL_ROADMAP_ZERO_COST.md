# TORCIDA+ — Plano de evolução comercial SaaS (sem novos custos)

## Regra financeira inegociável
Nenhuma etapa deste plano autoriza contratar plano pago, upgrade, serviço adicional, domínio, CDN, banco gerenciado, worker, cron ou plugin. Reutilizar GitHub, Render e serviços já configurados; manter recursos dentro da cota gratuita disponível. Antes de ativar qualquer integração, confirmar que não gera cobrança. Se um recurso gratuito atingir limite, pausar e documentar a limitação — não habilitar cobrança automática.

## Estado desta entrega
- Landing comercial responsiva adicionada ao frontend React.
- CTAs B2C e B2B presentes; B2C direciona ao formulário de cadastro/login existente; B2B direciona à seção explicativa para diretorias.
- Conteúdo sem números de prova social inventados.
- Design utiliza CSS e ícones já existentes; fontes locais do sistema, sem dependência de CDN.
- Não foram criados novos serviços, bancos ou integrações pagas.
- Não foram implementados nesta entrega: associação paga, planos recorrentes, carteira/QR dinâmico, bilheteria, PDV, ledger, conciliação ou isolamento SaaS completo.
- Esta mudança está na branch desenvolvimento-seguro; deploy e build ainda precisam ser confirmados pelo CI e pelo ambiente hospedado.

## Arquitetura alvo
Manter Django/DRF como API transacional e React/Vite/Capacitor como cliente Web/Android. Evoluir em módulos pequenos e reversíveis. O tenant deve ser resolvido pelo backend a partir do usuário autenticado e da organização associada; nunca confiar em tenant_id recebido do navegador.

### Módulos de domínio
1. SaaS: Tenant, TenantDomain, TenantSettings, TenantSubscription (somente quando modelo comercial for aprovado).
2. Associados: Membership, MembershipPlan, MembershipPayment, ConsentRecord.
3. Carteira: DigitalCredential, CredentialRevocation.
4. Eventos: Event, TicketType, Ticket, TicketScan.
5. Comércio: ProductVariant, StockLocation, StockMovement, Cart, Order.
6. PDV: PosSession, PosSale, PosSaleItem, CashMovement.
7. Financeiro: LedgerEntry imutável, CommissionRule, CommissionEntry, Reconciliation.
8. Segurança: AuditLog, DataSubjectRequest, SecurityEvent.

Antes de criar models, mapear modelos atuais e migrar dados com backup. O app atual já possui contas, torcidas, comunidade, chat, loja e eventos; evitar duplicar conceitos existentes.

## Priorização
### P0 — Aquisição
- Landing pública (entregue nesta branch).
- Página pública por torcida com identidade, informações e eventos.
- Instrumentação do funil sem PII: visualização, clique CTA, início de cadastro, cadastro concluído.
- Conteúdo e prova social somente com métricas reais e depoimentos autorizados.

### P1 — Associação
- Planos e benefícios, cadastro mínimo, validação de contato.
- Pagamento via provedor existente, se suportado sem custo adicional fixo.
- Confirmar adesão somente por webhook assinado ou consulta server-to-server.
- Carteirinha com QR opaco, assinado, de curta validade, revogável e sem CPF/nome no payload.

### P2 — E-commerce / PDV
- Variantes/SKU, disponibilidade e preço.
- Checkout idempotente e webhooks autenticados.
- Reserva temporária de estoque e reconciliação antes de devolução.
- PDV e e-commerce usando o mesmo serviço transacional de estoque.
- Nunca armazenar PAN/CVV; usar checkout/tokenização do PSP.

### P3 — Eventos / bilheteria
- Lotes, limites, emissão e validação de ingressos.
- Resgate atômico com proteção contra dupla entrada.
- Modo offline somente se houver desenho de risco, sincronização e trilha de auditoria.

### P4 — Gestão / finanças
- Dashboards com filtros por período e tenant.
- Ledger append-only; estornos por lançamentos compensatórios.
- Separar bruto, descontos, taxas, comissões, reembolsos e líquido.
- Caixa e fechamento por operador, sem apagar movimentações.

## Segurança e LGPD — gates obrigatórios
- Confirmar PostgreSQL persistente, backups e restauração testada; SQLite não deve ser banco de produção para SaaS multiusuário.
- Isolamento de tenant validado no backend em todas as listas, detalhes, exports, mutations e WebSockets.
- RBAC por tenant; ocultar botões não substitui autorização server-side.
- MFA para administradores; rotação/revogação de refresh tokens e rate limiting.
- TLS em trânsito; criptografia em repouso pelo armazenamento; campos de alto risco com envelope encryption somente se houver gestão segura de chaves gratuita/viável. Nunca versionar chaves.
- Não anunciar E2EE em chat/chamadas até implementar protocolo adequado e auditoria independente.
- Inventário de dados pessoais, finalidade/base legal, minimização, retenção, canal do titular, exportação/correção/eliminação quando aplicável, contratos com operadores e plano de incidente.
- Auditoria de alterações administrativas, financeiras, exportações e acessos sensíveis.

## Critérios de aceite
1. Testes negativos cross-tenant em todas as rotas.
2. Webhooks repetidos/tardios não duplicam cobrança, comissão, estoque ou ticket.
3. QR de ingresso não pode ser reutilizado.
4. Estoque nunca fica negativo em concorrência.
5. Painel concilia com ledger e PSP.
6. Fluxos mobile acessíveis e utilizáveis em rede lenta.
7. Backups restaurados em ambiente de teste.
8. Nenhum número, selo de segurança ou avaliação sem fonte verificável.
9. Nenhuma etapa cria cobrança, serviço pago ou upgrade automático.

## Estratégia de liberação
- Trabalhar na branch desenvolvimento-seguro.
- Executar CI frontend/backend/Android após cada conjunto coerente.
- Abrir PR para main após revisão e testes; não publicar diretamente em produção sem gates.
- Piloto controlado com uma torcida, monitorando erros e suporte.
- APK debug não é release comercial; release Android precisa assinatura e gestão segura de chave sem colocá-la no Git.
