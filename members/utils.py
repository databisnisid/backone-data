import requests
from django.core.exceptions import ObjectDoesNotExist
from .models import Networks, Members


def get_members_by_net(domain_api, network_id):

    try:
        network = Networks.objects.get(network_id=network_id)

        response = []
        response_json = {}

        try:
            #response = requests.get(domain_api + '/api/members/get_by_net/' + network_id + '/')
            response = requests.get(domain_api + '/api/members/get_by_net_mqtt/' + network_id + '/')
            response_json = response.json()

            #print(response_json)

        except requests.exceptions.HTTPError as e:
            print(e.response.text)

        for resp_json in response_json:
            member_name=resp_json['name']
            member_code=resp_json['member_code']
            member_description=resp_json['description']
            member_id=resp_json['member_id']
            member_address=resp_json['address']
            member_location=resp_json['location']
            member_online_at=resp_json['online_at']
            member_offline_at=resp_json['offline_at']
            member_service_line=resp_json['mobile_number_first']

            try:
                member_quota_string=resp_json['mqtt']['quota_first']
            except TypeError:
                member_quota_string=''

            '''
            member_name=resp_json['fields']['name']
            member_code=resp_json['fields']['member_code']
            member_description=resp_json['fields']['description']
            member_id=resp_json['fields']['member_id']
            member_address=resp_json['fields']['address']
            member_location=resp_json['fields']['location']
            member_online_at=resp_json['fields']['online_at']
            member_offline_at=resp_json['fields']['offline_at']
            member_service_line=resp_json['fields']['mobile_number_first']
            '''


            try:
                member = Members.objects.get(member_id=member_id)

            except ObjectDoesNotExist:
                print(resp_json)
                member = Members()
                member.member_id = member_id

            member.name = member_name
            member.member_code = member_code
            member.description = member_description
            member.address = member_address
            member.location = member_location
            member.online_at = member_online_at
            member.offline_at = member_offline_at
            member.service_line = member_service_line
            member.network = network
            member.quota_string = member_quota_string
            member.save()

    except ObjectDoesNotExist:
        pass


def get_members_all(domain_api):
    networks = Networks.objects.all()

    for network in networks:
        print('NetworkID: ', network.network_id)
        get_members_by_net(domain_api, network.network_id)


