# Initial chat schema.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("torcidas", "0002_convitetorcida"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Conversa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("privada", "Privada"), ("grupo", "Grupo")], max_length=10)),
                ("nome", models.CharField(blank=True, max_length=120)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
                ("criada_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="conversas_criadas", to=settings.AUTH_USER_MODEL)),
                ("torcida", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversas", to="torcidas.torcida")),
            ],
            options={"ordering": ["-atualizada_em", "-id"]},
        ),
        migrations.CreateModel(
            name="ParticipanteConversa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entrou_em", models.DateTimeField(auto_now_add=True)),
                ("ativo", models.BooleanField(default=True)),
                ("conversa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participantes", to="chat.conversa")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participacoes_chat", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="participanteconversa",
            constraint=models.UniqueConstraint(fields=("conversa", "usuario"), name="chat_participante_unico"),
        ),
        migrations.CreateModel(
            name="Mensagem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("conteudo", models.TextField(max_length=4000)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("editada_em", models.DateTimeField(blank=True, null=True)),
                ("apagada_em", models.DateTimeField(blank=True, null=True)),
                ("autor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mensagens_chat", to=settings.AUTH_USER_MODEL)),
                ("conversa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensagens", to="chat.conversa")),
            ],
            options={"ordering": ["-criada_em", "-id"]},
        ),
    ]
