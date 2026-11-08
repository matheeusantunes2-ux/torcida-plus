from django.conf import settings
from django.db import models


class Publicacao(models.Model):
    torcida = models.ForeignKey(
        "torcidas.Torcida",
        on_delete=models.CASCADE,
        related_name="publicacoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="publicacoes_torcida",
    )
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Aguardando aprovação"
        APROVADA = "aprovada", "Aprovada"
        REJEITADA = "rejeitada", "Rejeitada"

    texto = models.TextField(max_length=5000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    imagem = models.ImageField(
        upload_to="publicacoes/",
        blank=True,
        null=True,
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criada_em"]

    def __str__(self):
        return f"Publicação {self.pk} - torcida {self.torcida_id}"


class Comentario(models.Model):
    publicacao = models.ForeignKey(
        Publicacao,
        on_delete=models.CASCADE,
        related_name="comentarios",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comentarios_torcida",
    )
    texto = models.TextField(max_length=2000)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["criado_em"]

    def __str__(self):
        return f"Comentário {self.pk} - publicação {self.publicacao_id}"


class Curtida(models.Model):
    publicacao = models.ForeignKey(
        Publicacao,
        on_delete=models.CASCADE,
        related_name="curtidas",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="curtidas_torcida",
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["publicacao", "usuario"],
                name="unica_curtida_por_usuario_publicacao",
            )
        ]

    def __str__(self):
        return f"Usuário {self.usuario_id} curtiu publicação {self.publicacao_id}"


class Notificacao(models.Model):
    class Tipo(models.TextChoices):
        CURTIDA = "curtida", "Curtida"
        COMENTARIO = "comentario", "Comentário"
        MENSAGEM = "mensagem", "Mensagem"
        CONVITE = "convite", "Convite"

    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificacoes_torcida")
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notificacoes_enviadas_torcida")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    texto = models.CharField(max_length=240)
    referencia = models.CharField(max_length=160, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em"]
        indexes = [models.Index(fields=["destinatario", "lida_em", "-criada_em"], name="notif_user_read_date_idx")]
