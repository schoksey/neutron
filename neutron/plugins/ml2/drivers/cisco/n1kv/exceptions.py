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

"""Exceptions used by Cisco Nexus1000V ML2 mechanism driver."""

from neutron.common import exceptions


class VSMConnectionFailed(exceptions.ServiceUnavailable):
    """No response from Cisco Nexus1000V VSM."""
    message = _("Connection to VSM failed: %(reason)s.")


class VSMError(exceptions.NeutronException):
    """A response from Cisco Nexus1000V VSM was not HTTP OK."""
    message = _("Internal VSM Error: %(reason)s.")


class NetworkProfileNotFound(exceptions.NotFound):
    """Network Profile with the given UUID/name cannot be found."""
    message = _("Network Profile %(profile)s could not be found.")


class NetworkProfileAlreadyExists(exceptions.NeutronException):
    """Network Profile cannot be created since it already exists."""
    message = _("Network Profile %(profile_id)s "
                "already exists.")
