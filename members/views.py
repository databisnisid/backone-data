import random
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from accounts.models import User, Organizations
from .models import Members


def randomize_coordinate(members):
    for i in range(0, len(members)):
        for j in range(i+1, len(members)):
            if members[i]['lat'] == members[j]['lat'] and members[i]['lng'] == members[j]['lng']:
                members[i]['lat'] = float(members[i]['lat']) + random.uniform(-0.0001, 0.0001)
                members[i]['lng'] = float(members[i]['lng']) + random.uniform(-0.0001, 0.0001)

    return members


def prepare_data(members):
    new_members = []

    for member in members:
        member_geo = {}
        try:
            point = member.location.split(';')
            result = point[1].split(' ')
            lng = result[0].replace('POINT(', '')
            lat = result[1].replace(')', '')
        except AttributeError:
            lat = settings.GEO_WIDGET_DEFAULT_LOCATION['lat'] + random.uniform(-0.0025, 0.0025)
            lng = settings.GEO_WIDGET_DEFAULT_LOCATION['lng'] + random.uniform(-0.0025, 0.0025)

        member_geo['id'] = member.id
        member_geo['name'] = member.name
        member_geo['member_id'] = member.member_id
        member_geo['address'] = member.address
        member_geo['network'] = member.network.name
        member_geo['lat'] = lat
        member_geo['lng'] = lng

        # Online or Offline
        member_geo['is_online'] = 0
        if member.offline_at is None or member.offline_at <= timezone.now():
            member_geo['is_online'] = 1

        new_members.append(member_geo)

    return randomize_coordinate(new_members)


def get_members_by_user(request, user):
    user = User.objects.get(id=user)

    if user.organization is None:
        members = Members.objects.all()
    else:
        networks = user.organization.networks.all()
        members = Members.objects.filter(network__in=networks, offline_at__isnull=True) | Members.objects.filter(network__in=networks, offline_at__gt=timezone.now())

    members_data = prepare_data(members)

    return JsonResponse(members_data, safe=False)


