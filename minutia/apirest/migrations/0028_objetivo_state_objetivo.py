# Generated by Django 5.1.1 on 2024-11-09 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0027_tipoobjetivo_remove_objetivo_tipo_objetivo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='objetivo',
            name='state_objetivo',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
