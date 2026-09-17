import logging
from urllib.parse import urlparse

import requests
from django.core.exceptions import ObjectDoesNotExist

from .models import Networks
from members.models import MemberLink

logger = logging.getLogger(__name__)


def _netloc(domain_api):
    """Host key for domain_api, e.g. 'manage.vn.backone.cloud'. Falls back to
    the raw string so a malformed URL still yields a stable, distinct key."""
    return urlparse(domain_api).netloc or domain_api


def get_networks(domain_api):
    domain = _netloc(domain_api)

    try:
        response = requests.get(domain_api + '/api/networks/list/')
        response_json = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.warning("Sync aborted: %s", e)
        return

    if not isinstance(response_json, list) or len(response_json) == 0:
        logger.warning("Sync aborted: empty or invalid API response")
        return

    # Only this domain's rows are deletion candidates: an id absent from THIS
    # API says nothing about a network owned by another upstream instance.
    current_networks_list = list(
        Networks.objects.filter(domain=domain).values_list('network_id', flat=True)
    )

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
        network.domain = domain
        network.save()

    # Delete network which not in the list from API
    if current_networks_list:
        logger.info("Deleting Network: %s", current_networks_list)
        # ponytail: pre-delete MemberLink because MySQL FK blocks the cascade
        # Networks -> Members -> MemberLink. Members themselves go with the
        # cascade; SPEC V3 says sync never deletes Members, so revisit if the
        # upstream is expected to retire networks that still hold sites.
        networks_to_delete = Networks.objects.filter(network_id__in=current_networks_list)
        MemberLink.objects.filter(member__network__in=networks_to_delete).delete()
        networks_to_delete.delete()
