# Generated by Django 5.1.1 on 2024-11-17 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0034_desperdicio'),
    ]

    operations = [
        migrations.AddField(
            model_name='infominuta',
            name='contado_en_estadisticas',
            field=models.BooleanField(default=False),
        ),
    ]
