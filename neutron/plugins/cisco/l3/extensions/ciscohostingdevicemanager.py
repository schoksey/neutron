# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 OpenStack Foundation.
# All rights reserved.
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

from abc import ABCMeta
from abc import abstractmethod

from oslo.config import cfg
import six

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron.api.v2 import resource_helper
from neutron.common import constants as const
from neutron.common import exceptions as qexception
from neutron import manager
from neutron.openstack.common import importutils
from neutron.openstack.common import uuidutils
from neutron.plugins.common import constants


# Hosting device and hosting device template exceptions
class HostingDeviceInvalidPortValue(qexception.InvalidInput):
    message = _("Invalid value for port %(port)s")


class HostingDeviceInUse(qexception.InUse):
    message = _("Hosting device %(id)s in use.")


class HostingDeviceMgmtPortNotFound(qexception.InUse):
    message = _("Specified management port %(id)s does not exist.")


class HostingDeviceNotFound(qexception.NotFound):
    message = _("Hosting device %(id)s does not exist")


class HostingDeviceTemplateNotFound(qexception.NotFound):
    message = _("Hosting device template %(id)s does not exist")


class HostingDeviceTemplateInUse(qexception.InUse):
    message = _("Hosting device template %(id)s in use.")


class DriverNotFound(qexception.NetworkNotFound):
    message = _("Driver %(driver)s does not exist")


def convert_validate_port_value(port):
    if port is None:
        return port
    try:
        val = int(port)
    except (ValueError, TypeError):
        raise HostingDeviceInvalidPortValue(port=port)
    if val >= 0 and val <= 65535:
        return val
    else:
        raise HostingDeviceInvalidPortValue(port=port)


def convert_validate_driver(driver):
    if driver is None:
        raise DriverNotFound(driver=driver)
    try:
        # yes, this is a coarse-grained check...
        importutils.import_object(driver)
        return driver
    except ImportError:
        raise DriverNotFound(driver=driver)
    except:
        return driver


# Hosting device belong to one of the following categories:
VM_CATEGORY = 'VM'
HARDWARE_CATEGORY = 'Hardware'

HOSTING_DEVICE_MANAGER_ALIAS = 'cisco-hosting-device-manager'
DEVICE = 'hosting_device'
DEVICES = DEVICE + 's'
DEVICE_TEMPLATE = DEVICE + '_template'
DEVICE_TEMPLATES = DEVICE_TEMPLATE + 's'

# Attribute Map
RESOURCE_ATTRIBUTE_MAP = {
    DEVICES: {
        'tenant_id': {'allow_post': False, 'allow_put': False,
                      'is_visible': True},
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'template_id': {'allow_post': True, 'allow_put': False,
                        'is_visible': True, 'required_by_policy': True},
        'credentials_id': {'allow_post': True, 'allow_put': True,
                           'default': None, 'is_visible': True},
        'device_id': {'allow_post': True, 'allow_put': True,
                      'is_visible': True, 'default': None},
        'admin_state_up': {'allow_post': True, 'allow_put': True,
                           'default': True,
                           'convert_to': attr.convert_to_boolean,
                           'is_visible': True},
        'mgmt_port_id': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:uuid': None}, 'is_visible': True,
                         'required_by_policy': True},
        'protocol_port': {'allow_post': True, 'allow_put': False,
                          'convert_to': convert_validate_port_value,
                          'default': None, 'is_visible': True},
        'cfg_agent_id': {'allow_post': True, 'allow_put': False,
                         'default': None, 'is_visible': True},
        'created_at': {'allow_post': False, 'allow_put': False,
                       'is_visible': True},
        'booting_time': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:non_negative': 0},
                         'convert_to': attr.convert_to_int,
                         'default': None, 'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'default': None, 'is_visible': True},
        'tenant_bound': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:uuid_or_none': None},
                         'default': None, 'is_visible': True},
        'auto_delete_on_fail': {'allow_post': True, 'allow_put': True,
                                'default': True,
                                'convert_to': attr.convert_to_boolean},
    },
    DEVICE_TEMPLATES: {
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'is_visible': True},
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'is_visible': True, 'default': ''},
        'enabled': {'allow_post': True, 'allow_put': True,
                    'default': True, 'convert_to': attr.convert_to_boolean},
        'host_category': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:values': [VM_CATEGORY,
                                                       HARDWARE_CATEGORY]},
                          'required_by_policy': True, 'is_visible': True},
        #TODO(bobmel): validate service_types
        'service_types': {'allow_post': True, 'allow_put': True,
                          'is_visible': True, 'default': ''},
        'image': {'allow_post': True, 'allow_put': True,
                  'default': None, 'is_visible': True},
        'flavor': {'allow_post': True, 'allow_put': True,
                   'default': None, 'is_visible': True},
        'configuration_mechanism': {'allow_post': True, 'allow_put': True,
                                    'is_visible': True},
        'protocol_port': {'allow_post': True, 'allow_put': True,
                          'convert_to': convert_validate_port_value,
                          'default': None, 'is_visible': True},
        'booting_time': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:non_negative': 0},
                         'convert_to': attr.convert_to_int,
                         'default': None, 'is_visible': True},
        'slot_capacity': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:non_negative': 0},
                          'convert_to': attr.convert_to_int,
                          'default': 0, 'is_visible': True},
        'desired_slots_free': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:non_negative': 0},
                               'convert_to': attr.convert_to_int,
                               'default': 0, 'is_visible': True},
        'tenant_bound': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:uuid_list': []},
                         'default': None, 'is_visible': True},
        'device_driver': {'allow_post': True, 'allow_put': False,
                          'convert_to': convert_validate_driver,
                          'required_by_policy': True,
                          'is_visible': True},
        'plugging_driver': {'allow_post': True, 'allow_put': False,
                            'convert_to': convert_validate_driver,
                            'required_by_policy': True,
                            'is_visible': True},
    }
}


class Ciscohostingdevice(extensions.ExtensionDescriptor):
    """Hosting device and template extension."""

    @classmethod
    def get_name(cls):
        return "Cisco hosting device manager"

    @classmethod
    def get_alias(cls):
        return HOSTING_DEVICE_MANAGER_ALIAS

    @classmethod
    def get_description(cls):
        return "Extension for manager of hosting devices and their templates"

    @classmethod
    def get_namespace(cls):
        # todo
        return ("http://docs.openstack.org/ext/" +
                HOSTING_DEVICE_MANAGER_ALIAS + "/api/v2.0")

    @classmethod
    def get_updated(cls):
        return "2014-03-31T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        attr.PLURALS.update(plural_mappings)
        return resource_helper.build_resource_info(plural_mappings,
                                                   RESOURCE_ATTRIBUTE_MAP,
                                                   constants.DEVICE_MANAGER)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(ABCMeta)
class CiscoHostingDevicePluginBase(object):

    @abstractmethod
    def create_hosting_device(self, context, hosting_device):
        pass

    @abstractmethod
    def update_hosting_device(self, context, id, hosting_device):
        pass

    @abstractmethod
    def delete_hosting_device(self, context, id):
        pass

    @abstractmethod
    def get_hosting_device(self, context, id, fields=None):
        pass

    @abstractmethod
    def get_hosting_devices(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        pass

    @abstractmethod
    def create_hosting_device_template(self, context,
                                       hosting_device_template):
        pass

    @abstractmethod
    def update_hosting_device_template(self, context,
                                       hosting_device_template):
        pass

    @abstractmethod
    def delete_hosting_device_template(self, context, id):
        pass

    @abstractmethod
    def get_hosting_device_template(self, context, id, fields=None):
        pass

    @abstractmethod
    def get_hosting_device_templates(self, context, filters=None, fields=None,
                                     sorts=None, limit=None, marker=None,
                                     page_reverse=False):
        pass