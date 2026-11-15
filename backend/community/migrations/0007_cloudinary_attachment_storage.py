import community.storage
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0006_merge_publicacao_anexos_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publicacao",
            name="audio",
            field=models.FileField(
                blank=True,
                null=True,
                storage=community.storage.CloudinaryRawStorage(),
                upload_to="publicacoes/audio/",
            ),
        ),
        migrations.AlterField(
            model_name="publicacao",
            name="arquivo",
            field=models.FileField(
                blank=True,
                null=True,
                storage=community.storage.CloudinaryRawStorage(),
                upload_to="publicacoes/arquivos/",
            ),
        ),
    ]
