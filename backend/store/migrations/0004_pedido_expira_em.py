from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0003_pedido_estoque_devolvido"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="expira_em",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
