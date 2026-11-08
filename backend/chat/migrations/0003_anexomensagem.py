import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0002_leituramensagem")]
    operations = [migrations.CreateModel(name="AnexoMensagem", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("tipo", models.CharField(choices=[("imagem", "Imagem"), ("video", "Vídeo")], max_length=10)), ("cloudinary_public_id", models.CharField(max_length=255, unique=True)), ("cloudinary_resource_type", models.CharField(choices=[("image", "Imagem"), ("video", "Vídeo")], max_length=10)), ("formato", models.CharField(max_length=20)), ("nome_original", models.CharField(max_length=255)), ("content_type", models.CharField(max_length=100)), ("tamanho", models.PositiveBigIntegerField()), ("criado_em", models.DateTimeField(auto_now_add=True)), ("mensagem", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="anexos", to="chat.mensagem"))], options={"ordering": ["id"]})]
