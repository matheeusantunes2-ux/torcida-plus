from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0002_checkout_payment_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="estoque_devolvido",
            field=models.BooleanField(default=False),
        ),
    ]
