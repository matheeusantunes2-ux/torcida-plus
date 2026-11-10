from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("torcidas", "0003_pelotoes")]

    operations = [
        migrations.AlterField(
            model_name="membro",
            name="papel",
            field=models.CharField(
                choices=[("admin", "Administrador"), ("moderador", "Moderador"), ("lider_pelotao", "Líder de pelotão"), ("membro", "Membro")],
                default="membro",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="convitetorcida",
            name="papel",
            field=models.CharField(
                choices=[("admin", "Administrador"), ("moderador", "Moderador"), ("lider_pelotao", "Líder de pelotão"), ("membro", "Membro")],
                default="membro",
                max_length=16,
            ),
        ),
    ]
