# Generated by Django 5.1 on 2024-08-26 17:25

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0003_busoperator'),
    ]

    operations = [
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origin', models.CharField(max_length=100)),
                ('destination', models.CharField(max_length=100)),
                ('distance', models.DecimalField(decimal_places=2, help_text='Distance in kilometers', max_digits=6)),
            ],
        ),
        migrations.CreateModel(
            name='Bus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('bus_number', models.CharField(max_length=20, unique=True)),
                ('capacity', models.PositiveIntegerField()),
                ('amenities', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.busoperator')),
            ],
        ),
    ]
