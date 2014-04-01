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

import eventlet
import math
import threading

from keystoneclient import exceptions as k_exceptions
from keystoneclient.v2_0 import client as k_client
from oslo.config import cfg
from sqlalchemy import func
from sqlalchemy.orm import exc
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import expression as expr

from neutron.common import exceptions as n_exc
from neutron.common import utils
from neutron import context as neutron_context
from neutron import manager
from neutron.openstack.common import excutils
from neutron.openstack.common import log as logging
from neutron.openstack.common import timeutils
from neutron.plugins.cisco.l3.common import constants as cl3_const
from neutron.plugins.cisco.l3.db.l3_models import HostingDevice
from neutron.plugins.cisco.l3.db.l3_models import HostingDeviceTemplate
from neutron.plugins.cisco.l3.extensions import ciscohostingdevicemanager
from neutron.plugins.common import constants as svc_constants

LOG = logging.getLogger(__name__)


class HostingDeviceDBMixin(CiscoHostingDevicePluginBase,
                           base_db.CommonDbMixin):
    """A class implementing DB functionality for hosting devices."""

    def create_hosting_device(self, context, hosting_device):
        LOG.debug(_("create_hosting_device() called"))
        hd = hosting_device['hosting_device']
        tenant_id = self._get_tenant_id_for_create(context, hd)
        birth_date = hd.get('created_at', timeutils.utcnow())
        with context.session.begin(subtransactions=True):
            hd_db = HostingDevice(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant,
                template_id=hd['template_id'],
                credentials_id=hd['credentials_id'],
                device_id=hd['device_id'],
                admin_state_up=hd['admin_state_up'],
                mgmt_port_id=hd['mgmt_port_id'],
                protocol_port=hd['protocol_port'],
                cfg_agent_id=hd['cfg_agent_id'],
                created_at=birth_date,
                booting_time=hd['booting_time'],
                status=svc_constants.ACTIVE,
                tenant_bound=hd['tenant_bound'],
                auto_delete_on_fail=hd['auto_delete_on_fail'])
            context.session.add(hd_db)
        return self._make_hosting_device_dict(hd_db)

    def update_hosting_device(self, context, id, hosting_device):
        LOG.debug(_("update_hosting_device() called"))
        hd = hosting_device['hosting_device']
        with context.session.begin(subtransactions=True):
            #TODO(bobmel): handle tenant_bound changes
            hd_query = context.session.query(
                HostingDevice).with_lockmode('update')
            hd_db = hd_query.filter_by(id=id).one()
            hd_db.update(hd)
            #TODO(bobmel): notify_agent on changes to credentials,
            # admin_state_up, booting_time, tenant_bound
        return self._make_hosting_device_dict(hd_db)

    def delete_hosting_device(self, context, id):
        LOG.debug(_("delete_hosting_device() called"))
        with context.session.begin(subtransactions=True):
            hd_query = context.session.query(
                HostingDevice).with_lockmode('update')
            hd_db = hd_query.filter_by(id=id).one()
             #TODO(bobmel): ensure no slots are allocated
            context.session.delete(hd_db)
        pass

    def get_hosting_device(self, context, id, fields=None):
        LOG.debug(_("get_hosting_device() called"))
        hd_db = self._get_hosting_device(context, id)
        return self._make_hosting_device_dict(hd_db)

    def get_hosting_devices(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        LOG.debug(_("get_hosting_devices() called"))
        return self._get_collection(context, HostingDevice,
                                    self._make_hosting_device_dict,
                                    filters=filters, fields=fields)

    def create_hosting_device_template(self, context, hosting_device_template):
        LOG.debug(_("create_hosting_device_template() called"))
        hdt = hosting_device_template['hosting_device_template']
        tenant_id = self._get_tenant_id_for_create(context, hdt)
        #TODO(bobmel): check service types
        with context.session.begin(subtransactions=True):
            hdt_db = HostingDeviceTemplate(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant,
                name=hdt['name'],
                enabled=hdt['enabled'],
                host_category=hdt['host_category'],
                service_types=hdt['service_types'],
                image=hdt['image'],
                flavor=hdt['flavor'],
                configuration_mechanism=hdt['configuration_mechanism'],
                protocol_port=hdt['protocol_port'],
                booting_time=hdt['booting_time'],
                slot_capacity=hdt['slot_capacity'],
                desired_slots_free=hdt['desired_slots_free'],
                tenant_bound=hdt['tenant_bound'],
                device_driver=hdt['device_driver'],
                plugging_driver=hdt['plugging_driver'])
            context.session.add(hdt_db)
        return self._make_hosting_device_template_dict(hdt_db)

    def update_hosting_device_template(self, context, hosting_device_template):
        LOG.debug(_("update_hosting_device_template() called"))
        hdt = hosting_device_template['hosting_device_template']
        with context.session.begin(subtransactions=True):
            hdt_query = context.session.query(
                HostingDeviceTemplate).with_lockmode('update')
            hdt_db = hdt_query.filter_by(id=id).one()
            hdt_db.update(hd)
        return self._make_hosting_device_template_dict(hdt_db)

    def delete_hosting_device_template(self, context, id):
        LOG.debug(_("delete_hosting_device_template() called"))
        with context.session.begin(subtransactions=True):
            hd_query = context.session.query(HostingDevice)
            if hd_query.filter_by(id=id).first() is not None:
                raise ciscohostingdevicemanager.HostingDeviceTemplateInUse(
                    id=id)
            hdt_query = context.session.query(
                HostingDeviceTemplate).with_lockmode('update')
            hdt_db = hdt_query.filter_by(id=id).one()
            context.session.delete(hdt_db)

    def get_hosting_device_template(self, context, id, fields=None):
        LOG.debug(_("get_hosting_device_template() called"))
        hdt_db = self._get_hosting_device_template(context, id)
        return self._make_hosting_device_template_dict(hdt_db)

    def get_hosting_device_templates(self, context, filters=None, fields=None,
                                     sorts=None, limit=None, marker=None,
                                     page_reverse=False):
        LOG.debug(_("get_hosting_device_templates() called"))
        return self._get_collection(context, HostingDeviceTemplate,
                                    self._make_hosting_device_template_dict,
                                    filters=filters, fields=fields)

    def _get_hosting_device(self, context, id):
        try:
            return self._get_by_id(context, HostingDevice, id)
        except exc.NoResultFound:
            raise ciscohostingdevicemanager.HostingDeviceNotFound(id=id)

    def _make_hosting_device_dict(self, hd, fields=None):
        res = {'id': hd['id'],
               'tenant_id': hd['tenant_id'],
               'template_id': hd['template_id'],
               'credentials_id': hd['credentials_id'],
               'device_id': hd['device_id'],
               'admin_state_up': hd['admin_state_up'],
               'management_port_id': hd['management_port_id'],
               'protocol_port': hd['protocol_port'],
               'cfg_agent_id': hd['cfg_agent_id'],
               'created_at': hd['created_at'],
               'booting_time': hd['booting_time'],
               'status': hd['status'],
               'tenant_bound': hd['tenant_bound'],
               'auto_delete_on_fail': hd['auto_delete_on_fail']}
        return self._fields(res, fields)

    def _get_hosting_device_template(self, context, id):
        try:
            return self._get_by_id(context, HostingDeviceTemplate, id)
        except exc.NoResultFound:
            raise ciscohostingdevicemanager.HostingDeviceTemplateNotFound(
                id=id)

    def _make_hosting_device_template_dict(self, hdt, fields=None):
        res = {'id': hdt['id'],
               'tenant_id': hdt['tenant_id'],
               'enabled': hdt['enabled'],
               'host_category': hdt['host_category'],
               'service_types': hdt['service_types'],
               'image': hdt['image'],
               'flavor': hdt['flavor'],
               'configuration_mechanism': hdt['configuration_mechanism'],
               'protocol_port': hdt['protocol_port'],
               'booting_time': hdt['booting_time'],
               'slot_capacity': hdt['slot_capacity'],
               'desired_slots_free': hdt['desired_slots_free'],
               'tenant_bound': hdt['tenant_bound'],
               'device_driver': hdt['device_driver'],
               'plugging_driver': hdt['plugging_driver']}
        return self._fields(res, fields)