# Generated by Django 5.1.1 on 2024-10-10 13:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0012_listaminuta_fecha_creacion_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoMinuta',
            fields=[
                ('id_info_minuta', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_dieta', models.CharField(max_length=70)),
                ('cantidad_personas', models.IntegerField()),
                ('lista_minuta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info_minutas', to='apirest.listaminuta')),
            ],
        ),
    ]