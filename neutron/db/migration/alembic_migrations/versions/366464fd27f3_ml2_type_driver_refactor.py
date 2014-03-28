# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 OpenStack Foundation
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

"""ML2 Type driver refactor

Revision ID: 366464fd27f3
Revises: 8f682276ee4
Create Date: 2014-03-21 08:24:00.839630

"""

# revision identifiers, used by Alembic.
revision = '366464fd27f3'
down_revision = '8f682276ee4'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.plugins.ml2.plugin.Ml2Plugin'
]

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from neutron.db import migration


def upgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('agent_type', sa.String(length=255), nullable=False),
    sa.Column('binary', sa.String(length=255), nullable=False),
    sa.Column('topic', sa.String(length=255), nullable=False),
    sa.Column('host', sa.String(length=255), nullable=False),
    sa.Column('admin_state_up', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('heartbeat_timestamp', sa.DateTime(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('configurations', sa.String(length=4095), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('agent_type', 'host', name='uniq_agents0agent_type0host')
    )
    op.create_table('quotas',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=True),
    sa.Column('resource', sa.String(length=255), nullable=True),
    sa.Column('limit', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index('ix_quotas_tenant_id', 'quotas', ['tenant_id'], unique=False)
    op.create_table('networkdhcpagentbindings',
    sa.Column('network_id', sa.String(length=36), nullable=False),
    sa.Column('dhcp_agent_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dhcp_agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['network_id'], ['networks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('network_id', 'dhcp_agent_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('subnetroutes',
    sa.Column('destination', sa.String(length=64), nullable=False),
    sa.Column('nexthop', sa.String(length=64), nullable=False),
    sa.Column('subnet_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['subnet_id'], ['subnets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('destination', 'nexthop', 'subnet_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extradhcpopts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('port_id', sa.String(length=36), nullable=False),
    sa.Column('opt_name', sa.String(length=64), nullable=False),
    sa.Column('opt_value', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('port_id', 'opt_name', name='uidx_portid_optname')
    )
    op.create_table('routerroutes',
    sa.Column('destination', sa.String(length=64), nullable=False),
    sa.Column('nexthop', sa.String(length=64), nullable=False),
    sa.Column('router_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['router_id'], ['routers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('destination', 'nexthop', 'router_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('routerl3agentbindings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('router_id', sa.String(length=36), nullable=True),
    sa.Column('l3_agent_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['l3_agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['router_id'], ['routers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.drop_table(u'cisco_ml2_credentials')
    op.drop_table(u'ml2_gre_allocations')
    op.drop_table(u'ml2_vxlan_endpoints')
    op.drop_table(u'routes')
    op.drop_table(u'servicedefinitions')
    op.drop_table(u'cisco_ml2_nexusport_bindings')
    op.drop_table(u'ml2_vxlan_allocations')
    op.drop_table(u'ml2_gre_endpoints')
    op.drop_table(u'arista_provisioned_nets')
    op.drop_table(u'ml2_flat_allocations')
    op.drop_table(u'servicetypes')
    op.drop_table(u'ml2_vlan_allocations')
    op.drop_table(u'arista_provisioned_vms')
    op.drop_table(u'arista_provisioned_tenants')
    op.add_column('ml2_network_segments', sa.Column('segment_type', sa.String(length=255), nullable=False))
    op.drop_column('ml2_network_segments', u'segmentation_id')
    op.drop_column('ml2_network_segments', u'physical_network')
    op.drop_column('ml2_network_segments', u'network_type')
    ### end Alembic commands ###


def downgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ml2_network_segments', sa.Column(u'network_type', mysql.VARCHAR(length=32), nullable=False))
    op.add_column('ml2_network_segments', sa.Column(u'physical_network', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('ml2_network_segments', sa.Column(u'segmentation_id', mysql.INTEGER(display_width=11), nullable=True))
    op.drop_column('ml2_network_segments', 'segment_type')
    op.create_table(u'arista_provisioned_tenants',
    sa.Column(u'tenant_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'id', mysql.VARCHAR(length=36), nullable=False),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'arista_provisioned_vms',
    sa.Column(u'tenant_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'id', mysql.VARCHAR(length=36), nullable=False),
    sa.Column(u'vm_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'host_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'port_id', mysql.VARCHAR(length=36), nullable=True),
    sa.Column(u'network_id', mysql.VARCHAR(length=36), nullable=True),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_vlan_allocations',
    sa.Column(u'physical_network', mysql.VARCHAR(length=64), nullable=False),
    sa.Column(u'vlan_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column(u'allocated', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'physical_network', u'vlan_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'servicetypes',
    sa.Column(u'tenant_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'id', mysql.VARCHAR(length=36), nullable=False),
    sa.Column(u'name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'description', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'default', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column(u'num_instances', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_flat_allocations',
    sa.Column(u'physical_network', mysql.VARCHAR(length=64), nullable=False),
    sa.PrimaryKeyConstraint(u'physical_network'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'arista_provisioned_nets',
    sa.Column(u'tenant_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'id', mysql.VARCHAR(length=36), nullable=False),
    sa.Column(u'network_id', mysql.VARCHAR(length=36), nullable=True),
    sa.Column(u'segmentation_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_gre_endpoints',
    sa.Column(u'ip_address', mysql.VARCHAR(length=64), server_default='', nullable=False),
    sa.PrimaryKeyConstraint(u'ip_address'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_vxlan_allocations',
    sa.Column(u'vxlan_vni', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column(u'allocated', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'vxlan_vni'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'cisco_ml2_nexusport_bindings',
    sa.Column(u'binding_id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column(u'port_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'vlan_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column(u'switch_ip', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'instance_id', mysql.VARCHAR(length=255), nullable=True),
    sa.PrimaryKeyConstraint(u'binding_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'servicedefinitions',
    sa.Column(u'id', mysql.VARCHAR(length=36), nullable=False),
    sa.Column(u'service_class', mysql.VARCHAR(length=255), nullable=False),
    sa.Column(u'plugin', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'driver', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'service_type_id', mysql.VARCHAR(length=36), nullable=False),
    sa.ForeignKeyConstraint(['service_type_id'], [u'servicetypes.id'], name=u'servicedefinitions_ibfk_1'),
    sa.PrimaryKeyConstraint(u'id', u'service_class', u'service_type_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'routes',
    sa.Column(u'destination', mysql.VARCHAR(length=64), nullable=False),
    sa.Column(u'nexthop', mysql.VARCHAR(length=64), nullable=False),
    sa.Column(u'subnet_id', mysql.VARCHAR(length=36), nullable=False),
    sa.ForeignKeyConstraint(['subnet_id'], [u'subnets.id'], name=u'routes_ibfk_1'),
    sa.PrimaryKeyConstraint(u'destination', u'nexthop', u'subnet_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_vxlan_endpoints',
    sa.Column(u'ip_address', mysql.VARCHAR(length=64), server_default='', nullable=False),
    sa.Column(u'udp_port', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'ip_address', u'udp_port'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'ml2_gre_allocations',
    sa.Column(u'gre_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column(u'allocated', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'gre_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'cisco_ml2_credentials',
    sa.Column(u'credential_id', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'tenant_id', mysql.VARCHAR(length=255), nullable=False),
    sa.Column(u'credential_name', mysql.VARCHAR(length=255), nullable=False),
    sa.Column(u'user_name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column(u'password', mysql.VARCHAR(length=255), nullable=True),
    sa.PrimaryKeyConstraint(u'tenant_id', u'credential_name'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.drop_table('routerl3agentbindings')
    op.drop_table('routerroutes')
    op.drop_table('extradhcpopts')
    op.drop_table('subnetroutes')
    op.drop_table('networkdhcpagentbindings')
    op.drop_index('ix_quotas_tenant_id', table_name='quotas')
    op.drop_table('quotas')
    op.drop_table('agents')
    ### end Alembic commands ###
