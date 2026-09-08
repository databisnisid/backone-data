import logging
import requests
from django.core.exceptions import ObjectDoesNotExist
from .models import Networks

logger = logging.getLogger(__name__)


def get_networks(domain_api):
    response_json = []

    try:
        response = requests.get(domain_api + '/api/networks/list/')
        response_json = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.warning("Sync aborted: %s", e)
        return

    if not isinstance(response_json, list) or len(response_json) == 0:
        logger.warning("Sync aborted: empty or invalid API response")
        return

    current_networks_list = list(Networks.objects.values_list('network_id', flat=True))

    for resp_json in response_json:
        network_name=resp_json['fields']['name']
        network_description=resp_json['fields']['description']
        network_id=resp_json['fields']['network_id']

        try:
            network = Networks.objects.get(network_id=network_id)

        except ObjectDoesNotExist:
            logger.info("Creating new network: %s", resp_json['fields'])
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
        logger.info("Deleting Network: %s", current_networks_list)
        Networks.objects.filter(network_id__in=current_networks_list).delete()
