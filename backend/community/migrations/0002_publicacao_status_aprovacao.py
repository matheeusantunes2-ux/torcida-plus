from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0004_notificacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicacao",
            name="status",
            field=models.CharField(
                choices=[
                    ("pendente", "Aguardando aprovação"),
                    ("aprovada", "Aprovada"),
                    ("rejeitada", "Rejeitada"),
                ],
                db_index=True,
                default="aprovada",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="publicacao",
            name="status",
            field=models.CharField(
                choices=[
                    ("pendente", "Aguardando aprovação"),
                    ("aprovada", "Aprovada"),
                    ("rejeitada", "Rejeitada"),
                ],
                db_index=True,
                default="pendente",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="notificacao",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("curtida", "Curtida"),
                    ("comentario", "Comentário"),
                    ("mensagem", "Mensagem"),
                    ("convite", "Convite"),
                    ("publicacao_pendente", "Publicação aguardando aprovação"),
                ],
                max_length=20,
            ),
        ),
    ]
