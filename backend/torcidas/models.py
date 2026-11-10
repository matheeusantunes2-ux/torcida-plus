from django.conf import settings
from django.db import models
from django.utils import timezone


class Torcida(models.Model):
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    escudo_url = models.URLField(blank=True)
    cor_principal = models.CharField(max_length=7, default="#202020")
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Pelotao(models.Model):
    torcida = models.ForeignKey(Torcida, on_delete=models.CASCADE, related_name="pelotoes")
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    descricao = models.CharField(max_length=300, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome", "id"]
        constraints = [models.UniqueConstraint(fields=["torcida", "slug"], name="pelotao_slug_unico_por_torcida")]

    def __str__(self):
        return f"{self.nome} - {self.torcida.nome}"


class Membro(models.Model):
    class Papel(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MODERADOR = "moderador", "Moderador"
        LIDER_PELOTAO = "lider_pelotao", "Líder de pelotão"
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
        max_length=16,
        choices=Papel.choices,
        default=Papel.MEMBRO,
    )
    pelotao = models.ForeignKey(Pelotao, on_delete=models.SET_NULL, null=True, blank=True, related_name="membros")
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


class ConviteTorcida(models.Model):
    torcida = models.ForeignKey(
        Torcida, on_delete=models.CASCADE, related_name="convites"
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="convites_criados",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    papel = models.CharField(
        max_length=12, choices=Membro.Papel.choices, default=Membro.Papel.MEMBRO
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    limite_usos = models.PositiveIntegerField(default=1)
    usos = models.PositiveIntegerField(default=0)
    revogado_em = models.DateTimeField(null=True, blank=True)
    pelotao = models.ForeignKey(Pelotao, on_delete=models.SET_NULL, null=True, blank=True, related_name="convites")

    class Meta:
        indexes = [
            models.Index(fields=["torcida", "expira_em"], name="torcidas_co_torcida_0d17a1_idx"),
        ]

    @property
    def ativo(self):
        return (
            self.revogado_em is None
            and self.expira_em > timezone.now()
            and self.usos < self.limite_usos
        )
