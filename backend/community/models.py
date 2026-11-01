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
    texto = models.TextField(max_length=5000)
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
