from django.db import models
from django.conf import settings


class Evento(models.Model):
    torcida = models.ForeignKey(
        "torcidas.Torcida",
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    titulo = models.CharField(max_length=180)
    descricao = models.TextField(blank=True)
    local = models.CharField(max_length=180, blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(blank=True, null=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="eventos_criados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_inicio"]

    def __str__(self):
        return f"{self.torcida} - {self.titulo}"

