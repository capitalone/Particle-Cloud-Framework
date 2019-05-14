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

from pcf.core import State
from pcf.util import pcf_util
from pcf.core.aws_resource import AWSResource
from pcf.core.pcf_exceptions import TooManyResourceException
import logging

logger = logging.getLogger(__name__)

class ECRRepository(AWSResource):
    """
    This is the implementation of Amazon's EC2 Container Registry (ECR) Repository.
    """

    flavor = "ecr_repository"

    state_lookup = {
        "available": State.running,
        "pending": State.pending,
        "missing": State.terminated
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    DEFINITION_FILTER = {
        'repositoryName',
        'tags'
    }

    UNIQUE_KEYS = ["aws_resource.repositoryName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ecr", session=session)
        self._set_unique_keys()
        self.repositoryName = self.desired_state_definition.get("repositoryName")

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECR Repository

        """
        self.unique_keys = ECRRepository.UNIQUE_KEYS

    def _terminate(self):
        """
        Calls boto3 delete_repository()

        Returns:
            boto3 delete_repository() response
        """
        resp = self.client.delete_repository(repositoryName =self.repositoryName)
        return resp

    def _start(self):
        """
        Starts the events particle that matches desired state definition

        Returns:
            response of boto3 create_repository()
        """
        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), ECRRepository.DEFINITION_FILTER)
        return self.client.create_repository(**start_definition)

    def _stop(self):
        """
        Calls _terminate()
        """
        return self._terminate()

    def sync_state(self):
        """
        Calls describe_repositories() and list_tags_for_resource to get state and state definitions of the ECR Particle
        """
        try:
            ecrs = self.client.describe_repositories(repositoryNames=[self.repositoryName])
            if len(ecrs["repositories"]) == 1:
                self.state = ECRRepository.state_lookup.get("available")
                ecr_status = ecrs["repositories"][0]
                ecr_status["tags"] = self.client.list_tags_for_resource(
                    resourceArn=ecr_status.get("repositoryArn")).get("tags")
                self.current_state_definition = ecr_status
            else:
                raise TooManyResourceException
        except:
            self.state = ECRRepository.state_lookup.get("missing")

    def is_state_equivalent(self, state1, state2):
        """
        Compare current and desired state

        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return ECRRepository.equivalent_states.get(state1) == ECRRepository.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Compare current and desired state definition

        Returns:
            bool
        """
        self.sync_state()
        diff_dict = pcf_util.diff_dict(pcf_util.param_filter(self.current_state_definition, ECRRepository.DEFINITION_FILTER),
                                       pcf_util.param_filter(self.desired_state_definition, ECRRepository.DEFINITION_FILTER))
        return diff_dict == {}


    def _update(self):
        """
        Updates any tag change
        """
        tags = self.current_state_definition.get("tags")
        tag_keys = []
        for tag in tags:
            tag_keys.append(tag.get("Key"))

        self.client.untag_resource(resourceArn=self.current_state_definition.get("repositoryArn"),
                                       tagKeys=tag_keys)
        self.client.tag_resource(resourceArn=self.current_state_definition.get("repositoryArn"),
                                       tags=self.desired_state_definition.get("tags"))
