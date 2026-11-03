import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="LeituraMensagem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("lida_em", models.DateTimeField(auto_now_add=True)),
                ("mensagem", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leituras", to="chat.mensagem")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leituras_chat", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="leituramensagem",
            constraint=models.UniqueConstraint(fields=("mensagem", "usuario"), name="chat_leitura_unica"),
        ),
    ]
