from django.conf import settings
from django.db import models


class Torcida(models.Model):
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    escudo_url = models.URLField(blank=True)
    cor_principal = models.CharField(max_length=7, default="#202020")
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Membro(models.Model):
    class Papel(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MODERADOR = "moderador", "Moderador"
        MEMBRO = "membro", "Membro"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vinculos_torcidas",
    )
    torcida = models.ForeignKey(
        Torcida,
        on_delete=models.CASCADE,
        related_name="membros",
    )
    papel = models.CharField(
        max_length=12,
        choices=Papel.choices,
        default=Papel.MEMBRO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "torcida"],
                name="membro_unico_por_torcida",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.torcida}"
