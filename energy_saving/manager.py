import ConfigParser
import sys
import time
from energy_saving import client_wrapper
from energy_saving.policies.ratio import RatioPolicy
from energy_saving.policies.simple import SimplePolicy

CONFIG_FILE = "/home/ecs/config/ecs.conf"

def get_config(config_file):
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_file))
    return config

def validate_config(config):
    valid_policy = ['simple', 'ratio']
    if config.get('DEFAULT', 'policy') not in valid_policy:
        sys.exit()

    valid_interval = 1
    if int(config.get('DEFAULT', 'time_interval'))\
            < valid_interval:
        sys.exit()


def check(config, **kwargs):
    if 'simple' == config.get('DEFAULT', 'policy'):
        reservation = config.get('DEFAULT', 'reservation')
        policy = SimplePolicy(reservation)
        return policy.check(**kwargs)
    elif 'ratio' == config.get('DEFAULT', 'policy'):
        percent = config.get('ratio', 'percent')
        policy = RatioPolicy(percent)
        return policy.check(**kwargs)


def classify_node(ironic_client, nova_client):
    node_pool = {
        'on_with_vms_pool': [],
        'on_without_vms_pool': [],
        'off_with_vms_pool': [],
        'off_without_vms_pool': []
    }
    node_list = ironic_client.node.list(detail=True)
    for node in node_list:
        compute_node_id = int(node.to_dict()['extra'].get('compute_node_id'))
        running_vms =\
            nova_client.hypervisors.get(compute_node_id).to_dict().get('running_vms')

        if node.to_dict().get('power_state') == 'power on':
            if running_vms > 0:
                node_pool['on_with_vms_pool'].append(node.to_dict().get('uuid'))
            else:
                node_pool['on_without_vms_pool'].append(node.to_dict().get('uuid'))
        elif node.to_dict().get('power_state') == 'power off':
            if running_vms > 0:
                node_pool['off_with_vms_pool'].append(node.to_dict().get('uuid'))
            else:
                node_pool['off_without_vms_pool'].append(node.to_dict().get('uuid'))

    return node_pool


def power_action(check_result, node_pool, ironic_client):
    if not check_result:
        return

    for key, value in check_result.items():
        if key == 'power_on':
            for index in range(value):
                ironic_client.node.set_power_state(
                    node_pool.get('off_without_vms_pool')[-(index+1)],
                    'on'
                )
        else:
            for index in range(value):
                ironic_client.node.set_power_state(
                    node_pool.get('on_without_vms_pool')[-(index+1)],
                    'off'
                )



class EcsManager(object):

    def __init__(self):
        super(EcsManager, self).__init__()


    def start(self):
        config = get_config(CONFIG_FILE)

        validate_config(config)

        while True:
            ironic_client = \
                client_wrapper.IronicClientWrapper().get_client(config)
            nova_client = \
                client_wrapper.NovaClientWrapper().get_client(config)
            node_pool = classify_node(ironic_client, nova_client)

            node_info = {
                'on_with_vms': len(node_pool.get('on_with_vms_pool')),
                'on_without_vms': len(node_pool.get('on_without_vms_pool')),
                'off_with_vms': len(node_pool.get('off_with_vms_pool')),
                'off_without_vms': len(node_pool.get('off_without_vms_pool')),
            }

            check_result = check(config, **node_info)

            power_action(check_result, node_pool, ironic_client)

            time.sleep(config.get('DEFAULT', 'time_interval'))



