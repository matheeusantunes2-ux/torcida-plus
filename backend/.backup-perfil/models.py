from django.conf import settings
from django.db import models


class Perfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    nome_exibicao = models.CharField(
        max_length=80,
        blank=True,
    )
    biografia = models.CharField(
        max_length=300,
        blank=True,
    )
    foto = models.ImageField(
        upload_to="perfis/",
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return self.nome_exibicao or self.usuario.username
