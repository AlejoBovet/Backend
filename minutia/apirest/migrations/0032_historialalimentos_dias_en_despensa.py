# Generated by Django 5.1.1 on 2024-11-17 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0031_alimento_fecha_ingreso'),
    ]

    operations = [
        migrations.AddField(
            model_name='historialalimentos',
            name='dias_en_despensa',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]