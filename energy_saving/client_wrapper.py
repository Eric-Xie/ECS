from novaclient import client as nova_client
from ironicclient import client as ironic_client

class IronicClientWrapper(object):

    def get_client(self, config):
        version = int(config.get('ironic', 'api_version'))
        kwargs = {'os_username': config.get('ironic', 'admin_username'),
                  'os_password': config.get('ironic', 'admin_password'),
                  'os_auth_url': config.get('ironic', 'admin_url'),
                  'os_tenant_name': config.get('ironic', 'admin_tenant_name'),
                  'os_service_type': 'baremetal',
                  'os_endpoint_type': 'public',
                  'ironic_url': config.get('ironic', 'api_endpoint')}
        return ironic_client.get_client(version, **kwargs)

class NovaClientWrapper(object):

    def get_client(self, config):
        version = int(config.get('nova', 'api_version'))
        args = [
            config.get('nova', 'admin_username'),
            config.get('nova', 'admin_password'),
            config.get('nova', 'admin_tenant_name')
        ]
        kwargs = {
            'auth_url': config.get('nova', 'auth_url')
        }
        return nova_client.Client(version, *args, **kwargs)

