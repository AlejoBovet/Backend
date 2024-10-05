# Generated by Django 5.1.1 on 2024-10-05 21:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0009_remove_historialalimentos_alimento_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='minuta',
            name='state_minuta',
        ),
        migrations.RemoveField(
            model_name='minuta',
            name='user',
        ),
        migrations.RemoveField(
            model_name='users',
            name='type_user',
        ),
        migrations.AddField(
            model_name='dispensa',
            name='ultima_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='users',
            name='user_type',
            field=models.CharField(choices=[('admin', 'Admin'), ('regular', 'Regular'), ('student', 'Estudiante'), ('worker', 'Trabajador'), ('homemaker', 'Dueño de casa')], default='estudiante', max_length=50),
        ),
        migrations.AlterField(
            model_name='minuta',
            name='type_food',
            field=models.CharField(choices=[('desayuno', 'Desayuno'), ('almuerzo', 'Almuerzo'), ('cena', 'Cena')], max_length=50),
        ),
        migrations.CreateModel(
            name='ListaMinuta',
            fields=[
                ('id_lista_minuta', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_inicio', models.DateField(blank=True, null=True)),
                ('fecha_termino', models.DateField(blank=True, null=True)),
                ('state_minuta', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='listas_minuta', to='apirest.users')),
            ],
        ),
        migrations.AddField(
            model_name='minuta',
            name='lista_minuta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='minutas', to='apirest.listaminuta'),
        ),
    ]
