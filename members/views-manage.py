import random
from django.core.serializers import serialize
from django.http import HttpResponse
#from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
#from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
#from .models import Members, Mqtt
from .models import Members
from .utils import get_unique_members
from problems.models import MemberProblems


def randomize_coordinate(members):
    for i in range(0, len(members)):
        for j in range(i+1, len(members)):
            if members[i]['lat'] == members[j]['lat'] and members[i]['lng'] == members[j]['lng']:
                members[i]['lat'] = float(members[i]['lat']) + random.uniform(-0.0001, 0.0001)
                members[i]['lng'] = float(members[i]['lng']) + random.uniform(-0.0001, 0.0001)

    return members


def is_problem(member, members_problems):
    is_found = 0
    problem_string = ''

    if member.organization.features.is_nms:
        problem_array = []
        for problem in members_problems:
            if member.id == problem.member.id:
                is_found = 1
                problem_array.append(problem.problem.name)

        problem_string = ', '.join(problem_array)

    return is_found, problem_string


def is_new(member):
    am_i_new = True

    timedelta = timezone.now() - member.created_at
    if timedelta.total_seconds() > settings.MEMBER_NEW_PERIOD:
        am_i_new = False

    if member.online_at is not None: # If online_at is setup
        am_i_new = False

    return am_i_new


def prepare_data(members, members_problems):
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
        member_geo['ipaddress'] = member.ipaddress
        member_geo['lat'] = lat
        member_geo['lng'] = lng
        member_geo['is_online'] = 1 if member.is_online() else 0
        is_found, problem_string = is_problem(member, members_problems)
        member_geo['is_problem'] = is_found
        member_geo['problem_string'] = problem_string
        member_geo['is_new'] = 1 if is_new(member) else 0 
        member_geo['is_authorized'] = 1 if member.is_authorized else 0 
        new_members.append(member_geo)

    return randomize_coordinate(new_members)


def problem_time():
    return timezone.now() - timezone.timedelta(seconds=settings.MONITOR_DELAY)


def get_members_all(request):
    members = Members.objects.all()
    members_problems = MemberProblems.unsolved.filter(start_at__lt=problem_time())
    members_data = prepare_data(get_unique_members(members), members_problems)

    return JsonResponse(members_data, safe=False)

def get_members_user(request, user):
    members = Members.objects.filter(user__id=user)
    members_problems = MemberProblems.unsolved.filter(
            member__user__id=user, start_at__lt=problem_time()
            )
    members_data = prepare_data(get_unique_members(members), members_problems)

    return JsonResponse(members_data, safe=False)


def get_members_org(request, organization):
    members = Members.objects.filter(organization__id=organization)
    members_problems = MemberProblems.unsolved.filter(
            member__organization__id=organization, start_at__lt=problem_time()
            )
    members_data = prepare_data(get_unique_members(members), members_problems)

    return JsonResponse(members_data, safe=False)


'''
List Members by NetworkID
'''
def get_members_by_network(request, network_id):
    members = Members.objects.filter(
            network__network_id=network_id,
            online_at__isnull=False
            )
    data = serialize(
            "json", members, 
            fields=(
                'name', 'member_code', 'description', 
                'member_id', 'address', 'location',
                'online_at', 'offline_at'
                )
            )
    return HttpResponse(data, content_type="application/json")
    #return JsonResponse(members, safe=False)

