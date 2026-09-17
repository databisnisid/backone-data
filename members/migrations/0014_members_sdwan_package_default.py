# C59: no site is ever left with a NULL SDWAN package.
#
# Sync creates sites without writing sdwan_package (V6), which is how prod
# reached 1249 of 1257 NULLs. A model default sends every new insert to the
# `BackOne - Tanpa SDWAN` row; this migration backfills the existing NULLs onto
# the same row so the dashboard pie partitions the active set exactly (V61).
# The row is resolved BY NAME — prod ids are DB-generated, never hardcode a pk.

import django.db.models.deletion
import members.models
from django.db import migrations, models


def backfill_null_sdwan(apps, schema_editor):
    SdwanPackage = apps.get_model("members", "SdwanPackage")
    Members = apps.get_model("members", "Members")
    pk = (
        SdwanPackage.objects.filter(name="BackOne - Tanpa SDWAN")
        .values_list("pk", flat=True)
        .first()
    )
    if pk is None:  # lookup absent (unseeded DB) — nothing sensible to write
        return
    Members.objects.filter(sdwan_package__isnull=True).update(sdwan_package=pk)


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0013_lookup_name_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="members",
            name="sdwan_package",
            field=models.ForeignKey(
                blank=True,
                default=members.models.default_sdwan_package_id,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="members",
                to="members.sdwanpackage",
                verbose_name="SDWAN Package",
            ),
        ),
        migrations.RunPython(backfill_null_sdwan, migrations.RunPython.noop),
    ]
