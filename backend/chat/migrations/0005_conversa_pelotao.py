import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0004_anexomensagem_audio"),
        ("torcidas", "0003_pelotoes"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversa",
            name="pelotao",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="conversas", to="torcidas.pelotao"),
        ),
    ]
