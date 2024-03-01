from django.contrib import admin
from .models import Members


class MembersAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_links']



admin.site.register(Members, MembersAdmin)

