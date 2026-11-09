# TORCIDA+ 2.0.0

## Escopo desta atualização

- Compartilhamento real de publicações pelo menu nativo do aparelho, com cópia do link como alternativa.
- Links compartilháveis apontam diretamente para a publicação no feed.
- Validação no cliente de tipo e tamanho das imagens antes do envio (JPEG, PNG ou WEBP; limite de 5 MB).
- Identificação de versão 2.0.0 na aplicação e metadados atualizados.
- Preservação dos módulos existentes de autenticação, feed, chat, chamadas LiveKit, notificações, comunidades, moderação e loja.

## Observações operacionais

- O APK Android é empacotado a partir de `frontend/` com Capacitor pelo workflow `Android APK`.
- Chamadas de voz/vídeo dependem das credenciais LiveKit configuradas no servidor.
- Eventos e algumas telas ainda são módulos em desenvolvimento; esta versão não os declara como concluídos.
- A segurança de chamadas não deve ser descrita como criptografia ponta a ponta: a interface informa que E2EE ainda não está habilitada.
- A validação de upload no cliente melhora a experiência, mas o servidor continua responsável por validar os arquivos.

## Verificação

O build TypeScript/Vite e a geração do APK devem ser validados pelo GitHub Actions após o push.
