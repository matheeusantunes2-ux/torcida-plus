from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="metodo_pagamento",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="pedido",
            name="status_pagamento",
            field=models.CharField(default="nao_iniciado", max_length=20),
        ),
        migrations.AddField(
            model_name="pedido",
            name="mercado_pago_preference_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="pedido",
            name="mercado_pago_payment_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="pedido",
            name="checkout_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
    ]
