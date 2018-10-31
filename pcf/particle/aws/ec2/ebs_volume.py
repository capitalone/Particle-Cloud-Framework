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

from botocore.exceptions import ClientError
from pcf.core import State
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core.aws_resource import AWSResource
from pcf.core.pcf_exceptions import NoResourceException, TooManyResourceException, ParentRequiredException
from pcf.util import pcf_util

import logging

logger = logging.getLogger(__name__)


class EBSVolume(AWSResource):
    """This is the EBS Volume particle. This also contains functions to attach and detach to an ec2 volume. There is a custom config called
     attach, which when set to True will auto attach to a parent EC2"""
    flavor = 'ebs_volume'

    state_lookup = {
        'creating': State.pending,
        'deleting': State.pending,
        'attaching': State.pending,
        'available': State.running,
        'in-use': State.running,
        'deleted': State.terminated,
        'detaching':State.terminated,
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAM_FILTER = {
        'AvailabilityZone',
        'Encrypted',
        'Iops',
        'KmsKeyId',
        'Size',
        'SnapshotId',
        'VolumeType',
        'TagSpecifications',
    }

    UPDATE_PARAM_FILTER = {
        'Iops': '',
        'Size': '',
        'VolumeType': '',
    }

    UNIQUE_KEYS = ["aws_resource.custom_config.volume_name"]

    def __init__(self, particle_definition):
        super(EBSVolume, self).__init__(particle_definition, 'ec2')

        self.desired_state_definition['TagSpecifications'][0]['Tags'].append({"Key":"PCFName", "Value":self.custom_config["volume_name"]})
        self.tags = self.desired_state_definition['TagSpecifications'][0]['Tags']

        self.volume_id = self.desired_state_definition.get('VolumeId')

        if not self.volume_id and not self.custom_config.get("volume_name"):
            raise ValueError('VolumeId or custom_config:volume_name missing from definition')

        self.state = None

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the EBS volume

        """
        self.unique_keys = EBSVolume.UNIQUE_KEYS

    def get_status(self):
        """
        Calls boto3 describe_volumes using VolumeId.

        Returns:
             status
        """
        volume_id = self.volume_id

        if not volume_id:
            volume_id = self.current_state_definition.get('VolumeId')

        if not volume_id:
            res = self.client.describe_volumes(Filters=[{
                'Name': 'tag:PCFName',
                'Values': [self.custom_config.get("volume_name")]
            }])

            if not res.get('Volumes'):
                raise NoResourceException

            if len(res.get('Volumes', [])) > 1:
                raise TooManyResourceException

            return res['Volumes'][0]

        try:
            res = self.client.describe_volumes(VolumeIds=[volume_id])
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                raise NoResourceException
            raise

        return res.get('Volumes')[0]

    def is_state_definition_equivalent(self):
        """
        Determines if state definitions are equivalent including list of tags.

        Returns:
            Bool
        """
        if len(self.current_state_definition.get('Tags',[])) != len(self.tags):
            return False

        tag_zip = zip(sorted(self.current_state_definition.get('Tags',[]), key=lambda k: k["Value"]), sorted(self.tags, key=lambda k: k["Value"]))
        diff_tags = any(x != y for x, y in tag_zip)

        if diff_tags:
            return False

        filtered_current_definition = pcf_util.param_filter(
            self.get_current_state_definition(),
            EBSVolume.UPDATE_PARAM_FILTER,
        )

        filtered_desired_definition = pcf_util.param_filter(
            self.get_desired_state_definition(),
            EBSVolume.UPDATE_PARAM_FILTER,
        )

        diff = pcf_util.diff_dict(filtered_current_definition, filtered_desired_definition)

        if diff:
            return False

        return True

    def is_state_equivalent(self, state1, state2):
        """
        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return EBSVolume.equivalent_states.get(state1) == EBSVolume.equivalent_states.get(state2)

    def sync_state(self):
        """
        Updates the current_state_definition and the current state. Will attach to parent ec2 if parent exists and custom
        config flag is set. Will detach on termination. If you do not want it terminated, set termination protection and
        call detach function.
        """
        try:
            status = self.get_status()
        except NoResourceException:
            self.state = State.terminated
            return

        self.volume_id = status['VolumeId']
        state_name = status['State']
        self.state = EBSVolume.state_lookup.get(state_name)
        self.current_state_definition = status

        # attach ebs to parent ec2
        if self.state == State.running and self.desired_state == State.running and \
            self.custom_config.get("attach") and len(status.get('Attachments', [])) != 1:

            name = self.custom_config.get("volume_name")
            if name[len(name)-1].isdigit():
                device = '/dev/xvd' + chr(int(name[len(name)-1]) + 98)
            else:
                device = '/dev/sdf'

            self.attach_volume(device=device)
            self.sync_state()  # update current definition with attachment


    def _start(self):
        """
        Calls boto3 create_volume().

        Returns:
           boto3 create_volume() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(
            self.current_state_definition,
            self.get_desired_state_definition()
        )
        start_params = pcf_util.param_filter(new_desired_state_def, EBSVolume.START_PARAM_FILTER)
        res = self.client.create_volume(**start_params)
        if res.get('VolumeId'):
            self.volume_id = res.get('VolumeId')

        return res

    def _stop(self):
        """
        Calls _terminate()
        """
        self._terminate()

    def _terminate(self):
        """
        Calls boto3 delete_volume().

        Returns:
           boto3 delete_volume() response
        """
        # detach on termination
        if len(self.current_state_definition.get('Attachments', [])) == 1:
            self.detach_volume()

        try:
            self.client.delete_volume(VolumeId=self.volume_id)
        except ClientError as e:
            if e.response['Error']['Code'] == 'VolumeInUse':
                pass  # wait for volume to fully detach


    def _update(self):
        """
        Calls boto3 modify_volume(). If tags are changes then also calls delete_tags() and then create_tags()

        Returns:
           boto3 modify_volume() response
        """
        filtered_current_definition = pcf_util.param_filter(
            self.get_current_state_definition(),
            EBSVolume.UPDATE_PARAM_FILTER,
        )

        filtered_desired_definition = pcf_util.param_filter(
            self.get_desired_state_definition(),
            EBSVolume.UPDATE_PARAM_FILTER,
        )

        diff = pcf_util.diff_dict(filtered_current_definition, filtered_desired_definition)

        # update tags
        tag_zip = zip(sorted(self.current_state_definition.get('Tags',[]), key=lambda k: k["Value"]), sorted(self.tags, key=lambda k: k["Value"]))
        diff_tags = any(x != y for x, y in tag_zip)
        if diff_tags or len(self.current_state_definition.get('Tags',[])) != len(self.tags):
            self.client.delete_tags(Resources=[self.volume_id])
            self.client.create_tags(Resources=[self.volume_id],Tags=self.tags)

        if not diff:
            return

        return self.client.modify_volume(VolumeId=self.volume_id, **filtered_desired_definition)

    def attach_volume(self, device="/dev/sdf", ec2_parent_id=None):
        """
        Calls boto3 attach_volume().

        Args:
            device (str): ec2 device to attach to. Default: /dev/sdf
            ec2_parent_id (str): ec2 parent instance id. Default: Parent ec2 instanceId

        Returns:
            boto3 attach_volume() response

        """
        if not ec2_parent_id:
            ec2_instance_parents = list(filter(lambda x: isinstance(x, EC2Instance), self.parents))
            if len(ec2_instance_parents) != 1:
                raise ParentRequiredException
            ec2_parent_id = ec2_instance_parents[0].get_identifier()

        return self.client.attach_volume(Device=device, InstanceId=ec2_parent_id, VolumeId=self.volume_id)

    def detach_volume(self):
        """
        Calls boto3 detach_volume().

        Returns:
            boto3 detach_volume() response
        """
        return self.client.detach_volume(VolumeId=self.volume_id)

