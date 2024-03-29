from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from wagtail.admin import urls as wagtailadmin_urls

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/members/', include('members.urls')),
    path('', include(wagtailadmin_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

