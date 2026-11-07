import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("torcidas", "0002_convitetorcida"),
    ]
    operations = [
        migrations.CreateModel(
            name="Evento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=150)),
                ("descricao", models.TextField(blank=True)),
                ("tipo", models.CharField(choices=[("encontro", "Encontro"), ("jogo", "Jogo"), ("viagem", "Viagem"), ("ingresso", "Evento com ingresso")], default="encontro", max_length=12)),
                ("local", models.CharField(blank=True, max_length=180)),
                ("inicio_em", models.DateTimeField()),
                ("fim_em", models.DateTimeField(blank=True, null=True)),
                ("capacidade", models.PositiveIntegerField(blank=True, null=True)),
                ("valor", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("rascunho", "Rascunho"), ("publicado", "Publicado"), ("cancelado", "Cancelado"), ("encerrado", "Encerrado")], default="rascunho", max_length=12)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("criado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="eventos_criados", to=settings.AUTH_USER_MODEL)),
                ("torcida", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="eventos", to="torcidas.torcida")),
            ],
            options={"ordering": ["inicio_em", "id"]},
        ),
        migrations.AddIndex(
            model_name="evento",
            index=models.Index(fields=["torcida", "status", "inicio_em"], name="events_torcida_status_idx"),
        ),
    ]
