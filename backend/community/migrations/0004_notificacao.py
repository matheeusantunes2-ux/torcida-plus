from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0003_publicacao_imagem"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notificacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("curtida", "Curtida"), ("comentario", "Comentário"), ("mensagem", "Mensagem"), ("convite", "Convite")], max_length=20)),
                ("texto", models.CharField(max_length=240)),
                ("referencia", models.CharField(blank=True, max_length=160)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("lida_em", models.DateTimeField(blank=True, null=True)),
                ("ator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notificacoes_enviadas_torcida", to=settings.AUTH_USER_MODEL)),
                ("destinatario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notificacoes_torcida", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-criada_em"]},
        ),
        migrations.AddIndex(
            model_name="notificacao",
            index=models.Index(fields=["destinatario", "lida_em", "-criada_em"], name="notif_user_read_date_idx"),
        ),
    ]
