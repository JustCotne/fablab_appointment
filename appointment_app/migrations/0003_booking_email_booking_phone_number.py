# Generated by Django 5.1.6 on 2025-02-12 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment_app', '0002_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='phone_number',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
    ]
