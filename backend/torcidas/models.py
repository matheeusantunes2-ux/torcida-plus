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
        max_length=16, choices=Membro.Papel.choices, default=Membro.Papel.MEMBRO
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


class AtividadePelotao(models.Model):
    torcida = models.ForeignKey(Torcida, on_delete=models.CASCADE, related_name="atividades_pelotoes")
    pelotao = models.ForeignKey(Pelotao, on_delete=models.SET_NULL, null=True, blank=True, related_name="atividades")
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="atividades_pelotoes")
    acao = models.CharField(max_length=48)
    descricao = models.CharField(max_length=300)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        indexes = [models.Index(fields=["torcida", "criado_em"], name="atividade_tor_data_idx"),
                   models.Index(fields=["pelotao", "criado_em"], name="atividade_pel_data_idx")]

    def __str__(self):
        return f"{self.acao}: {self.descricao}"


class PlanoAssociacao(models.Model):
    torcida = models.ForeignKey(Torcida, on_delete=models.CASCADE, related_name="planos_associacao")
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=300, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duracao_dias = models.PositiveIntegerField(default=365)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["valor", "nome"]
        constraints = [models.UniqueConstraint(fields=["torcida", "nome"], name="plano_nome_unico_torcida")]

    def __str__(self):
        return f"{self.nome} - {self.torcida.nome}"


class Associacao(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ATIVA = "ativa", "Ativa"
        EXPIRADA = "expirada", "Expirada"
        CANCELADA = "cancelada", "Cancelada"

    torcida = models.ForeignKey(Torcida, on_delete=models.CASCADE, related_name="associacoes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="associacoes_torcida")
    plano = models.ForeignKey(PlanoAssociacao, on_delete=models.PROTECT, related_name="associacoes")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    inicio_em = models.DateTimeField(null=True, blank=True)
    fim_em = models.DateTimeField(null=True, blank=True, db_index=True)
    aprovado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="associacoes_aprovadas")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [models.UniqueConstraint(fields=["torcida", "usuario"], condition=~models.Q(status="cancelada"), name="associacao_ativa_unica_usuario_torcida")]
        indexes = [models.Index(fields=["torcida", "status", "fim_em"], name="assoc_tor_status_fim_idx")]

    def __str__(self):
        return f"{self.usuario} - {self.torcida} ({self.status})"


class PagamentoAssociacao(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        PAGO = "pago", "Pago"
        ATRASADO = "atrasado", "Atrasado"
        CANCELADO = "cancelado", "Cancelado"

    associacao = models.ForeignKey(Associacao, on_delete=models.CASCADE, related_name="pagamentos")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    pago_em = models.DateTimeField(null=True, blank=True)
    confirmado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="pagamentos_associacao_confirmados")
    observacao = models.CharField(max_length=240, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["vencimento", "id"]
        constraints = [models.UniqueConstraint(fields=["associacao", "vencimento"], name="pagamento_assoc_venc_unico")]
        indexes = [models.Index(fields=["status", "vencimento"], name="pag_assoc_status_venc_idx")]

    def __str__(self):
        return f"{self.associacao_id} - {self.vencimento} ({self.status})"
