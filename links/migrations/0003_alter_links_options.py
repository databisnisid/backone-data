# Generated by Django 4.2.4 on 2024-02-28 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0002_alter_links_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='links',
            options={'verbose_name': 'Service', 'verbose_name_plural': 'Services'},
        ),
    ]
