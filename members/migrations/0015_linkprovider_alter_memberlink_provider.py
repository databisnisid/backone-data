# C61: MemberLink.provider moves from free text (50 chars) to a PROTECT FK on a
# LinkProvider lookup. Seed the starter rows, give every DISTINCT existing
# non-empty string its own row, then convert the column. Blank/null stay blank
# — a legacy link with no provider is preserved as-is, never given a placeholder
# name (C63) and never dropped (C63/V67).

import django.db.models.deletion
from django.db import migrations, models


def seed_and_backfill_providers(apps, schema_editor):
    LinkProvider = apps.get_model("members", "LinkProvider")
    MemberLink = apps.get_model("members", "MemberLink")

    for name in ("TELKOM", "ICON"):
        LinkProvider.objects.get_or_create(name=name)

    # One lookup row per distinct legacy string. `provider` is still the
    # CharField here (AlterField runs after), so store the lookup PK as a
    # numeric string — the char→FK ALTER then coerces it to int.
    legacy = (
        MemberLink.objects.exclude(provider__isnull=True)
        .exclude(provider="")
        .values_list("provider", flat=True)
        .distinct()
    )
    for value in list(legacy):
        row, _ = LinkProvider.objects.get_or_create(name=value)
        MemberLink.objects.filter(provider=value).update(provider=str(row.pk))


def backfill_to_string(apps, schema_editor):
    """Reverse: denormalize the FK id back to the provider NAME.

    Unapply order is AlterField (FK→Char) first, then this — so the char column
    already holds the FK id as a string and it must go through int() before the
    lookup (mirroring 0012). Names survive verbatim in LinkProvider.name, so
    this direction is lossless; blank/null stay NULL.
    """
    LinkProvider = apps.get_model("members", "LinkProvider")
    MemberLink = apps.get_model("members", "MemberLink")

    name_map = {p.pk: p.name for p in LinkProvider.objects.all()}
    for ml in MemberLink.objects.all():
        try:
            name = name_map.get(int(ml.provider)) if ml.provider else ""
        except (ValueError, TypeError):
            name = ml.provider or ""
        MemberLink.objects.filter(pk=ml.pk).update(provider=name or None)


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0014_members_sdwan_package_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Name')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Link Provider',
                'verbose_name_plural': 'Link Providers',
            },
        ),
        migrations.RunPython(seed_and_backfill_providers, backfill_to_string),
        migrations.AlterField(
            model_name='memberlink',
            name='provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='member_links', to='members.linkprovider', verbose_name='Provider'),
        ),
    ]
