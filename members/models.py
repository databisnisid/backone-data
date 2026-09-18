from django.db import models
from modelcluster.models import ClusterableModel, ParentalKey
from modelcluster.fields import ParentalManyToManyField
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from networks.models import Networks
from links.models import Links



# class Members(models.Model):
class SdwanPackage(models.Model):
    """Lookup: SDWAN package options (C24). Backs Members.sdwan_package FK."""

    name = models.CharField(_("Name"), max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("SDWAN Package")
        verbose_name_plural = _("SDWAN Packages")

    def __str__(self):
        return "%s" % self.name


DEFAULT_SDWAN_PACKAGE = "BackOne - Tanpa SDWAN"


def default_sdwan_package_id():
    """PK of the `Tanpa SDWAN` row, resolved BY NAME (C59).

    Never a hardcoded pk: prod ids are DB-generated. Returns None if the row is
    absent so `migrate` on a fresh DB and the reverse migration stay safe. Kept
    as a callable (not `default=<pk>`) for exactly that reason — callables are
    evaluated per insert and never baked into the schema.
    """
    return (
        SdwanPackage.objects.filter(name=DEFAULT_SDWAN_PACKAGE)
        .values_list("pk", flat=True)
        .first()
    )


class BaaStatus(models.Model):
    """Lookup: BAA status category options (C24). Backs Members.baa_status_category FK."""

    name = models.CharField(_("Name"), max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("BAA Status")
        verbose_name_plural = _("BAA Statuses")

    def __str__(self):
        return "%s" % self.name


class LinkRole(models.Model):
    """Lookup: member-link role options (C24). Backs MemberLink.role FK."""

    name = models.CharField(_("Name"), max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Link Role")
        verbose_name_plural = _("Link Roles")

    def __str__(self):
        return "%s" % self.name


class LinkProvider(models.Model):
    """Lookup: link provider options (C61). Backs MemberLink.provider FK.

    max_length=50, not LinkRole's 10: `provider` was free text at 50 chars, so a
    shorter column could truncate a legacy value during the backfill (C61).
    """

    name = models.CharField(_("Name"), max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Link Provider")
        verbose_name_plural = _("Link Providers")

    def __str__(self):
        return "%s" % self.name


class Members(ClusterableModel):
    name = models.CharField(_("Member Name"), max_length=50)
    member_code = models.CharField(
        _("Member Code"), max_length=20, blank=True, null=True
    )
    description = models.TextField(_("Description"), blank=True)
    member_id = models.CharField(_("Member ID"), max_length=50, unique=True)

    address = models.CharField(_("Address"), max_length=250, blank=True, null=True)
    location = models.CharField(_("Location"), max_length=250, blank=True, null=True)

    online_at = models.DateField(_("Start Online"), blank=True, null=True)
    offline_at = models.DateTimeField(_("Stop Online"), blank=True, null=True)

    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        verbose_name=_("Network"),
        blank=True,
        null=True,
    )

    links = ParentalManyToManyField(Links, related_name="members")
    # links = models.ManyToManyField(Links, related_name='members')

    upload_baa = models.FileField(_("BAA"), upload_to="baa/", blank=True, null=True)
    invoice_number = models.CharField(
        _("Invoice Number"), max_length=50, blank=True, null=True
    )

    # member_sid = models.TextField(_('SID'), blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    service_line = models.CharField(
        _("Service Line"), max_length=20, blank=True, null=True
    )
    quota_string = models.CharField(
        _("Quota Info"), max_length=50, blank=True, null=True
    )

    # Mockup Sites Dashboard — user-owned data (V4,V5,V6)
    is_manual = models.BooleanField(_("Manual Site"), default=False)
    ip_address = models.CharField(_("IP Address"), max_length=50, blank=True, null=True)
    sdwan_package = models.ForeignKey(
        SdwanPackage,
        on_delete=models.PROTECT,
        related_name="members",
        verbose_name=_("SDWAN Package"),
        blank=True,
        null=True,
        default=default_sdwan_package_id,
    )
    project_number = models.CharField(
        _("Project Number"), max_length=50, blank=True, null=True
    )
    baa_status_category = models.ForeignKey(
        BaaStatus,
        on_delete=models.PROTECT,
        related_name="members",
        verbose_name=_("BAA Status Category"),
        blank=True,
        null=True,
    )
    po_file_user = models.FileField(
        _("PO from User"), upload_to="po/", blank=True, null=True
    )
    po_file_vendor = models.FileField(
        _("PO to Vendor"), upload_to="po/", blank=True, null=True
    )
    invoice_file = models.FileField(
        _("Invoice File"), upload_to="invoice/", blank=True, null=True
    )
    bap_file = models.FileField(
        _("BAP Dismantle"), upload_to="bap/", blank=True, null=True
    )

    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Owner'),
        null=True
    )
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )
    """

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "members"
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self):
        return "%s" % self.name

    def delete(self, *args, **kwargs):
        for field_name in (
            "upload_baa",
            "po_file_user",
            "po_file_vendor",
            "invoice_file",
            "bap_file",
        ):
            field = getattr(self, field_name, None)
            if field:
                field.delete()
        super().delete(*args, **kwargs)

    def name_with_network(self):
        text = format_html("{}<br />", self.name)
        if self.network:
            text = format_html("{}<small>{}</small>", text, self.network)
        return text

    name_with_network.short_description = _("Site Name")
    name_with_network.admin_order_field = "name"

    def get_quota_type(self) -> str:
        quota_type: str = ""
        if self.quota_string:
            quota_split = self.quota_string.split("/")

            try:
                quota_split[3]
                quota_type = quota_split[3]

            except (IndexError, ValueError):
                pass

        return quota_type

    get_quota_type.short_description = _("Quota Type")

    def get_quota_current(self) -> str:
        quota_current: str = ""
        if self.quota_string:
            quota_split = self.quota_string.split("/")

            try:
                quota_split[0]
                quota_current = quota_split[0]

            except (IndexError, ValueError):
                pass

        return quota_current

    get_quota_current.short_description = _("Sisa Kuota")

    def get_quota_usage(self) -> str:
        quota_usage = 0
        if self.quota_string:
            quota_split = self.quota_string.split("/")
            quota_current = self.get_quota_current()

            try:
                quota_total = quota_split[1]
            except (IndexError, ValueError):
                pass
            else:
                try:
                    quota_usage = -1 * float(quota_total.replace("GB", "")) + float(
                        quota_current.replace("GB", "")
                    )
                except ValueError:
                    quota_usage = 0

        return str(round(quota_usage, 2) * -1) + "GB"

    get_quota_usage.short_description = _("Penggunaan Kuota")

    def get_quota_day(self) -> str:
        quota_day: str = ""
        if self.quota_string:
            quota_split = self.quota_string.split("/")

            try:
                quota_split[2]
                quota_day = quota_split[2]

            except (IndexError, ValueError):
                pass

        return quota_day

    get_quota_day.short_description = _("Sisa Kuota Hari")

    def get_quota_string_no_total(self) -> str:
        quota_string: str = ""
        # quota_string, quota_current, quota_day, quota_type = ''

        if self.quota_string:
            quota_split = self.quota_string.split("/")

            try:
                quota_split[0]
                quota_current = quota_split[0]

            except (IndexError, ValueError):
                quota_current = ""

            try:
                quota_split[2]
                quota_day = quota_split[2]

            except (IndexError, ValueError):
                quota_day = ""

            try:
                quota_split[3]
                quota_type = quota_split[3]

            except (IndexError, ValueError):
                quota_type = ""

            quota_string = "{}/{}/{}".format(quota_current, quota_day, quota_type)

        return quota_string.upper()

    def name_with_parameters(self):
        text = format_html(
            "{}<br /><small>{}</small>", self.name, self.get_links_html()
        )

        if self.service_line and self.get_quota_type().lower() in settings.QUOTA_TYPE:
            text = format_html("{}<br /><small>{}</small>", text, self.service_line)
            if self.quota_string:
                text = format_html(
                    "{}<br /><small>{}</small>", text, self.get_quota_string_no_total()
                )
                # text = format_html('{}<br /><small>{}</small>', text, self.quota_string.upper())
        return text

    name_with_parameters.short_description = _("Site")
    name_with_parameters.admin_order_field = "name"

    def get_links(self):
        return ", ".join([p.name for p in self.links.all()])
        # return self.links.all().values_list('name', flat=True)

    get_links.short_description = _("Services")

    def get_links_html(self):
        return format_html("<br />".join([p.name for p in self.links.all()]))

    get_links_html.short_description = _("Services")

    def address_and_services(self):
        # svc_text = format_html_join('\n', '<li>{}</li>', ([p.name for p in self.links.all()]))
        # text = format_html('{}<br /><ul>{}</ul>', self.address, svc_text)
        text = format_html(
            "{}<br /><small>{}</small>", self.address, self.get_links_html()
        )
        return text

    address_and_services.short_description = _("Address and Services")
    address_and_services.admin_order_field = "address"

    def baa_file(self):
        text = format_html(
            "<img src='{}/static/members/images/notfound.png' width='40'>",
            settings.WAGTAILADMIN_BASE_URL,
        )
        if self.upload_baa:
            media_url = (
                settings.WAGTAILADMIN_BASE_URL
                + settings.MEDIA_URL
                + str(self.upload_baa)
            )
            text = format_html(
                "<a href='{}'><img src='{}/static/members/images/file.png' width='50'></a>",
                media_url,
                settings.WAGTAILADMIN_BASE_URL,
            )

        return text

    baa_file.short_description = _("BAA")
    baa_file.admin_order_field = "upload_baa"

    def address_multiline(self):
        text = None
        if self.address:
            text = format_html(self.address.replace(",", "<br />"))
        return text

    address_multiline.short_description = _("Address")
    address_multiline.admin_order_field = "address"

    def network_group(self):
        if self.network:
            if self.network.network_group:
                return self.network.network_group.name
            else:
                return "Ungroup"
        else:
            return None

    network_group.short_description = _("Networks")
    network_group.admin_order_field = "networks"


class MemberLink(models.Model):
    """Multi-link detail for a site (mockup col B): MAIN/BACKUP/SINGLE with provider, capacity, SID."""

    member = ParentalKey(Members, related_name="member_links", on_delete=models.CASCADE)
    role = models.ForeignKey(
        LinkRole,
        on_delete=models.PROTECT,
        related_name="member_links",
        verbose_name=_("Link Role"),
        blank=True,
        null=True,
    )
    service = models.ForeignKey(
        Links,
        on_delete=models.SET_NULL,
        verbose_name=_("Service"),
        blank=True,
        null=True,
    )
    provider = models.ForeignKey(
        LinkProvider,
        on_delete=models.PROTECT,
        related_name="member_links",
        verbose_name=_("Provider"),
        blank=True,
        null=True,
    )
    capacity = models.CharField(_("Capacity"), max_length=20, blank=True, null=True)
    sid = models.CharField(_("SID Langganan"), max_length=100, blank=True, null=True)

    class Meta:
        db_table = "members_link"
        verbose_name = _("Member Link")
        verbose_name_plural = _("Member Links")

    def __str__(self):
        return "%s %s - %s" % (
            self.role.name if self.role else "",
            self.service or "",
            self.provider.name if self.provider else "",
        )



