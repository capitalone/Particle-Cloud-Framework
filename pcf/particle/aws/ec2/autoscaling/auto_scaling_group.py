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

import logging
import json

logger = logging.getLogger(__name__)

class AutoScalingGroup(AWSResource):
    """
    This is the implementation of Amazon's Auto Scaling group. This particle requires one of the following: a launch configuration,
    a launch template, or an EC2 instance to be included in the initial state definition or have those particles as a parent.
    """
    flavor = "auto_scaling_group"

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAM_FILTER = {
        "AutoScalingGroupName",
        "LaunchConfigurationName",
        "LaunchTemplate",
        "DesiredCapacity",
        "DefaultCooldown",
        "AvailabilityZones",
        "LoadBalancerNames",
        "TargetGroupARNs",
        "HealthCheckType",
        "HealthCheckGracePeriod",
        "PlacementGroup",
        "TerminationPolicies",
        "NewInstancesProtectedFromScaleIn",
        "ServiceLinkedRoleARN",
        "InstanceId",
        "MinSize",
        "MaxSize",
        "Tags",
        "VPCZoneIdentifier",
        "LifecycleHookSpecificationList",
        "UserData",
        "instance-id",
    }

    REMOVE_PARAM_FILTER = {
        "LoadBalancerNames",
        "LifecycleHookSpecificationList",
        "Instances",
        "Tags",
    }

    UNIQUE_KEYS = ["aws_resource.AutoScalingGroupName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="autoscaling", session=session)
        self.asg_name = self.desired_state_definition["AutoScalingGroupName"]

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Auto Scaling Group

        """
        self.unique_keys = AutoScalingGroup.UNIQUE_KEYS

    def _terminate(self):
        """
        deletes the Auto Scaling group particle that matches the name

        Returns:
            response of boto3 delete_auto_scaling_group()
        """
        return self.client.delete_auto_scaling_group(AutoScalingGroupName=self.asg_name, ForceDelete=True)

    def _start(self):
        """
        start the autoscaling group particle that matches current state definition

        Returns:
            response of boto3 create_auto_scaling_group()
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, AutoScalingGroup.START_PARAM_FILTER)
        return self.client.create_auto_scaling_group(**start_definition)

    def _update(self):
        """
        Updates the Auto Scaling group that matches current state definition

        Returns:
            response of boto3 update_auto_scaling_group()
        """
        update_definition = pcf_util.param_filter(self.desired_state_definition,
                                                    AutoScalingGroup.REMOVE_PARAM_FILTER, True)
        return self.client.update_auto_scaling_group(**update_definition)

    def get_status(self):
        """
        Get the current status of your autoscaling group. Calls boto3 describe_auto_scaling_groups using asg_name

        Returns:
            dict with the Auto Scaling group that matches the asg_name provided
        """
        asg_status = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg_name])

        return asg_status.get('AutoScalingGroups',[])

    def sync_state(self):
        """
        Sync state calls get_status to determines and the state of the Auto Scaling group particle.
        """
        asg_status = self.get_status()
        if len(asg_status) == 0:
            self.state = State.terminated
            self.current_state_definition = {}
        else:
            self.current_state_definition = asg_status[0]
            if asg_status[0].get('Status') == 'Delete in progress':
                print('State.pending')
                self.state = State.pending
            elif asg_status[0].get('AutoScalingGroupName') == self.asg_name:
                self.state = State.running
            else:
                self.state = State.terminated

    def is_state_definition_equivalent(self):
        """
        Determines if the current state definition matches the current state definition. Uses keep and remove function from pcf util to remove extra params in desired state that are not
        in the current state.

        Returns:
            bool
        """
        self.get_state()
        desired_definition = pcf_util.param_filter(self.desired_state_definition,
                                                     AutoScalingGroup.REMOVE_PARAM_FILTER, True)
        diff = pcf_util.diff_dict(self.current_state_definition, desired_definition)
        if not diff or len(diff) == 0:
            return True
        else:
            logger.debug("State is not equivalent for {0} with diff: {1}".format(self.get_pcf_id(), json.dumps(diff)))
            return False

    def _stop(self):
        pass
