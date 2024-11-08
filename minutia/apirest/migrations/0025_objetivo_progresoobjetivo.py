# Generated by Django 5.1.1 on 2024-11-07 18:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0024_infominuta_tipo_alimento'),
    ]

    operations = [
        migrations.CreateModel(
            name='Objetivo',
            fields=[
                ('id_objetivo', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_objetivo', models.CharField(max_length=100)),
                ('meta_total', models.PositiveIntegerField()),
                ('completado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objetivos', to='apirest.users')),
            ],
        ),
        migrations.CreateModel(
            name='ProgresoObjetivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_now_add=True)),
                ('progreso_diario', models.PositiveIntegerField()),
                ('progreso_acumulado', models.PositiveIntegerField()),
                ('objetivo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progresos', to='apirest.objetivo')),
            ],
        ),
    ]