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
from botocore.errorfactory import ClientError
#TEST
import itertools
import logging

logger = logging.getLogger(__name__)

class ESDomain(AWSResource):
    """
    This is the implementation of Amazon's S3 service.
    """
    flavor = "es"

    START_PARAM_FILTER = {
        'DomainName',
        'ElasticsearchVersion',
        'ElasticsearchClusterConfig',
        'EBSOptions',
        'AccessPolicies',
        'SnapshotOptions',
        'VPCOptions',
        'CognitoOptions',
        'EncryptionAtRestOptions',
        'NodeToNodeEncryptionOptions',
        'AdvancedOptions',
        'LogPublishingOptions'
        }

    UPDATE_PARAM_FILTER = {
        'DomainName',
        'ElasticsearchClusterConfig',
        'EBSOptions',
        'SnapshotOptions',
        'VPCOptions',
        'CognitoOptions',
        'AdvancedOptions',
        'AccessPolicies',
        'LogPublishingOptions'
        }

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="es", session=session)
        self.domain_name = self.desired_state_definition["DomainName"]

    def _terminate(self):
        """
        Terminates the elasticsearch particle that matches with domain_name

        Returns:
            response of boto3 delete_elasticsearch_domain
        """
        return self.client.delete_elasticsearch_domain(DomainName=self.domain_name)

    def _start(self):
        """
        Starts the elasticsearch particle that mathces the desired state function

        Returns:
            response of boto3 create_elasticsearch_domain
        """

        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), ESDomain.START_PARAM_FILTER)
        response = self.client.create_elasticsearch_domain(**start_definition)
        self._arn = response['DomainStatus']['ARN']

        if self.custom_config.get("Tags"):
            tags = self.custom_config.get("Tags")
            tag_set = []
            for k, v in tags.items():
                tag_set.append({
                    "Key": k,
                    "Value": v
                })

            self.client.add_tags(ARN=self._arn, TagList=tag_set)

        return response

    def _stop(self):
        """
        Elasticsearch does not have a sotpped state so it calls terminate.
        """
        return self._terminate

    def sync_state(self):
        """
        Elasticsearch implementation of sync state. Calls get status and sets the current state.
        """
        status_def = self.get_status()
        if status_def.get('status') == 'missing':
            self.state = State.terminated
            return

        self.current_state_definition = status_def
        if self.current_state_definition["Created"] and not self.current_state_definition['Deleted'] and not self.current_state_definition['Processing'] and not self.current_state_definition['UpgradeProcessing']:
            self.state = State.pending
        else:
            self.state = State.terminated

        print("THIS IS THE CURRENT STATE DEFINITION", self.current_state_definition)
        print("THIS IS THE DESIRED STATE DEFINITION", self.desired_state_definition)

    def get_status(self):
        """
        Calls the describe es boto call and returns status missing if the function does not exist.
        Otherwise will return the current definition

        Return:
            current definition
        """
        try:
            current_definition = self.client.describe_elasticsearch_domain(DomainName=self.domain_name)['DomainStatus']

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Domain {} was not found. State is terminated".format(self.domain_name))
                return {'status': 'missing'}
            else:
                raise e

        return current_definition

    def _update(self):
        """
        Updates the es particle to match current state definition.
        """
        update_definition = pcf_util.param_filter(self.current_state_definition, self.UPDATE_PARAM_FILTER)
        self.client.update_elasticsearch_domain_config(**update_definition)

        if self._arn:
            domain_arn = self._arn
            current_tags = self.client.list_tags_of_resource(ResourceArn=domain_arn)['Tags']
        else:
            domain_arn = self.current_state_definition.get('TableArn')
            current_tags = self.client.list_tags_of_resource(ResourceArn=domain_arn)['Tags']

        desired_tags = self.desired_state_definition.get('Tags', [])

        if self._need_update(current_tags, desired_tags):
            add = list(itertools.filterfalse(lambda x:x in current_tags, desired_tags))
            remove = list(itertools.filterfalse(lambda x:x in desired_tags, current_tags))
            if remove:
                self.client.untag_resource(
                        ResourceArn=domain_arn,
                        TagKeys=[x.get('Key') for x in remove]
                    )
            if add:
                self.client.tag_resource(
                        ResourceArn=domain_arn,
                        Tags=list(add)
                    )

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and the current state definitions.

        Returns:
            bool
        """
        self.get_state()
        current_definition = pcf.util.param_filter(self.current_state_definition, self.desired_state_definition)
        desired_definition = pcf.util.param_filter(self.desired_state_definition, self.current_state_definition)

        #compare tags
        if self._arn:
            current_tags = self.client.list_tags_of_resources(ResourceARN=self._arn)['Tags']
        else:
            current_tags = self.client.list_tags_of_resource(ResourceArn=self.current_state_definition.get('TableArn'))['Tags']

        desired_tags = desired_definition.get('Tags', [])

        new_desired_state_def, diff_dict = pcf_util.update_dict(current_definition, desired_definition)

        diff_dict.pop('Tags', None)

        return diff_dict == {} #and not self._need_update(current_tags, desired_tags)

    def _need_update(self, curr_list, desired_list):
        """
        Checks to see if there any differences in curr_list or desired_list. If they are different True is returned.

        Args:
            curr_list (list): list of dictionaries
            desired_list (list): list of dictionaries

        return:
            bool
        """
        add = list(itertools.filterfalse(lambda x:x in curr_list, desired_list))
        remove = list(itertools.filterfalse(lambda x:x in desired_list, curr_list))
        return True if add or remove else False
