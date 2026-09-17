from django.db import migrations, models


def backfill_domain(apps, schema_editor):
    """Every row predating multi-domain sync came from the backone upstream."""
    Networks = apps.get_model('networks', 'Networks')
    Networks.objects.filter(domain='').update(domain='manage.backone.cloud')


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0003_networksgroup_member_sites'),
    ]

    operations = [
        migrations.AddField(
            model_name='networks',
            name='domain',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Source Domain'),
        ),
        migrations.RunPython(backfill_domain, migrations.RunPython.noop),
    ]
