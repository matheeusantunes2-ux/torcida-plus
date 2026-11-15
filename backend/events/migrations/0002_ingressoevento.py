import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("events", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="IngressoEvento", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("quantidade", models.PositiveIntegerField(default=1)),
            ("valor_total", models.DecimalField(decimal_places=2, max_digits=10)),
            ("status", models.CharField(choices=[("aguardando", "Aguardando pagamento"), ("pago", "Pago"), ("cancelado", "Cancelado")], db_index=True, default="aguardando", max_length=12)),
            ("codigo", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("metodo_pagamento", models.CharField(blank=True, default="", max_length=12)),
            ("checkout_url", models.URLField(blank=True, max_length=500)),
            ("preference_id", models.CharField(blank=True, default="", max_length=100)),
            ("payment_id", models.CharField(blank=True, default="", max_length=100)),
            ("expira_em", models.DateTimeField(blank=True, null=True)),
            ("criado_em", models.DateTimeField(auto_now_add=True)),
            ("comprador", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ingressos_eventos", to=settings.AUTH_USER_MODEL)),
            ("evento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ingressos", to="events.evento")),
        ], options={"ordering": ["-criado_em"]}),
        migrations.AddIndex(model_name="ingressoevento", index=models.Index(fields=["evento", "status"], name="event_ticket_status_idx")),
    ]
