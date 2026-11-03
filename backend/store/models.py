from django.db import models


class Produto(models.Model):
    torcida = models.ForeignKey(
        "torcidas.Torcida",
        on_delete=models.CASCADE,
        related_name="produtos",
    )
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imagem = models.URLField(blank=True)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.torcida} - {self.nome}"

