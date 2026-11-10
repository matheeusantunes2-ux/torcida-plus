import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("torcidas", "0002_convitetorcida")]

    operations = [
        migrations.CreateModel(
            name="Pelotao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140)),
                ("descricao", models.CharField(blank=True, max_length=300)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("torcida", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pelotoes", to="torcidas.torcida")),
            ],
            options={"ordering": ["nome", "id"]},
        ),
        migrations.AddConstraint(
            model_name="pelotao",
            constraint=models.UniqueConstraint(fields=("torcida", "slug"), name="pelotao_slug_unico_por_torcida"),
        ),
        migrations.AddField(
            model_name="membro",
            name="pelotao",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="membros", to="torcidas.pelotao"),
        ),
        migrations.AddField(
            model_name="convitetorcida",
            name="pelotao",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="convites", to="torcidas.pelotao"),
        ),
    ]
