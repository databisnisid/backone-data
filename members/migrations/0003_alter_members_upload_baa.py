# Generated by Django 4.2.4 on 2024-02-28 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_members_upload_baa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='members',
            name='upload_baa',
            field=models.FileField(blank=True, null=True, upload_to='baa/', verbose_name='BAA'),
        ),
    ]
