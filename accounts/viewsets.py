from wagtail.users.views.users import (
    UserViewSet as WagtailUserViewSet,
    IndexView as WagtailIndexView,
)

from .forms import CustomUserCreationForm, CustomUserEditForm


class CustomUserIndexView(WagtailIndexView):

    def get_base_queryset(self):
        queryset = super().get_base_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)

        return queryset


class UserViewSet(WagtailUserViewSet):

    index_view_class = CustomUserIndexView

    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Apply your custom filtering here
        queryset = queryset.exclude(is_superuser=True)
        print(queryset)
        return queryset
