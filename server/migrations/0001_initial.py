# Generated by Django 5.1.6 on 2025-02-07 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('uid', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254)),
                ('purdueEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('displayName', models.CharField(max_length=255)),
                ('rating', models.FloatField(default=0)),
                ('bio', models.TextField(blank=True, null=True)),
                ('admin', models.BooleanField(default=False)),
                ('banned', models.BooleanField(default=False)),
            ],
        ),
    ]
