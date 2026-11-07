# Configuração do Mercado Pago no TORCIDA+

A loja usa o Checkout Pro: o TORCIDA+ cria o pedido e uma preferência de pagamento no backend; o comprador é enviado ao ambiente hospedado pelo Mercado Pago. O cartão, Pix ou boleto é processado pelo provedor. O TORCIDA+ nunca recebe nem armazena número de cartão ou CVV.

## Variáveis de ambiente

Configure estas variáveis no serviço de backend (por exemplo, Render → Environment). Não coloque credenciais no frontend, no APK, no Git ou em mensagens:

- `MERCADO_PAGO_ACCESS_TOKEN`: Access Token da aplicação Mercado Pago. Comece com credenciais de teste.
- `MERCADO_PAGO_WEBHOOK_SECRET`: chave secreta gerada na configuração de Webhooks da aplicação.
- `MERCADO_PAGO_WEBHOOK_URL`: URL HTTPS pública do endpoint `https://SEU-DOMINIO-API/api/loja/pagamentos/webhook/`.
- `TORCIDA_FRONTEND_URL`: URL pública do app web que recebe o retorno do checkout.

Um modelo sem credenciais reais está em `backend/.env.mercadopago.example`.

## Configuração no painel Mercado Pago

1. Crie uma aplicação em Suas integrações.
2. Copie o Access Token de teste para `MERCADO_PAGO_ACCESS_TOKEN`.
3. Em Webhooks, cadastre a URL HTTPS acima e habilite o evento Pagamentos.
4. Copie a chave secreta do Webhook para `MERCADO_PAGO_WEBHOOK_SECRET`.
5. Configure as quatro variáveis no backend e reinicie o serviço.
6. Faça compras de teste e valide os retornos aprovado, pendente e recusado antes de ativar credenciais de produção.

## Endpoints

- `POST /api/loja/pedidos/<id>/pagar/` — recebe `{"metodo_pagamento":"pix"}`, `cartao` ou `boleto` e retorna `checkout_url`.
- `POST /api/loja/pagamentos/webhook/` — recebe notificações do Mercado Pago, valida a assinatura HMAC e consulta o pagamento diretamente na API antes de atualizar o pedido.

O status do pedido só muda para **pago** depois da confirmação consultada no Mercado Pago. O retorno do navegador não é usado como prova de pagamento.

## Observações

- O comprador precisa ter um e-mail válido no cadastro.
- Pix, cartão e boleto são apresentados conforme o meio selecionado e a disponibilidade habilitada na conta Mercado Pago.
- O endereço de retorno precisa ser público; localhost não serve para homologação do Checkout Pro.
- Não use credenciais de produção até concluir testes de ponta a ponta.
