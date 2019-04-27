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

class ElasticLoadBalancing(AWSResource):
    """
    This is the implementation of Amazon's ElasticLoadBalancing.
    """
    flavor = "elb"

    state_lookup = {
        "running": State.running,
        "missing": State.terminated,
        "pending": State.pending
    }

    START_PARAM_FILTER = {
        "LoadBalancerName",
        "Listeners",
        "AvailabilityZones",
        "Subnets",
        "SecurityGroups",
        "Scheme",
        "Tags",
    }

    UPDATE_PARAM_FILTER = {
        "SecurityGroups",
        "Subnets",
        "Tags",
        "ListenerDescriptions"
    }

    REMOVE_PARAM_FILTER = {
        "LoadBalancerName",
        "AvailabilityZones",
        "Scheme",
    }

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="elb", session=session)
        self.elb_name = self.desired_state_definition["LoadBalancerName"]

    def create(self):
        """
        Creates a Classic Load Balancer that matches current state definition

        Returns:
            response of boto3 create rds instance with action create_load_balancer.
        """
        create_def = {key: self.desired_state_definition[key] for key in ElasticLoadBalancing.START_PARAM_FILTER if key
                      in self.desired_state_definition.keys()}
        return self.client.create_load_balancer(**create_def)

    def _terminate(self):
        """
        deletes the load balancer particle that matches the LoadBalancerName

        Returns:
            response of boto3 delete_load_balancer()
        """
        return self.client.delete_load_balancer(LoadBalancerName=self.elb_name)


    def get_status(self):
        """
        Get the current status of your load balancer. Calls boto3 describe_load_balancers using LoadBalancerNames

        Returns:
            dict with the load balancer that matches the LoadBalancerName provided
        """

        try:
            elb_status = self.client.describe_load_balancers(LoadBalancerNames=[self.elb_name])
        except ClientError as e:
            error_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            if error_code == 404 or error_code == 400:
                return {}
            else:
                raise e
        else:
            return elb_status['LoadBalancerDescriptions'][0]

    def sync_state(self):
        """
        Sync state calls get_status to determines and the state of the ELB particle.
        """
        elb_status = self.get_status()

        if elb_status:
            self.current_state_definition = elb_status
            self.state = State.running
        else:
            self.state = State.terminated

    def _update(self):
        """
        updates the ELB particle to match the desired state

        """
        filtered_curr_def = {key: self.current_state_definition[key] for key in ElasticLoadBalancing.UPDATE_PARAM_FILTER
                             if key in self.current_state_definition.keys()}

        filtered_des_def = {key: self.desired_state_definition[key] for key in self.desired_state_definition.keys()
                            if key not in ElasticLoadBalancing.REMOVE_PARAM_FILTER}

        diff = pcf_util.diff_dict(filtered_curr_def, filtered_des_def)

        curr_tags = self.client.describe_tags(
            LoadBalancerNames=[
                self.elb_name,
            ]
        )
        curr_tags = curr_tags.get('TagDescriptions')[0].get('Tags')
        curr_listeners = [x['Listener'] for x in filtered_curr_def.get('ListenerDescriptions')]
        des_listeners = filtered_des_def['Listeners']

        if diff.get('SecurityGroups', None):
            self.client.apply_security_groups_to_load_balancer(
                LoadBalancerName=self.elb_name,
                SecurityGroups=filtered_des_def.get('SecurityGroups')
            )

        if diff.get('Subnets', None):
            remove = set(filtered_curr_def.get('Subnets')) - set(filtered_des_def.get('Subnets'))
            add = set(filtered_des_def.get('Subnets')) - set(filtered_curr_def.get('Subnets'))
            if remove:
                self.client.detach_load_balancer_from_subnets(
                    LoadBalancerName=self.elb_name,
                    Subnets=list(remove)
                )
            if add:
                self.client.attach_load_balancer_to_subnets(
                    LoadBalancerName=self.elb_name,
                    Subnets=list(add)
                )

        if _need_update(curr_tags, filtered_des_def.get('Tags', {})):
            add = list(itertools.filterfalse(lambda x: x in curr_tags, filtered_des_def.get('Tags')))
            remove = list(itertools.filterfalse(lambda x: x in filtered_des_def.get('Tags'), curr_tags))
            if remove:
                self.client.remove_tags(LoadBalancerNames=[self.elb_name], Tags=[{'Key': x.get('Key')} for x in remove])
            if add:
                self.client.add_tags(LoadBalancerNames=[self.elb_name], Tags=add)

        if _need_update(curr_listeners, des_listeners):
            #Format current listener and desired listener so that I can compare.
            for item in des_listeners:
                if not item.get('InstanceProtocol'):
                    item.update({'InstanceProtocol': item.get('Protocol')})

            remove = list(itertools.filterfalse(lambda x: x in des_listeners, curr_listeners))
            add = list(itertools.filterfalse(lambda x: x in curr_listeners, des_listeners))

            if remove:
                self.client.delete_load_balancer_listeners(
                    LoadBalancerName=self.elb_name,
                    LoadBalancerPorts=[x['LoadBalancerPort'] for x in remove]
                )
            if add:
                self.client.create_load_balancer_listeners(
                    LoadBalancerName=self.elb_name,
                    Listeners=add
        )

    def _start(self):
        """
        creates elb particle that matches current state definition

        """
        self.create()

    def is_state_definition_equivalent(self):
        """
        Determines if the current state definition and the desired state definition are equivalent.

        Returns:
            bool
        """
        self.sync_state()
        filtered_curr_def = {key: self.current_state_definition[key] for key in ElasticLoadBalancing.UPDATE_PARAM_FILTER
                             if key in self.current_state_definition.keys()}

        filtered_des_def = {key: self.desired_state_definition[key] for key in self.desired_state_definition.keys()
                            if key not in ElasticLoadBalancing.REMOVE_PARAM_FILTER}

        def_diff = pcf_util.diff_dict(filtered_curr_def, filtered_des_def)
        curr_tags = self.client.describe_tags(
            LoadBalancerNames=[
                self.elb_name,
            ]
        )

        curr_tags = curr_tags.get('TagDescriptions')[0].get('Tags', [])
        des_tags = filtered_des_def.get('Tags', [])

        curr_listeners = [x['Listener'] for x in filtered_curr_def.get('ListenerDescriptions')]
        des_listeners = filtered_des_def['Listeners']

        for item in des_listeners:
            item.update({'InstanceProtocol': item.get('Protocol').upper()})
            item.update({'Protocol': item.get('Protocol').upper()})

        def_diff.pop('Listeners', None)
        def_diff.pop('Tags', None)
        print(curr_listeners,des_listeners,curr_tags,des_tags)
        if def_diff or _need_update(curr_listeners, des_listeners) or _need_update(curr_tags, des_tags):
            return False
        return True


def _need_update(curr_list, desired_list):
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
