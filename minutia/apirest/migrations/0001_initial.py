# Generated by Django 5.1.1 on 2024-09-19 21:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alimento',
            fields=[
                ('id_alimento', models.AutoField(primary_key=True, serialize=False)),
                ('name_alimento', models.CharField(max_length=255)),
                ('unit_measurement', models.CharField(max_length=255)),
                ('load_alimento', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Dispensa',
            fields=[
                ('id_dispensa', models.AutoField(primary_key=True, serialize=False)),
                ('alimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apirest.alimento')),
            ],
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id_user', models.AutoField(primary_key=True, serialize=False)),
                ('name_user', models.CharField(max_length=255)),
                ('last_name_user', models.CharField(max_length=255)),
                ('year_user', models.IntegerField()),
                ('type_user', models.CharField(max_length=255)),
                ('dispensa', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='apirest.dispensa')),
            ],
        ),
        migrations.CreateModel(
            name='Minuta',
            fields=[
                ('id_minuta', models.AutoField(primary_key=True, serialize=False)),
                ('fecha', models.DateField(blank=True, null=True)),
                ('tipe_food', models.CharField(max_length=255)),
                ('name_food', models.CharField(max_length=255)),
                ('state', models.BooleanField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apirest.users')),
            ],
        ),
        migrations.CreateModel(
            name='HistorialAlimentos',
            fields=[
                ('id_historial', models.AutoField(primary_key=True, serialize=False)),
                ('name_alimento', models.CharField(max_length=255)),
                ('unit_measurement', models.CharField(max_length=255)),
                ('load_alimento', models.IntegerField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('alimento', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='apirest.alimento')),
                ('dispensa', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='apirest.dispensa')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apirest.users')),
            ],
        ),
    ]
