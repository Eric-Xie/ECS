import os
from cmd import ecs
import unittest
import multiprocessing

import mock
import ConfigParser
from energy_saving import manager
from energy_saving.policies import simple
from energy_saving.policies import ratio
from ironicclient import client as ironic_client
from ironicclient.v1 import node as ironic_node
from novaclient.v2 import hypervisors
from energy_saving import client_wrapper


def create_fake_ironic_nodes():
    node1 = ironic_node.Node(ironic_node.NodeManager,
                            info={"uuid": "fake-uuid-1",
                            "power_state": "power on",
                            "extra": {
                                "compute_node_id": "1"
                            }},
                            loaded=True)
    node2 = ironic_node.Node(ironic_node.NodeManager,
                             info={"uuid": "fake-uuid-2",
                            "power_state": "power on",
                            "extra": {
                                "compute_node_id": "2"
                            }},
                             loaded=True)
    node3 = ironic_node.Node(ironic_node.NodeManager,
                             info={"uuid": "fake-uuid-3",
                            "power_state": "power off",
                            "extra": {
                                "compute_node_id": "3"
                            }},
                             loaded=True)
    node4 = ironic_node.Node(ironic_node.NodeManager,
                             info={"uuid": "fake-uuid-4",
                            "power_state": "power off",
                            "extra": {
                                "compute_node_id": "4"
                            }},
                             loaded=True)
    return [node1, node2, node3, node4]


def select_fake_nova_nodes(compute_node_id):
    hypervisor1 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager,
        info={
            "running_vms": 1,
            "id": 1
        },
        loaded=True
    )
    hypervisor2 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager,
        info={
            "running_vms": 0,
            "id": 2
        },
        loaded=True
    )
    hypervisor3 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager,
        info={
            "running_vms": 1,
            "id": 3
        },
        loaded=True
    )
    hypervisor4 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager,
        info={
            "running_vms": 0,
            "id": 4
        },
        loaded=True
    )
    hypervisor_list = [hypervisor1, hypervisor2, hypervisor3, hypervisor4]
    for hypervisor in hypervisor_list:
        if hypervisor.to_dict().get('id') == compute_node_id:
            return hypervisor


class EcsServiceTestCase(unittest.TestCase):

    @mock.patch.object(multiprocessing.process.Process, 'start')
    def test_ecs_service_start(self, mock_start):
        ecs.main()
        self.assertTrue(mock_start.called)

class EcsConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.fake_config_file = "./fake_config.conf"
        self._create_fake_config(self.fake_config_file)

    def tearDown(self):
        os.remove(self.fake_config_file)

    def _create_fake_config(self, fake_config_file):
        config = ConfigParser.ConfigParser()
        config.read(fake_config_file)
        config.set('DEFAULT', 'test', 'fake')
        config.write(open(fake_config_file, 'w'))

    def test_get_config(self):
        config = manager.get_config(self.fake_config_file)
        self.assertEqual(config.get('DEFAULT', 'test'), 'fake')

    @mock.patch("sys.exit")
    def test_validate_config_with_policy(self, mock_exit):
        config = ConfigParser.ConfigParser()
        config.read(self.fake_config_file)
        config.set('DEFAULT', 'policy', 'simple')
        config.set('DEFAULT', 'time_interval', '60')
        config.write(open(self.fake_config_file, 'w'))
        config = manager.get_config(self.fake_config_file)
        manager.validate_config(config)
        self.assertTrue(not mock_exit.called)

        config.set('DEFAULT', 'policy', 'invalid')
        config.write(open(self.fake_config_file, 'w'))
        config = manager.get_config(self.fake_config_file)
        manager.validate_config(config)
        self.assertTrue(mock_exit.called)

    @mock.patch("sys.exit")
    def test_validate_config_with_time_interval(self, mock_exit):
        config = ConfigParser.ConfigParser()
        config.read(self.fake_config_file)
        config.set('DEFAULT', 'policy', 'simple')
        config.set('DEFAULT', 'time_interval', '60')
        config.write(open(self.fake_config_file, 'w'))
        config = manager.get_config(self.fake_config_file)
        manager.validate_config(config)
        self.assertTrue(not mock_exit.called)

        config.set('DEFAULT', 'time_interval', '0')
        config.write(open(self.fake_config_file, 'w'))
        config = manager.get_config(self.fake_config_file)
        manager.validate_config(config)
        self.assertTrue(mock_exit.called)

class IronicNovaClientTestCase(unittest.TestCase):

    def setUp(self):
        self.fake_config_file = "./fake_config.conf"
        self._create_fake_config(self.fake_config_file)

    def tearDown(self):
        os.remove(self.fake_config_file)

    def _create_fake_config(self, fake_config_file):
        config = ConfigParser.ConfigParser()
        config.read(fake_config_file)
        config.set('DEFAULT', 'test', 'fake')
        config.write(open(fake_config_file, 'w'))

    def _create_ironic_config(self):
        config = ConfigParser.ConfigParser()
        config.read(self.fake_config_file)
        config.add_section('ironic')
        config.set('ironic', 'api_version', '1')
        config.set('ironic', 'admin_username', 'fake-user')
        config.set('ironic', 'admin_password', 'fake-password')
        config.set('ironic', 'admin_url', 'http://127.0.0.1:5000/')
        config.set('ironic', 'admin_tenant_name', 'services')
        config.set('ironic', 'api_endpoint', 'http://127.0.0.1:6385/')
        config.write(open(self.fake_config_file, 'w'))

    @mock.patch.object(ironic_client, 'get_client')
    def test_get_ironic_client(self, mock_client):
        self._create_ironic_config()
        config = manager.get_config(self.fake_config_file)
        client_wrapper.IronicClientWrapper().get_client(config)
        expected = {'os_username': config.get('ironic', 'admin_username'),
                    'os_password': config.get('ironic', 'admin_password'),
                    'os_auth_url': config.get('ironic', 'admin_url'),
                    'os_tenant_name': config.get('ironic', 'admin_tenant_name'),
                    'os_service_type': 'baremetal',
                    'os_endpoint_type': 'public',
                    'ironic_url': config.get('ironic', 'api_endpoint')}
        mock_client.assert_called_once_with(int(config.get('ironic', 'api_version')),
                                            **expected)

    def _create_nova_config(self):
        config = ConfigParser.ConfigParser()
        config.read(self.fake_config_file)
        config.add_section('nova')
        config.set('nova', 'api_version', '2')
        config.set('nova', 'admin_username', 'fake-user')
        config.set('nova', 'admin_password', 'fake-password')
        config.set('nova', 'auth_url', 'http://127.0.0.1:35357/v2.0')
        config.set('nova', 'admin_tenant_name', 'services')
        config.write(open(self.fake_config_file, 'w'))

    @mock.patch('novaclient.client.Client')
    def test_get_nova_client(self, mock_client):
        self._create_nova_config()
        config = manager.get_config(self.fake_config_file)
        client_wrapper.NovaClientWrapper().get_client(config)
        expected_args = [config.get('nova', 'admin_username'),
                    config.get('nova', 'admin_password'),
                    config.get('nova', 'admin_tenant_name')]
        expected_kwargs = {'auth_url': config.get('nova', 'auth_url')}
        mock_client.assert_called_once_with(int(config.get('nova', 'api_version')),
                                            *expected_args, **expected_kwargs)

    @mock.patch.object(client_wrapper.NovaClientWrapper, 'get_client')
    @mock.patch.object(client_wrapper.IronicClientWrapper, 'get_client')
    def test_get_node_info(self, mock_ironic_client, mock_nova_client):
        m = mock.Mock()
        m.node.list.return_value = create_fake_ironic_nodes()
        mock_ironic_client = m

        m_nova = mock.Mock()
        m_nova.hypervisors.get.side_effect = select_fake_nova_nodes
        mock_nova_client = m_nova

        self.assertEqual({
            'on_with_vms_pool': ['fake-uuid-1'],
            'on_without_vms_pool': ['fake-uuid-2'],
            'off_with_vms_pool': ['fake-uuid-3'],
            'off_without_vms_pool': ['fake-uuid-4']
        }, manager.classify_node(
            mock_ironic_client,
            mock_nova_client
        ))


class SimplePolicyTestCase(unittest.TestCase):

    def test_simple_policy_check_with_default_reservation(self):
        simple_policy = simple.SimplePolicy()

        fake_hosts_dict = {'on_without_vms': 2,
                           'off_without_vms': 1}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_off': 1}, result)

        fake_hosts_dict = {'on_without_vms': 1,
                           'off_without_vms': 1}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({}, result)

    def test_simple_policy_check_with_appointed_reservation(self):
        simple_policy = simple.SimplePolicy(reservation=3)

        fake_hosts_dict = {'on_without_vms': 4,
                           'off_without_vms': 1}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_off': 1}, result)

        fake_hosts_dict = {'on_without_vms': 3,
                           'off_without_vms': 1}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({}, result)

        fake_hosts_dict = {'on_without_vms': 1,
                           'off_without_vms': 2}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_on': 2}, result)

        fake_hosts_dict = {'on_without_vms': 1,
                           'off_without_vms': 1}
        result = simple_policy.check(**fake_hosts_dict)
        self.assertEqual({}, result)


class RatioPolicyTestCase(unittest.TestCase):

    def test_ratio_policy_check_with_default(self):
        ratio_policy = ratio.RatioPolicy()

        fake_hosts_dict = {
            'on_with_vms': 2,
            'on_without_vms': 3,
            'off_without_vms': 4
        }
        result = ratio_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_off': 3}, result)


    def test_ratio_policy_check_with_appointed_percent(self):
        ratio_policy = ratio.RatioPolicy(percent='50')

        fake_hosts_dict = {
            'on_with_vms': 2,
            'on_without_vms': 3,
            'off_without_vms': 4
        }
        result = ratio_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_off': 2}, result)

        fake_hosts_dict = {
            'on_with_vms': 2,
            'on_without_vms': 1,
            'off_without_vms': 4
        }
        result = ratio_policy.check(**fake_hosts_dict)
        self.assertEqual({}, result)

        fake_hosts_dict = {
            'on_with_vms': 2,
            'on_without_vms': 0,
            'off_without_vms': 4
        }
        result = ratio_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_on': 1}, result)

        fake_hosts_dict = {
            'on_with_vms': 4,
            'on_without_vms': 0,
            'off_without_vms': 1
        }
        result = ratio_policy.check(**fake_hosts_dict)
        self.assertEqual({'power_on': 1}, result)


class EcsPowerActionTestCase(unittest.TestCase):

    @mock.patch.object(client_wrapper.IronicClientWrapper, 'get_client')
    def test_power_action_need_power_on(self, mock_client):
        fake_check_result = {'power_on': 2}
        fake_node_pool = {
            'off_without_vms_pool': ['fake-uuid-1',
                                     'fake-uuid-2',
                                     'fake-uuid-3',
                                     'fake-uuid-4']
        }
        manager.power_action(fake_check_result, fake_node_pool, mock_client)
        self.assertEqual(2, mock_client.node.set_power_state.call_count)


    @mock.patch.object(client_wrapper.IronicClientWrapper, 'get_client')
    def test_power_action_need_power_off(self, mock_client):
        fake_check_result = {'power_off': 1}
        fake_node_pool = {
            'on_without_vms_pool': ['fake-uuid-1',
                                     'fake-uuid-2',
                                     'fake-uuid-3',
                                     'fake-uuid-4']
        }
        manager.power_action(fake_check_result, fake_node_pool, mock_client)
        mock_client.node.set_power_state.assert_called_with(
            'fake-uuid-4', 'off'
        )
        self.assertEqual(1, mock_client.node.set_power_state.call_count)



if __name__ == '__main__':
    unittest.main()


