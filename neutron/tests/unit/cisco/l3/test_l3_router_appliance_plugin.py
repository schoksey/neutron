# Copyright 2014 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Bob Melander, Cisco Systems, Inc.

from oslo.config import cfg

from neutron import context
from neutron.extensions import external_net
from neutron.extensions import extraroute
from neutron.extensions import l3
from neutron.manager import NeutronManager
from neutron.openstack.common import log as logging
from neutron.openstack.common.notifier import api as notifier_api
from neutron.openstack.common.notifier import test_notifier
from neutron.plugins.cisco.common import cisco_constants as c_const
from neutron.plugins.cisco.extensions import routertype
from neutron.tests.unit.cisco.device_manager import device_manager_test_support
from neutron.tests.unit.cisco.device_manager import test_db_device_manager
from neutron.tests.unit.cisco.l3 import l3_router_test_support
from neutron.tests.unit.cisco.l3 import test_db_routertype
from neutron.tests.unit import test_extension_extraroute as test_ext_extraroute
from neutron.tests.unit import test_l3_plugin

LOG = logging.getLogger(__name__)


CORE_PLUGIN_KLASS = device_manager_test_support.CORE_PLUGIN_KLASS
L3_PLUGIN_KLASS = (
    "neutron.tests.unit.cisco.l3.test_l3_router_appliance_plugin."
    "TestApplianceL3RouterServicePlugin")


class TestApplianceL3RouterExtensionManager(
    test_db_routertype.L3TestRoutertypeExtensionManager):

    def get_resources(self):
        l3.RESOURCE_ATTRIBUTE_MAP['routers'].update(
            extraroute.EXTENDED_ATTRIBUTES_2_0['routers'])
        return super(TestApplianceL3RouterExtensionManager,
                     self).get_resources()


# A routertype and set routes capable L3 routing service plugin class
class TestApplianceL3RouterServicePlugin(
        l3_router_test_support.TestL3RouterServicePlugin):

    supported_extension_aliases = ["router", "extraroute",
                                   routertype.ROUTERTYPE_ALIAS]


class L3RouterApplianceTestCaseBase(
    test_ext_extraroute.ExtraRouteDBSepTestCase,
    test_db_routertype.RoutertypeTestCaseMixin,
    test_db_device_manager.DeviceManagerTestCaseMixin,
    l3_router_test_support.L3RouterTestSupportMixin,
        device_manager_test_support.DeviceManagerTestSupportMixin):

    resource_prefix_map = (test_db_device_manager.TestDeviceManagerDBPlugin
                           .resource_prefix_map)

    def setUp(self, core_plugin=None, l3_plugin=None, dm_plugin=None,
              ext_mgr=None):
        if not core_plugin:
            core_plugin = CORE_PLUGIN_KLASS
        if l3_plugin is None:
            l3_plugin = L3_PLUGIN_KLASS
        service_plugins = {'l3_plugin_name': l3_plugin}
        cfg.CONF.set_override('api_extensions_path',
                              l3_router_test_support.extensions_path)

        # for these tests we need to enable overlapping ips
        cfg.CONF.set_default('allow_overlapping_ips', True)
        cfg.CONF.set_default('max_routes', 3)
        ext_mgr = TestApplianceL3RouterExtensionManager()

        # call grandparent's setUp() to avoid that wrong plugin and
        # extensions are used.
        super(test_l3_plugin.L3BaseForSepTests, self).setUp(
            plugin=core_plugin, service_plugins=service_plugins,
            ext_mgr=ext_mgr)

        # Set to None to reload the drivers
        notifier_api._drivers = None
        cfg.CONF.set_override("notification_driver", [test_notifier.__name__])

        cfg.CONF.set_override('allow_sorting', True)
        test_opts = [
            cfg.StrOpt('auth_protocol', default='http'),
            cfg.StrOpt('auth_host', default='localhost'),
            cfg.IntOpt('auth_port', default=35357),
            cfg.StrOpt('admin_user', default='neutron'),
            cfg.StrOpt('admin_password', default='secrete')]
        cfg.CONF.register_opts(test_opts, 'keystone_authtoken')

        cfg.CONF.register_opt(
            cfg.BoolOpt('router_auto_schedule', default=True,
                        help=_('Allow auto scheduling of routers to '
                               'L3 agent.')))

        self._mock_l3_admin_tenant()
        self._create_mgmt_nw_for_tests(self.fmt)

    def tearDown(self):
        self._remove_mgmt_nw_for_tests()
        super(L3RouterApplianceTestCaseBase, self).tearDown()

    def test_get_network_succeeds_without_filter(self):
        plugin = NeutronManager.get_plugin()
        ctx = context.Context(None, None, is_admin=True)
        nets = plugin.get_networks(ctx, filters=None)
        # Remove mgmt network from list
        for i in xrange(len(nets)):
            if nets[i].get('id') == plugin.mgmt_nw_id():
                del nets[i]
                break
        self.assertEqual(nets, [])

    def test_list_nets_external(self):
        with self.network() as n1:
            self._set_net_external(n1['network']['id'])
            with self.network():
                body = self._list('networks')
                # 3 networks since there is also the mgmt network
                self.assertEqual(len(body['networks']), 3)

                body = self._list(
                    'networks', query_params="%s=True" % external_net.EXTERNAL)
                self.assertEqual(len(body['networks']), 1)

                body = self._list(
                    'networks',
                    query_params="%s=False" % external_net.EXTERNAL)
                # 2 networks since there is also the mgmt network
                self.assertEqual(len(body['networks']), 2)


class L3RouterApplianceNamespaceTestCase(L3RouterApplianceTestCaseBase):

    def setUp(self, core_plugin=None, l3_plugin=None, dm_plugin=None,
              ext_mgr=None):
        super(L3RouterApplianceNamespaceTestCase, self).setUp(
            core_plugin=core_plugin, l3_plugin=l3_plugin, dm_plugin=dm_plugin,
            ext_mgr=ext_mgr)

        cfg.CONF.set_override('default_router_type',
                              c_const.NAMESPACE_ROUTER_TYPE)

        templates = self._test_create_hosting_device_templates()
        self._test_create_routertypes(templates.values())

    def tearDown(self):
        plugin = NeutronManager.get_plugin()
        plugin.reset_all()

        self._test_remove_routertypes()
        self._test_remove_hosting_device_templates()
        super(L3RouterApplianceTestCaseBase, self).tearDown()


class L3RouterApplianceVMTestCase(L3RouterApplianceTestCaseBase):

    def setUp(self, core_plugin=None, l3_plugin=None, dm_plugin=None,
              ext_mgr=None):
        super(L3RouterApplianceVMTestCase, self).setUp(
            core_plugin=core_plugin, l3_plugin=l3_plugin, dm_plugin=dm_plugin,
            ext_mgr=ext_mgr)

        templates = self._test_create_hosting_device_templates()
        self._test_create_routertypes(templates.values())
        self._mock_svc_vm_create_delete()
        self._mock_get_routertype_scheduler_always_none()

    def tearDown(self):
        plugin = NeutronManager.get_plugin()
        plugin.delete_all_hosting_devices(context.get_admin_context(), True)
        plugin.reset_all()

        self._test_remove_routertypes()
        self._test_remove_hosting_device_templates()
        super(L3RouterApplianceTestCaseBase, self).tearDown()


class L3RouterApplianceTestCaseXML(L3RouterApplianceTestCaseBase):
    fmt = 'xml'