from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0004_pedido_expira_em"),
    ]

    operations = [
        migrations.CreateModel(
            name="MovimentacaoEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("reserva", "Reserva para pedido"), ("devolucao", "Devolução por cancelamento")], max_length=12)),
                ("quantidade", models.PositiveIntegerField()),
                ("saldo_anterior", models.PositiveIntegerField()),
                ("saldo_posterior", models.PositiveIntegerField()),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimentacoes_estoque", to="store.pedido")),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimentacoes_estoque", to="store.produto")),
            ],
            options={
                "ordering": ["-criado_em"],
                "constraints": [
                    models.UniqueConstraint(fields=("produto", "pedido", "tipo"), name="store_stock_move_order_product_type_uniq"),
                ],
            },
        ),
    ]
