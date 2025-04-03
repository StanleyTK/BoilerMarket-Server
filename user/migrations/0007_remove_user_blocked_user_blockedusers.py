# Generated by Django 5.1.6 on 2025-04-03 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_user_blocked'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='blocked',
        ),
        migrations.AddField(
            model_name='user',
            name='blockedUsers',
            field=models.ManyToManyField(blank=True, related_name='blocked_by', to='user.user'),
        ),
    ]
