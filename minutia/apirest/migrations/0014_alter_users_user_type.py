# Generated by Django 5.1.1 on 2024-10-13 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0013_infominuta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='user_type',
            field=models.CharField(choices=[('Estudiante', 'Estudiante'), ('Trabajador', 'Trabajador'), ('Ama de casa', 'Ama de casa')], max_length=50),
        ),
    ]