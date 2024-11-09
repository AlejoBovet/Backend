# Generated by Django 5.1.1 on 2024-11-02 00:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0018_alimento_uso_alimento'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sugerencias',
            fields=[
                ('id_recomendacion', models.AutoField(primary_key=True, serialize=False)),
                ('recomendacion', models.TextField()),
                ('fecha', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recomendaciones', to='apirest.users')),
            ],
        ),
    ]
