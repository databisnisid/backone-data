# Generated by Django 4.2.4 on 2024-03-04 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_members_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='members',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Invoice Number'),
        ),
    ]
