# Generated by Django 5.1.2 on 2024-11-29 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0004_messages_isvisibletoreceiver_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='messages',
            old_name='IsVisibleToReceiver',
            new_name='IsVisibleToUser1',
        ),
        migrations.RenameField(
            model_name='messages',
            old_name='IsVisibleToSender',
            new_name='IsVisibleToUser2',
        ),
    ]
