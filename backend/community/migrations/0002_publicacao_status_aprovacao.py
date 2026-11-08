from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="publicacao",
            name="imagem",
            field=models.ImageField(blank=True, null=True, upload_to="publicacoes/"),
        ),
        migrations.AddField(
            model_name="publicacao",
            name="status",
            field=models.CharField(choices=[("pendente", "Aguardando aprovação"), ("aprovada", "Aprovada"), ("rejeitada", "Rejeitada")], db_index=True, default="aprovada", max_length=12),
        ),
        migrations.AlterField(
            model_name="publicacao",
            name="status",
            field=models.CharField(choices=[("pendente", "Aguardando aprovação"), ("aprovada", "Aprovada"), ("rejeitada", "Rejeitada")], db_index=True, default="pendente", max_length=12),
        ),
    ]
