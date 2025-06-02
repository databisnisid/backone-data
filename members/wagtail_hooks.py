from crum import get_current_user
from django.core.exceptions import ObjectDoesNotExist
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    PermissionHelper,
    modeladmin_register,
)
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    FieldRowPanel,
    InlinePanel,
    ObjectList,
)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from django.contrib.auth.models import Group
from .models import Members


class MembersPermissionHelper(PermissionHelper):
    """

    def user_can_list(self, user):
        return True

    """

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        if user.is_superuser:
            return True
        else:
            return False

    """
    def user_can_edit_obj(self, user, obj):
        return False
    """


class MembersAdmin(ModelAdmin):
    model = Members
    menu_label = "Sites"
    menu_icon = "globe"
    inspect_view_enabled = True
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "name_with_network",
        "address_multiline",
        "online_at",
        "get_links",
        "upload_baa",
    )
    list_export = list_display
    search_fields = (
        "name",
        "network__name",
        "member_id",
        "notes",
        "invoice_number",
        "quota_string",
        "network__network_group__name",
        "service_line",
    )
    # list_filter = ('network',)
    list_per_page = 100
    permission_helper_class = MembersPermissionHelper

    """
    panels = [
            MultiFieldPanel([
                FieldPanel('name', read_only=True),
                #FieldPanel('description', read_only=True),
                FieldPanel('network', read_only=True),
                ], heading=_('Site and Network')),
            FieldPanel('address', read_only=True),
            #GeoAddressPanel("address", geocoder=geocoders.GOOGLE_MAPS, read_only=True),
            #GoogleMapsPanel('location', address_field='address', read_only=True),
            FieldRowPanel([
                FieldPanel('online_at', read_only=True),
                FieldPanel('offline_at', read_only=True),
                ]),

            FieldRowPanel([
                FieldPanel('links'),
                MultiFieldPanel([
                    FieldPanel('upload_baa'),
                    FieldPanel('invoice_number'),
                    ])
                ]),
            FieldPanel('notes'),
            ]
    """

    def get_edit_handler(self):
        basic_panels = [
            FieldPanel("name", read_only=True),
            FieldPanel("network", read_only=True),
            FieldPanel("address", read_only=True),
            FieldRowPanel(
                [
                    FieldPanel("online_at", read_only=True),
                    FieldPanel("offline_at", read_only=True),
                ]
            ),
        ]

        sales_panels = MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("links"),
                        MultiFieldPanel(
                            [
                                FieldPanel("upload_baa"),
                                FieldPanel("invoice_number", read_only=True),
                            ]
                        ),
                    ]
                ),
                FieldPanel("notes"),
            ]
        )

        finance_panels = MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("links", read_only=True),
                        MultiFieldPanel(
                            [
                                FieldPanel("upload_baa", read_only=True),
                                FieldPanel("invoice_number"),
                            ]
                        ),
                    ]
                ),
                FieldPanel("notes", read_only=True),
            ]
        )

        support_panels = MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("links", read_only=True),
                        MultiFieldPanel(
                            [
                                FieldPanel("upload_baa", read_only=True),
                                FieldPanel("invoice_number", read_only=True),
                            ]
                        ),
                    ]
                ),
                FieldPanel("notes", read_only=True),
            ]
        )

        user = get_current_user()

        try:
            group_support = Group.objects.get(name="Support")
        except ObjectDoesNotExist:
            group_support = []

        try:
            group_sales = Group.objects.get(name="Sales")
        except ObjectDoesNotExist:
            group_sales = []

        try:
            group_finance = Group.objects.get(name="Finance")
        except ObjectDoesNotExist:
            group_finance = []

        custom_panels = basic_panels
        if group_support in user.groups.all() or user.is_superuser:
            custom_panels.append(support_panels)

        if group_sales in user.groups.all():
            custom_panels.append(sales_panels)

        if group_finance in user.groups.all():
            custom_panels.append(finance_panels)

        return ObjectList(custom_panels)

    def get_list_display(self, request):
        if request.user.is_superuser:
            list_display = (
                "name_with_parameters",
                "address_multiline",
                "network_group",
                "online_at",
                "offline_at",
                "baa_file",
                "invoice_number",
                "notes",
            )
        else:
            list_display = (
                "name_with_parameters",
                "address_multiline",
                "network_group",
                "online_at",
                "offline_at",
                "baa_file",
                "invoice_number",
                "notes",
            )

        return list_display

    def get_queryset(self, request):
        # qs = Members.objects.none()
        if request.user.is_superuser:
            qs = Members.objects.all()
        else:
            networks = request.user.organization.networks.all()
            qs = Members.objects.filter(
                network__in=networks, offline_at__isnull=True
            ) | Members.objects.filter(
                network__in=networks, offline_at__gt=timezone.now()
            )

        return qs


modeladmin_register(MembersAdmin)
