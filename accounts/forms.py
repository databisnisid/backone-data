from django import forms
from wagtail.users.forms import UserEditForm, UserCreationForm
from .models import Organizations
from django.utils.translation import gettext_lazy as _


class CustomUserEditForm(UserEditForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects,
        required=True,
        label=_("Organization"),
        disabled=True,
    )

    """
    def save(self, commit=True):
        user = super().save(commit=False)
        user.organization = self.cleaned_data.get("organization")
        if commit:
            user.save()
            self.save_m2m()
        return user
    """

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"organization"}


class CustomUserCreationForm(UserCreationForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects,
        required=True,
        label=_("Organization"),
    )

    """
    def save(self, commit=True):
        user = super().save(commit=False)
        user.organization = self.cleaned_data.get("organization")
        if commit:
            user.save()
            self.save_m2m()
        return user
    """

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {"organization"}
