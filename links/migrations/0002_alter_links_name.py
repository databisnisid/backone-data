# Generated by Django 4.2.4 on 2024-02-28 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='links',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Name'),
        ),
    ]
