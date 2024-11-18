# Generated by Django 5.1.3 on 2024-11-18 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('friendships', '0003_alter_friendships_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendships',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
    ]
