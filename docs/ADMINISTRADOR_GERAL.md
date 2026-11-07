# Administrador geral do TORCIDA+

A conta de administrador geral é uma conta Django `is_staff=True` e
`is_superuser=True`. Ela deve ser criada diretamente no ambiente que contém
o banco de dados de produção, nunca em uma base local de desenvolvimento.

## Criar a conta

1. Faça deploy do código atualizado.
2. Abra um shell/console autenticado do serviço backend no Render.
3. Execute:

```bash
python manage.py migrate
python manage.py create_platform_admin
```

4. Quando solicitado, informe `admin-loja` como usuário (ou escolha outro) e
   digite uma senha forte. A senha não aparece na tela e não deve ser enviada
   por chat, commit, variável pública ou arquivo versionado.
5. Acesse o painel administrativo Django em `/admin/` usando HTTPS.

## Segurança

- O comando não exige e-mail e não cria senha padrão.
- O comando interrompe a operação se o username já existir; não promove nem
  altera uma conta preexistente.
- O acesso geral ao painel Django é concedido por `is_staff` e
  `is_superuser`. As permissões específicas das APIs continuam sujeitas às
  regras de cada módulo; a conta não deve ser considerada testada em todos os
  fluxos do aplicativo até que os testes de autorização sejam concluídos.
- Restrinja o acesso ao painel administrativo, use senha exclusiva e forte,
  HTTPS e autenticação adicional no provedor quando disponível.
- Não habilite cadastro público como superusuário.
