from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("community", "0004_notificacao")]
    operations = [
        migrations.AddField(model_name="publicacao", name="audio", field=models.FileField(blank=True, null=True, upload_to="publicacoes/audio/")),
        migrations.AddField(model_name="publicacao", name="arquivo", field=models.FileField(blank=True, null=True, upload_to="publicacoes/arquivos/")),
    ]
