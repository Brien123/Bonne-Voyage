# Generated by Django 5.1 on 2024-08-26 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='bus_images/'),
        ),
    ]
