# Generated by Django 5.1.4 on 2024-12-13 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_blacklist'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='IsOnline',
            field=models.BooleanField(default=False),
        ),
    ]