# Generated by Django 5.1.1 on 2024-11-17 01:35

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0030_estadisticasusuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='alimento',
            name='fecha_ingreso',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
    ]
