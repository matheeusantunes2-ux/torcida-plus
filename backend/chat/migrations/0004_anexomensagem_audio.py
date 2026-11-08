from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0003_anexomensagem")]
    operations = [
        migrations.AlterField(
            model_name="anexomensagem",
            name="tipo",
            field=models.CharField(
                choices=[("imagem", "Imagem"), ("video", "Vídeo"), ("audio", "Áudio")],
                max_length=10,
            ),
        ),
    ]
