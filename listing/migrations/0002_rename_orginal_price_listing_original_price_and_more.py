# Generated by Django 5.1.6 on 2025-02-24 20:03

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("listing", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="listing",
            old_name="orginal_price",
            new_name="original_price",
        ),
        migrations.RenameField(
            model_name="listing",
            old_name="userId",
            new_name="user",
        ),
    ]
