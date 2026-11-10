import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("torcidas", "0003_pelotoes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AtividadePelotao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("acao", models.CharField(max_length=48)),
                ("descricao", models.CharField(max_length=300)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("ator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="atividades_pelotoes", to=settings.AUTH_USER_MODEL)),
                ("pelotao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="atividades", to="torcidas.pelotao")),
                ("torcida", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="atividades_pelotoes", to="torcidas.torcida")),
            ],
            options={"ordering": ["-criado_em", "-id"]},
        ),
        migrations.AddIndex(model_name="atividadepelotao", index=models.Index(fields=["torcida", "criado_em"], name="atividade_tor_data_idx")),
        migrations.AddIndex(model_name="atividadepelotao", index=models.Index(fields=["pelotao", "criado_em"], name="atividade_pel_data_idx")),
    ]
