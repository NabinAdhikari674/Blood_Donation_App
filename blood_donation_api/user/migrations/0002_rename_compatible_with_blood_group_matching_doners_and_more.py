# Generated by Django 4.2.5 on 2023-10-01 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blood_group',
            old_name='compatible_with',
            new_name='matching_doners',
        ),
        migrations.AddField(
            model_name='blood_group',
            name='blood_group',
            field=models.CharField(default=None, max_length=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='blood_group',
            name='description',
            field=models.CharField(default=None, max_length=500),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='blood_group',
            name='blood_group_name',
            field=models.CharField(max_length=20),
        ),
    ]