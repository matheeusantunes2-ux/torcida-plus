from django.conf import settings
from django.db import models


class Perfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    nome_exibicao = models.CharField(max_length=80, blank=True)
    biografia = models.CharField(max_length=300, blank=True)
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


class AdminAuditLog(models.Model):
    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_administrativas_torcida",
    )
    acao = models.CharField(max_length=40, db_index=True)
    entidade = models.CharField(max_length=40, db_index=True)
    entidade_id = models.CharField(max_length=64, blank=True)
    descricao = models.CharField(max_length=255)
    detalhes = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Registro de auditoria administrativa"
        verbose_name_plural = "Registros de auditoria administrativa"

    def __str__(self):
        return f"{self.acao} - {self.entidade} #{self.entidade_id}"
