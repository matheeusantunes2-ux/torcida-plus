import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("torcidas", "0006_associacoes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="PagamentoAssociacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("vencimento", models.DateField()),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("pago", "Pago"), ("atrasado", "Atrasado"), ("cancelado", "Cancelado")], db_index=True, default="pendente", max_length=12)),
                ("pago_em", models.DateTimeField(blank=True, null=True)),
                ("observacao", models.CharField(blank=True, max_length=240)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("associacao", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pagamentos", to="torcidas.associacao")),
                ("confirmado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pagamentos_associacao_confirmados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["vencimento", "id"]},
        ),
        migrations.AddConstraint(model_name="pagamentoassociacao", constraint=models.UniqueConstraint(fields=("associacao", "vencimento"), name="pagamento_assoc_venc_unico")),
        migrations.AddIndex(model_name="pagamentoassociacao", index=models.Index(fields=["status", "vencimento"], name="pag_assoc_status_venc_idx")),
    ]
