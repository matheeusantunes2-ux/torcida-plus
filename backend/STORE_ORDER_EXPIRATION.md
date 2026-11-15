# Expiração e conciliação de pedidos da loja

O checkout reserva o estoque por 30 minutos (`expira_em`). O backend bloqueia a abertura de um novo checkout após esse prazo.

## Agendamento obrigatório no Render

Crie um serviço **Cron Job** no mesmo ambiente do backend, usando o mesmo repositório, branch e variáveis de ambiente do serviço web:

- **Branch:** `desenvolvimento-seguro`
- **Root Directory:** `backend`
- **Build Command:** igual ao serviço backend (instalar `requirements.txt`)
- **Command:** `python manage.py expirar_pedidos`
- **Schedule:** `*/5 * * * *` (a cada 5 minutos)

O Cron Job precisa receber as mesmas variáveis de banco de dados e Mercado Pago, principalmente `DATABASE_URL`, `MERCADO_PAGO_ACCESS_TOKEN` e demais configurações necessárias para inicializar o Django. Não configure um banco separado.

## Regras de segurança

- Pedidos vencidos sem pagamento iniciado são cancelados e o estoque é devolvido.
- Para pedidos com pagamento pendente, o job consulta o Mercado Pago antes de liberar o estoque.
- Se o provedor confirmar aprovação, o pedido é marcado como pago.
- Se houver pagamento ainda pendente ou a consulta falhar, a reserva é mantida para evitar vender a mesma unidade duas vezes.
- Se o provedor não encontrar pagamento ou todas as tentativas estiverem canceladas/recusadas, o pedido é cancelado e o estoque é devolvido.
- A rotina é idempotente: pedidos já cancelados/devolvidos não recebem uma segunda devolução.

## Monitoramento

O comando imprime um resumo com pedidos cancelados, pagamentos confirmados, pagamentos ainda pendentes e falhas de consulta. Verifique os logs do Cron Job no Render após a primeira execução.

**Importante:** o código e os testes não criam automaticamente o serviço Cron no Render. O agendamento precisa ser criado no painel e validado em produção.
