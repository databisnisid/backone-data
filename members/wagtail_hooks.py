from crum import get_current_user
from django.core.exceptions import ObjectDoesNotExist
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.snippets.models import register_snippet
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
from .models import Members, SdwanPackage, BaaStatus, LinkRole


class MembersViewSet(SnippetViewSet):
    model = Members
    menu_label = 'Sites'
    menu_icon = 'globe'
    inspect_view_enabled = True
    add_to_admin_menu = True
    add_to_settings_menu = False
    menu_order = 100
    list_display = (
        'service_line',
        'member_id',
        'name',
        'network',
        'get_quota_current',
        'get_quota_day',
        'get_quota_type',
        'get_quota_usage',
    )
    list_export = list_display
    search_fields = ('name', 'member_id', 'network__name', 'service_line')
    list_per_page = 25

    def get_edit_handler(self):
        basic_panels = [
            FieldPanel('service_line'),
            FieldPanel('name'),
            FieldPanel('member_id'),
            FieldPanel('address'),
            FieldPanel('upload_baa'),
            FieldPanel('invoice_number'),
        ]

        tabs = [
            ObjectList(basic_panels, heading='Profile'),
        ]

        user = get_current_user()
        if user is not None and user.is_superuser:
            tabs.append(
                ObjectList(
                    [
                        MultiFieldPanel(
                            [
                                FieldPanel('network'),
                                FieldPanel('links'),
                                FieldPanel('quota_string'),
                            ],
                            heading='Network & Quota',
                        ),
                    ],
                    heading='Network',
                )
            )

            tabs.append(
                ObjectList(
                    [
                        MultiFieldPanel(
                            [
                                GeoAddressPanel('location'),
                                GoogleMapsPanel('location'),
                            ],
                            heading='Location',
                        ),
                    ],
                    heading='Location',
                )
            )
        else:
            tabs.append(
                ObjectList(
                    [
                        MultiFieldPanel(
                            [
                                FieldPanel('network', read_only=True),
                                FieldPanel('links', read_only=True),
                            ],
                            heading='Network & Quota',
                        ),
                    ],
                    heading='Network',
                )
            )
            tabs.append(
                ObjectList(
                    [
                        GoogleMapsPanel('location'),
                    ],
                    heading='Location',
                )
            )
        return ObjectList(tabs).bind_to_model(self.model)


    def get_list_display(self, request):
        list_display = (
            'service_line',
            'member_id',
            'name',
            'network',
            'get_quota_current',
            'get_quota_day',
            'get_quota_type',
            'get_quota_usage',
        )

        return list_display

    def get_queryset(self, request):
        if (
            request.user.is_superuser
            or request.user.groups.filter(name='External').exists()
            or request.user.groups.filter(name='External Network').exists()
        ):
            return Members.objects.all()
        else:
            try:
                networks = request.user.organization.networks.all()
            except ObjectDoesNotExist:
                networks = []
            qs = Members.objects.filter(
                network__in=networks, offline_at__isnull=True
            ) | Members.objects.filter(
                network__in=networks, offline_at__gt=timezone.now()
            )
            return qs

    def user_can_create(self, request):
        return False

    def user_can_delete_obj(self, request, obj):
        return request.user.is_superuser


register_snippet(MembersViewSet)


class SdwanPackageViewSet(SnippetViewSet):
    model = SdwanPackage
    menu_label = "SDWAN Packages"
    menu_icon = "tag"
    add_to_admin_menu = False
    menu_order = 301
    list_display = ("name",)
    search_fields = ("name",)
    list_per_page = 100
    panels = [FieldPanel("name")]

    def user_can_delete_obj(self, request, obj):
        return False


class BaaStatusViewSet(SnippetViewSet):
    model = BaaStatus
    menu_label = "BAA Statuses"
    menu_icon = "tag"
    add_to_admin_menu = False
    menu_order = 302
    list_display = ("name",)
    search_fields = ("name",)
    list_per_page = 100
    panels = [FieldPanel("name")]

    def user_can_delete_obj(self, request, obj):
        return False


class LinkRoleViewSet(SnippetViewSet):
    model = LinkRole
    menu_label = "Link Roles"
    menu_icon = "tag"
    add_to_admin_menu = False
    menu_order = 303
    list_display = ("name",)
    search_fields = ("name",)
    list_per_page = 100
    panels = [FieldPanel("name")]

    def user_can_delete_obj(self, request, obj):
        return False


class LookupTablesGroup(SnippetViewSetGroup):
    items = (SdwanPackageViewSet, BaaStatusViewSet, LinkRoleViewSet)
    menu_label = "Lookup Tables"
    menu_icon = "cog"
    add_to_settings_menu = True


register_snippet(LookupTablesGroup)
