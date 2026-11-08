from django.conf import settings
from django.db import models


class Conversa(models.Model):
    class Tipo(models.TextChoices):
        PRIVADA = "privada", "Privada"
        GRUPO = "grupo", "Grupo"

    torcida = models.ForeignKey("torcidas.Torcida", on_delete=models.CASCADE, related_name="conversas")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    nome = models.CharField(max_length=120, blank=True)
    criada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="conversas_criadas")
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizada_em", "-id"]

    def __str__(self):
        return f"Conversa {self.pk} ({self.tipo})"


class ParticipanteConversa(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="participantes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="participacoes_chat")
    entrou_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["conversa", "usuario"], name="chat_participante_unico")]


class Mensagem(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mensagens_chat")
    conteudo = models.TextField(max_length=4000)
    criada_em = models.DateTimeField(auto_now_add=True)
    editada_em = models.DateTimeField(null=True, blank=True)
    apagada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em", "-id"]

    def __str__(self):
        return f"Mensagem {self.pk} - conversa {self.conversa_id}"


class AnexoMensagem(models.Model):
    class Tipo(models.TextChoices):
        IMAGEM = "imagem", "Imagem"
        VIDEO = "video", "Vídeo"

    mensagem = models.ForeignKey(Mensagem, on_delete=models.CASCADE, related_name="anexos")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    cloudinary_public_id = models.CharField(max_length=255, unique=True)
    cloudinary_resource_type = models.CharField(max_length=10, choices=[("image", "Imagem"), ("video", "Vídeo")])
    formato = models.CharField(max_length=20)
    nome_original = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    tamanho = models.PositiveBigIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Anexo {self.pk} - mensagem {self.mensagem_id}"


class LeituraMensagem(models.Model):
    mensagem = models.ForeignKey(Mensagem, on_delete=models.CASCADE, related_name="leituras")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leituras_chat")
    lida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["mensagem", "usuario"], name="chat_leitura_unica")]
