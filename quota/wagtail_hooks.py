from crum import get_current_user
from django.core.exceptions import ObjectDoesNotExist
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel, ObjectList
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from django.contrib.auth.models import Group
from .models import MembersDpi, MembersStarlink


class QuotaDpiViewSet(SnippetViewSet):
    model = MembersDpi
    menu_label = 'Siab GSM'
    menu_icon = 'tablet-alt'
    inspect_view_enabled = False
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('service_line', 'get_quota_current', 'get_quota_day', 'name')
    search_fields = ('name', 'service_line', 'quota_string')
    list_per_page = 100

    def get_queryset(self, request):
        if request.user.is_superuser:
            qs = MembersDpi.objects.all()
        else:
            networks = request.user.organization.networks.all()
            qs = MembersDpi.objects.filter(
                network__in=networks, offline_at__isnull=True
            ) | MembersDpi.objects.filter(
                network__in=networks, offline_at__gt=timezone.now()
            )
        return qs

    def user_can_create(self, request):
        return False

    def user_can_delete_obj(self, request, obj):
        return False

    def user_can_edit_obj(self, request, obj):
        return False


class QuotaStarlinkViewSet(SnippetViewSet):
    model = MembersStarlink
    menu_label = 'Starlink'
    menu_icon = 'site'
    inspect_view_enabled = False
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('service_line', 'get_quota_usage', 'get_quota_current', 'get_quota_day', 'name')
    search_fields = ('name', 'service_line', 'quota_string')
    list_per_page = 100

    def get_queryset(self, request):
        if request.user.is_superuser:
            qs = MembersStarlink.objects.all()
        else:
            networks = request.user.organization.networks.all()
            qs = MembersStarlink.objects.filter(
                network__in=networks, offline_at__isnull=True
            ) | MembersStarlink.objects.filter(
                network__in=networks, offline_at__gt=timezone.now()
            )
        return qs

    def user_can_create(self, request):
        return False

    def user_can_delete_obj(self, request, obj):
        return False

    def user_can_edit_obj(self, request, obj):
        return False


class QuotaViewSetGroup(SnippetViewSetGroup):
    items = (QuotaDpiViewSet, QuotaStarlinkViewSet)
    menu_label = 'Quota'
    menu_icon = 'placeholder'
    add_to_admin_menu = True
    menu_order = 400


register_snippet(QuotaViewSetGroup)
