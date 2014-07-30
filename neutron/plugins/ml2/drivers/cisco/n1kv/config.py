# Copyright 2014 OpenStack Foundation
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
#
# @author: Abhishek Raut (abhraut@cisco.com), Cisco Systems Inc.

from oslo.config import cfg


n1kv_opts = [
    cfg.StrOpt('n1kv_vsm_ip'
               help=_("IP Address of the Cisco Nexus1000V VSM")),
    cfg.StrOpt('n1kv_username'
               help=_("Username for the Cisco Nexus1000V VSM")),
    cfg.StrOpt('n1kv_password'
               help=_("Password for the Cisco Nexus1000V VSM"), secret=True),
    cfg.StrOpt('default_vlan_network_profile', default='default-vlan-np',
               help=_("Cisco Nexus1000V default network profile for VLAN "
                      "networks")),
    cfg.StrOpt('default_vxlan_network_profile', default='default-vxlan-np',
               help=_("Cisco Nexus1000V default network profile for VXLAN "
                      "networks")),
    cfg.StrOpt('default_policy_profile', default='default-pp',
               help=_("Cisco Nexus1000V default policy profile")),
    cfg.IntOpt('http_timeout', default=15,
               help=_("HTTP timeout, in seconds, for connections to the "
                      "Nexus1000V VSM")),
]


cfg.CONF.register_opts(n1kv_opts, "ml2_cisco_n1kv")
