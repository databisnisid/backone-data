import requests
from django.core.exceptions import ObjectDoesNotExist
from .models import Networks


def get_networks(domain_api):
    current_networks_list = []
    response = []
    response_json = {}

    try:
        response = requests.get(domain_api + '/api/networks/list/')
        response_json = response.json()

        #print(response_json)

        current_networks_list = list(Networks.objects.values_list('network_id', flat=True))
        print(current_networks_list)

    except requests.exceptions.HTTPError as e:
        print(e.response.text)

    for resp_json in response_json:
        network_name=resp_json['fields']['name']
        network_description=resp_json['fields']['description']
        network_id=resp_json['fields']['network_id']

        try:
            network = Networks.objects.get(network_id=network_id)

        except ObjectDoesNotExist:
            print(resp_json['fields'])
            network = Networks()
            network.network_id = network_id

        try:
            current_networks_list.remove(network_id)
        except ValueError:
            pass

        network.name = network_name
        network.description = network_description
        network.save()

    # Delete network which not in the list from API
    if current_networks_list:
        print('Deleting Network:', current_networks_list)
        Networks.objects.filter(network_id__in=current_networks_list).delete()



