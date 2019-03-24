# Copyright 2019 Capital One Services, LLC
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
import time
from datetime import datetime, timedelta


class CloudFrontDistribution(AWSResource):
    """
    Particle that maps to AWS Cloud Front
    """

    flavor = 'cloudfront'

    START_PARAM_FILER = {
        'CallerReference',
        'Aliases',
        'DefaultRootObject',
        'Origins',
        'OriginGroups',
        'DefaultCacheBehavior',
        'CacheBehaviors',
        'CustomErrorResponses',
        'Comment',
        'Logging',
        'PriceClass',
        'Enabled',
        'ViewerCertificate',
        'Restrictions',
        'WebACLId',
        'HttpVersion',
        'IsIPV6Enabled'
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Comment"]

    def __init__(self, particle_definition, session=None):
        """
        Args:
            particle_definition (definition): desired configuration of the particle
        """
        super(CloudFrontDistribution, self).__init__(particle_definition, 'cloudfront', session=session)
        self._id = None
        self._ifMatch = None

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the distribution
        """
        self.unique_keys = CloudFrontDistribution.UNIQUE_KEYS

    def _start(self):
        """
        Creates the distribution according to the particle definition and adds tags if necessary

        Returns:
            hosted_zone: boto3 response
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, CloudFrontDistribution.START_PARAM_FILER)
        response = self.client.create_distribution_with_tags(
            DistributionConfigWithTags={
                "DistributionConfig": start_definition,
                "Tags": {
                    "Items": self.desired_state_definition.get("Tags", [])
                }
            }
        )
        self._id = response.get("Distribution", {}).get("Id")
        self._ifMatch = response.get("ETag")
        return response

    def _terminate(self):
        """
        Deletes the distribution using its id

        Returns:
            boto3 response
        """
        self.stop()
        return self.client.delete_distribution(Id=self._id, IfMatch=self._ifMatch)

    def _stop(self):
        """
        Sets the distribution to disabled and waits until it is finished
        """
        status = self.client.get_distribution(Id=self._id)
        # wait if the distribution is already being updated
        if status.get('Distribution', {}).get('DistributionConfig', {}).get('Enabled', False):
            # using the current definition from get_distribution() to fill in all the extra required fields
            self.current_state_definition["Enabled"] = False
            self.client.update_distribution(
                DistributionConfig=self.current_state_definition,
                Id=self._id,
                IfMatch=self._ifMatch
            )
        print("Waiting for disabled distribution... This may take a while")
        timeout_min = 60
        wait_until = datetime.now() + timedelta(minutes=timeout_min)
        while status.get("Distribution", {}).get("Status") == "InProgress":
            print("Not completed yet. Sleeping 3 mins....")
            time.sleep(180)
            # check for timeout
            if wait_until < datetime.now():
                # timeout
                raise Exception("Distribution took too long to disable")
            # check status
            status = self.client.get_distribution(Id=self._id)

    def _update(self):
        """
        Not implemented
        """
        raise NotImplemented

    def get_status(self):
        """
        Gets the current definition of the cloudfront distribution
        Must list all distributions and search for matching comment field, bc
        no filtering by name and getting tags require another api call

        Returns:
            current definition of the distribution
        """
        if not self._id:
            response = self.client.list_distributions().get("DistributionList", {})
            distribution_list = response.get("Items", {})
            while response.get("IsTruncated", False):
                response = self.client.list_distributions(Marker=response.get("NextMarker")).get("DistributionList")
                distribution_list += response.get("Items")
            if len(distribution_list) < 1:
                return None
            for distribution in distribution_list:
                # use comment as uid
                if distribution.get("Comment") == self.desired_state_definition.get("Comment"):
                    self._id = distribution.get("Id")
        try:
            status = self.client.get_distribution(Id=self._id)
        except:
            return None
        self._ifMatch = status.get("ETag")
        return status.get("Distribution", {}).get("DistributionConfig", {})

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the distribution
        """
        full_status = self.get_status()
        if not full_status:
            self.state = State.terminated
        else:
            self.current_state_definition = full_status
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
        return CloudFrontDistribution.equivalent_states.get(state1) == CloudFrontDistribution.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Since there is no update available, always return True
        Returns:
             bool: True
        """
        return True
