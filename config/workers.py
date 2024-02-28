from networks.utils import get_networks
from members.utils import get_members_all


def sync_data(domain_api):
    get_networks(domain_api)
    get_members_all(domain_api)


