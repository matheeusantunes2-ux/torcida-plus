import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("torcidas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConviteTorcida",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("papel", models.CharField(choices=[("admin", "Administrador"), ("moderador", "Moderador"), ("membro", "Membro")], default="membro", max_length=12)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("expira_em", models.DateTimeField()),
                ("limite_usos", models.PositiveIntegerField(default=1)),
                ("usos", models.PositiveIntegerField(default=0)),
                ("revogado_em", models.DateTimeField(blank=True, null=True)),
                ("criado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="convites_criados", to=settings.AUTH_USER_MODEL)),
                ("torcida", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="convites", to="torcidas.torcida")),
            ],
        ),
        migrations.AddIndex(
            model_name="convitetorcida",
            index=models.Index(fields=["torcida", "expira_em"], name="torcidas_co_torcida_0d17a1_idx"),
        ),
    ]
