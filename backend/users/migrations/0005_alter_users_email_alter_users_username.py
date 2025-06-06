# Generated by Django 5.1.2 on 2024-11-13 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_users_isoauth'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='email',
            field=models.EmailField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='users',
            name='username',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
