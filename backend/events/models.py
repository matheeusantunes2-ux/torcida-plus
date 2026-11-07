from django.conf import settings
from django.db import models


class Evento(models.Model):
    class Tipo(models.TextChoices):
        ENCONTRO = "encontro", "Encontro"
        JOGO = "jogo", "Jogo"
        VIAGEM = "viagem", "Viagem"
        INGRESSO = "ingresso", "Evento com ingresso"

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        PUBLICADO = "publicado", "Publicado"
        CANCELADO = "cancelado", "Cancelado"
        ENCERRADO = "encerrado", "Encerrado"

    torcida = models.ForeignKey("torcidas.Torcida", on_delete=models.CASCADE, related_name="eventos")
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.ENCONTRO)
    local = models.CharField(max_length=180, blank=True)
    inicio_em = models.DateTimeField()
    fim_em = models.DateTimeField(null=True, blank=True)
    capacidade = models.PositiveIntegerField(null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RASCUNHO)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="eventos_criados")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["inicio_em", "id"]
        indexes = [models.Index(fields=["torcida", "status", "inicio_em"], name="events_torcida_status_idx")]

    def __str__(self):
        return f"{self.titulo} - {self.torcida.nome}"
