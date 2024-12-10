# Generated by Django 5.1.1 on 2024-11-08 18:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0026_alter_objetivo_tipo_objetivo'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoObjetivo',
            fields=[
                ('id_tipo_objetivo', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_objetivo', models.CharField(choices=[('minutas completas', 'Minutas completas'), ('lista de minutas completas', 'Lista de minutas completas'), ('vegetales usados', 'Vegetales usados'), ('frutas usadas', 'Frutas usadas'), ('carbohidratos usados', 'Carbohidratos usados')], max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='objetivo',
            name='tipo_objetivo',
        ),
        migrations.AddField(
            model_name='infominuta',
            name='estado_dias',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='objetivo',
            name='id_tipo_objetivo',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='apirest.tipoobjetivo'),
            preserve_default=False,
        ),
    ]
