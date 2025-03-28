# Generated by Django 5.1.6 on 2025-03-23 17:38

import storages.backends.s3
import user.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_user_profilepicture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profilePicture',
            field=models.ImageField(blank=True, null=True, storage=storages.backends.s3.S3Storage(), upload_to=user.models.user_profile_picture_path),
        ),
    ]
