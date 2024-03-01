from django.db.models import Count
import requests
from django.shortcuts import render
from django.utils import timezone
from accounts.models import User
from .models import Networks


class get_networks_by_user(requests, user_id):
    user = User.objects.get(id=user_id)

    if user.organization is None:
        networks = Networks.objects.all()
    else:
        nets_org = user.organization.network.all()
        for net_org in nets_org:
            net_org_count = 0
            net_org_count += Members.objects.filter(network__in=networks_org, offline_at__isnull=True).count()
            net_org_count += Members.objects.filter(network__in=networks_org, offline_at__gt=timezone.now()).count()
    
