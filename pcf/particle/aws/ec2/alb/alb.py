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

from botocore.errorfactory import ClientError
from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.util import pcf_util

import itertools
import logging

logger = logging.getLogger(__name__)

class ApplicationLoadBalancing(AWSResource):
    """
    This is the implementation of Amazon's Application Load Balancer.
    """
    flavor = "alb"

    state_lookup = {
        "active": State.running,
        "provisioning": State.pending,
        "active_impaired": State.terminated,
        "failed": State.terminated
    }

    START_PARAM_FILTER = {
        "Name",
        "Subnets",
        "SubnetMappings",
        "SecurityGroups",
        "Scheme",
        "Tags",
        "Type",
        "IpAddressType"
    }

    UPDATE_PARAM_FILTER = {
        "SecurityGroups"
    }

    REMOVE_PARAM_FILTER = {
        "Name",
        "Scheme",
        "custom_config",
        "Subnets",
        "Tags",
        "Type",
        "IpAddressType"
    }

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="elbv2", session=session)
        self.alb_name = self.desired_state_definition["Name"]

    def create(self):
        """
        Creates an Application Load Balancer that matches current state definition

        Returns:
            response of boto3 create alb instance with action create_load_balancer.
        """
        create_def = pcf_util.param_filter(self.desired_state_definition, self.START_PARAM_FILTER)
        return self.client.create_load_balancer(**create_def)

    def create_listener(self, create_listener_def):
        """
        Creates listeners for an Application Load Balancer that matches current state definition

        Returns:
            response of boto3 create alb instance with action create_listener.
        """
        create_listener_def['LoadBalancerArn'] = self.arn
        return self.client.create_listener(**create_listener_def)

    def _terminate(self):
        """
        deletes the load balancer particle that matches the LoadBalancerArn

        Returns:
            response of boto3 delete_load_balancer()
        """
        return self.client.delete_load_balancer(LoadBalancerArn=self.arn)

    def _get_arn(self):
        """
        Calls boto3 describe_load_balancers using Names to get current ALB status. Uses result to get LoadBalancerArn from the return object.

        Returns:
            ALB arn
        """

        status = self.client.describe_load_balancers(Names=[self.alb_name])
        return status['LoadBalancers'][0]['LoadBalancerArn']

    def get_status(self):
        """
        Get the current status of your load balancer. Calls boto3 describe_load_balancers using Names

        Returns:
            dict with the load balancer that matches the Name provided
        """

        try:
            alb_status = self.client.describe_load_balancers(Names=[self.alb_name])
        except ClientError as e:
            error_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            if error_code == 404 or error_code == 400:
                return {}
            else:
                raise e
        else:
            return alb_status['LoadBalancers'][0]

    def get_listener_status(self):
        """
        Get the current status of your load balancer's listener(s). Calls boto3 describe_listeners using LoadBalancerArn

        Returns:
            dict with the load balancer's listeners that matches the LoadBalancerArn provided
        """

        try:
            alb_listener_status = self.client.describe_listeners(LoadBalancerArn=self.arn)
        except ClientError as e:
            error_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            if error_code == 404 or error_code == 400:
                return {}
            else:
                raise e
        else:
            return alb_listener_status['Listeners']

    def sync_state(self):
        """
        Sync state calls get_status to determines and the state of the alb particle.
        """
        alb_status = self.get_status()

        if alb_status:
            self.current_state_definition = alb_status
            self.state = self.state_lookup[alb_status['State']['Code']]
        else:
            self.state = State.terminated

    def _update(self):
        """
        updates the alb particle to match the desired state

        """
        filtered_curr_def = pcf_util.param_filter(self.current_state_definition, self.UPDATE_PARAM_FILTER)

        filtered_des_def = pcf_util.param_filter(self.desired_state_definition, self.REMOVE_PARAM_FILTER, True)

        diff = pcf_util.diff_dict(filtered_curr_def, filtered_des_def)

        curr_tags = self.client.describe_tags(
            ResourceArns=[
                self.arn
            ]
        )
        curr_tags = curr_tags.get('TagDescriptions')[0].get('Tags')
        des_tags = self.desired_state_definition.get('Tags', [{}])

        curr_listeners = [x for x in self.get_listener_status()]
        # Format current listener to compare.
        filtered_curr_listeners = [x for x in self.get_listener_status()]
        for item in filtered_curr_listeners:
            if 'ListenerArn' in item:
                item.pop('ListenerArn')

        des_listeners = self.custom_config['Listeners']

        if diff.get('SecurityGroups', None):
            self.client.set_security_groups(
                LoadBalancerArn=self.arn,
                SecurityGroups=filtered_des_def.get('SecurityGroups')
            )

        curr_availabilty_zones = pcf_util.find_nested_dict_value(self.current_state_definition, ['AvailabilityZones'])
        curr_subnets_list = pcf_util.transform_list_of_dicts_to_desired_list(curr_availabilty_zones, 'SubnetId')
        des_subnets_list = self.desired_state_definition.get('Subnets')

        if not pcf_util.is_list_equal(curr_subnets_list, des_subnets_list):
            update = des_subnets_list
            if update:
                self.client.set_subnets(
                    LoadBalancerArn=self.arn,
                    Subnets=list(update)
                )


        if self._need_update(curr_tags, des_tags):
            add = list(itertools.filterfalse(lambda x: x in curr_tags, des_tags))
            remove = list(itertools.filterfalse(lambda x: x in des_tags, curr_tags))
            if remove:
                self.client.remove_tags(ResourceArns=[self.arn], TagKeys=[x.get('Key') for x in remove])
            if add:
                self.client.add_tags(ResourceArns=[self.arn], Tags=add)


        if self._need_update(filtered_curr_listeners, des_listeners):
            #Format current listener and desired listener to compare.
            for item in des_listeners:
                item.update({'Protocol': item.get('Protocol').upper()})

            for item in curr_listeners:
                self.client.delete_listener(
                    ListenerArn=item['ListenerArn']
                )

            for item in des_listeners:
                item['LoadBalancerArn'] = self.arn
                self.create_listener(item)

    def _start(self):
        """
        creates ALB particle that matches current state definition
        and
        calls create_listener() if 'Listeners' key is found in custom_config

        """
        started = True
        self.create()

        if self.custom_config.get('Listeners', None):
            listeners = self.custom_config.get('Listeners', None)
            for listener in listeners:
                self.create_listener(listener)


    def is_state_definition_equivalent(self):
        """
        Determines if the current state definition and the desired state definition are equivalent.

        Returns:
            bool
        """
        filtered_curr_def = pcf_util.param_filter(self.current_state_definition, self.UPDATE_PARAM_FILTER)

        filtered_des_def = pcf_util.param_filter(self.desired_state_definition, self.REMOVE_PARAM_FILTER, True)

        def_diff = pcf_util.diff_dict(filtered_curr_def, filtered_des_def)

        curr_tags = self.client.describe_tags(
            ResourceArns=[
                self.arn
            ]
        )

        curr_tags = curr_tags.get('TagDescriptions')[0].get('Tags', [])
        des_tags = self.desired_state_definition.get('Tags', [])

        curr_availabilty_zones = pcf_util.find_nested_dict_value(self.current_state_definition, ['AvailabilityZones'])
        curr_subnets_list = pcf_util.transform_list_of_dicts_to_desired_list(curr_availabilty_zones, 'SubnetId')

        des_subnets_list = self.desired_state_definition.get('Subnets', [])

        curr_listeners = [pcf_util.param_filter(x, {'SslPolicy'}, True) for x in self.get_listener_status()]
        des_listeners = self.custom_config.get('Listeners', [])

        for item in des_listeners:
            item.update({'Protocol': item.get('Protocol').upper()})

        for item in curr_listeners:
            if 'ListenerArn' in item:
                item.pop('ListenerArn')

        if def_diff or self._need_update(curr_tags, des_tags) or self._need_update(curr_listeners, des_listeners) \
            or not pcf_util.is_list_equal(curr_subnets_list, des_subnets_list):
            return False
        return True

    def _need_update(self, curr_list, desired_list):
        """
        Checks to see if there are any difference in curr_list or desired_list. If they are different this returns True.

        Args:
            curr_list (list): list of dictionaries
            desired_list (list): list of dictionaries

        Returns:
            bool
        """
        #Checks if items need to be added or removed.
        add = list(itertools.filterfalse(lambda x: x in curr_list, desired_list))
        remove = list(itertools.filterfalse(lambda x: x in desired_list, curr_list))
        if add or remove:
            return True
        return False
