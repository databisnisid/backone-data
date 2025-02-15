from django.db import models
from modelcluster.models import ClusterableModel, ParentalKey
from modelcluster.fields import ParentalManyToManyField
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from networks.models import Networks
from links.models import Links


# class Members(models.Model):
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
        # limit_choices_to=limit_choices_to_current_user,
        verbose_name=_("Network"),
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
        if self.upload_baa:
            self.upload_baa.delete()
        super().delete(*args, **kwargs)

    def name_with_network(self):
        text = format_html("{}<br /><small>{}</small>", self.name, self.network)
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

            except IndexError or ValueError:
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

            except IndexError or ValueError:
                pass

        return quota_current

    get_quota_current.short_description = _("Sisa Kuota")

    def get_quota_usage(self) -> str:
        quota_current: str = ""
        if self.quota_string:
            quota_split = self.quota_string.split("/")
            quota_current = self.get_quota_current()

            try:
                quota_split[1]
                quota_total = quota_split[1]

            except IndexError or ValueError:
                pass

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

            except IndexError or ValueError:
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

            except IndexError or ValueError:
                quota_current = ""

            try:
                quota_split[2]
                quota_day = quota_split[2]

            except IndexError or ValueError:
                quota_day = ""

            try:
                quota_split[3]
                quota_type = quota_split[3]

            except IndexError or ValueError:
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
