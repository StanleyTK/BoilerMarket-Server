# Generated by Django 5.1.6 on 2025-03-25 17:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('message', '0005_remove_room_messages_alter_room_unique_together_and_more'),
        ('user', '0003_user_purdueverificationlastsent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('rid', models.AutoField(primary_key=True, serialize=False)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_room', to='user.user')),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='listing.listing')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_room', to='user.user')),
            ],
            options={
                'unique_together': {('seller', 'buyer', 'listing')},
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('mid', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('timeSent', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='user.user')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='user.user')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='message.room')),
            ],
        ),
    ]
