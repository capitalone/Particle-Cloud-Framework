# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.util import pcf_util
from deepdiff import DeepDiff


class HostedZone(AWSResource):
    """
    Particle that maps to AWS hosted zone
    """

    flavor = 'route53_hosted_zone'

    START_PARAM_FILER = {
        "Name",
        "VPC",
        "CallerReference",
        "HostedZoneConfig",
        "DelegationSetId"
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Name"]

    def __init__(self, particle_definition, session=None):
        """
        Args:
            particle_definition (definition): desired definition of the hosted zone
        """
        super(HostedZone, self).__init__(particle_definition, 'route53', session=session)
        self._name = self.desired_state_definition.get("Name")
        self._id = ""
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Route53 Hosted Zone
        """
        self.unique_keys = HostedZone.UNIQUE_KEYS

    def _start(self):
        """
        Creates a Route53 Hosted Zone using boto3 create_hosted_zone
        Returns:
            hosted_zone: boto3 response
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, HostedZone.START_PARAM_FILER)
        hosted_zone = self.client.create_hosted_zone(**start_definition)
        self._id = hosted_zone.get("HostedZone", {}).get("Id", None)
        self.client.change_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=self._id,
            AddTags=self.custom_config.get("Tags"),
        )
        return hosted_zone

    def _terminate(self):
        """
        Deletes a Route53 Hosted Zone using boto3 delete_hosted_zone
        Returns:
            boto3 response
        """
        return self.client.delete_hosted_zone(Id=self._id)

    def _stop(self):
        """
        Calls _terminate
        """
        return self._terminate()

    def _update(self):
        """
        Removes existing tags and adds new tags using boto3 change_tags_for_resource and list_tags_for_resource
        """
        current_tags = self.client.list_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=self._id
        ).get("ResourceTagSet", {}).get("Tags")
        # one api call. might as well just remove all and add all, instead of iterating through tags for differences
        self.client.change_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=self._id,
            AddTags=self.custom_config.get("Tags"),
            RemoveTagKeys=[keypair.get("Key") for keypair in current_tags]
        )

    def get_status(self):
        """
        Get the current definition of the route 53 hosted zone
        Returns:
            current definition of the hosted zone
        """
        response = self.client.list_hosted_zones_by_name(DNSName=self._name, MaxItems="1") # why str boto??
        if len(response.get("HostedZones", [])) > 0:
            if response.get("HostedZones")[0].get("Name") == self._name:
                self._id = response.get("HostedZones")[0].get("Id")
                return response.get("HostedZones")[0]

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the hosted zone
        """
        full_status = self.get_status()
        if not full_status:
            self.state = State.terminated
            self.current_state_definition = {}
        else:
            self.current_state_definition = full_status.get("HostedZone")
            self.state = State.running

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent
        Args:
            state1 (state): first state
            state2 (state): second state
        Returns:
            bool: whether the two states are equivalent
        """
        return HostedZone.equivalent_states.get(state1) == HostedZone.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        This class is only concerned with changes to tags since there is a separate particle for record sets
        Returns:
             bool: True
        """
        current_tags = self.client.list_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=self._id
        ).get("ResourceTagSet", {}).get("Tags")
        if DeepDiff(current_tags, self.custom_config.get("Tags"), ignore_order=True):
            return False
        return True
