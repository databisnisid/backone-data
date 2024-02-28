from django.urls import path
from .views import get_members_by_user


urlpatterns = [
        path('get_by_user/<int:user>/', get_members_by_user, name='get-members-by-user'),
        ]
        
