# Generated by Django 5.1.1 on 2024-11-17 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0032_historialalimentos_dias_en_despensa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historialalimentos',
            name='dias_en_despensa',
            field=models.IntegerField(null=True),
        ),
    ]
