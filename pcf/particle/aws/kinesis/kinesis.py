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
from pcf.util import pcf_util
import logging
import json
import itertools
from pcf.core import State
from botocore.errorfactory import ClientError
logger = logging.getLogger(__name__)

class Kinesis(AWSResource):

    flavor='kinesis'

    #this is helpful if the particle doesn't have all three states or has more than three.

    UNIQUE_KEYS = ["aws_resource.StreamName"]
    equivalent_states = {
            State.running: 1,
            State.stopped: 0,
            State.terminated: 0,
        }
    state_lookup = {
        "CREATING":State.pending,
        "DELETING" : State.pending,
        "ACTIVE" : State.running,
        "UPDATING" : State.pending
    }

    START_PARAM_FILTER = {
        "StreamName",
        "ShardCount"
    }
    UPDATE_PARAM_FILTER = {
        "StreamName",
        "RetentionPeriodHours",
        "EncryptionType",
        "KeyId",
        "Tags"
    }
    def __init__(self, particle_definition):
        super(Kinesis, self).__init__(particle_definition, 'kinesis')
        self.stream_name = particle_definition.get("aws_resource").get("StreamName")
        self.get_desired_state_definition().get("Tags").append({"Key": "pcfName", "Value": particle_definition.get("pcf_name", '')})

    def sync_state(self):
        current_state = self.get_status()
        if not current_state:
            self.state = State.terminated
            return
        self.state = Kinesis.state_lookup.get(current_state.get("StreamStatus"))
        self.current_state_definition = pcf_util.param_filter(current_state, Kinesis.UPDATE_PARAM_FILTER)
        if not current_state.get("KeyId"):
            self.current_state_definition["KeyId"] = ''
        self.current_state_definition["Tags"] = self.client.list_tags_for_stream(StreamName=self.stream_name).get("Tags", [])
        if current_state.get("StreamStatus") == "ACTIVE":
            self.current_state_definition["ShardCount"] = self.getOpenShardCount()
        else:
            self.current_state_definition["ShardCount"] = 0
        print("THIS IS THE CURRENT STATE DEFINITION", self.current_state_definition)
        print("THIS IS THE DESIRED STATE DEFINITION", self.get_desired_state_definition())

    def getOpenShardCount(self):
        current_state = self.get_status()
        return current_state.get('OpenShardCount', 0)
    def _update(self):
        self._updateShards()
        self._updateTags()
        self._updateStreamRetention()
        self._updateEncryptionTypeAndKey()

    def _terminate(self):
        return self.client.delete_stream(StreamName=self.stream_name)

    def _start(self):
        create_definition = pcf_util.param_filter(self.get_desired_state_definition(), Kinesis.START_PARAM_FILTER)
        self.stream_name = self.get_desired_state_definition().get("StreamName")
        if (self.get_status()):
            self._update()
        else:
            self.client.create_stream(**create_definition)

    def _stop(self):
        return self._terminate()

    def _updateShards(self):
        current_state = self.get_status()
        print("IF STATEMENT VALUE", self.getOpenShardCount() != self.get_desired_state_definition().get("ShardCount") and current_state.get("StreamStatus") == "ACTIVE")
        if(self.getOpenShardCount() != self.get_desired_state_definition().get("ShardCount") and current_state.get("StreamStatus") == "ACTIVE"):
            print("IVE ATTEMPTED INCREASING THE SHARDS")
            self.client.update_shard_count(StreamName=self.stream_name, TargetShardCount=self.get_desired_state_definition().get("ShardCount"), ScalingType='UNIFORM_SCALING')

    def _updateStreamRetention(self):
        current_state = self.get_status()
        currentRetention = current_state.get("RetentionPeriodHours")
        desiredRetention = self.get_desired_state_definition().get("RetentionPeriodHours")
        diff = currentRetention - desiredRetention
        if current_state.get("StreamStatus") == "ACTIVE":
            if diff > 0:
                self.client.decrease_stream_retention_period(StreamName=self.stream_name, RetentionPeriodHours=desiredRetention)
            elif diff < 0:
                self.client.increase_stream_retention_period(StreamName=self.stream_name, RetentionPeriodHours=desiredRetention)
    def _updateTags(self):
        currentTags = self.client.list_tags_for_stream(StreamName=self.stream_name).get("Tags")
        desired_tags = self.get_desired_state_definition().get("Tags")
        if self._need_update(currentTags, desired_tags):
            add = list(itertools.filterfalse(lambda x: x in currentTags, desired_tags))
            remove = list(itertools.filterfalse(lambda x: x in desired_tags, currentTags))
            if remove:
                self.client.remove_tags_from_stream(
                    StreamName=self.stream_name,
                    TagKeys=[x.get('Key') for x in remove]
                )
            if add:
                addDict = {x.get("Key"):x.get("Value") for x in add}
                self.client.add_tags_to_stream(
                    StreamName=self.stream_name,
                    Tags=(addDict)
                )
    def _updateEncryptionTypeAndKey(self):
        current_state = self.get_status()
        currentEncryption = current_state.get("EncryptionType")
        desiredEncryption = self.get_desired_state_definition().get("EncryptionType")
        if currentEncryption != desiredEncryption and current_state.get("StreamStatus") == "ACTIVE":
            if desiredEncryption == 'NONE':
                KeyId = self.currentEncryption.get("StreamDescription").get("KeyId")
                self.client.stop_stream_encryption(StreamName=self.stream_name, EncryptionType=currentEncryption, KeyId=KeyId)
            else:
                self.client.start_stream_encryption(StreamName=self.stream_name, EncryptionType=desiredEncryption, KeyId=self.get_desired_state_definition().get("KeyId") )

    def get_status(self):
        try:
            current_definition = self.client.describe_stream_summary(StreamName=self.stream_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Stream {} was not found. State is terminated".format(self.stream_name))
                return None
            else:
                raise e

        return current_definition.get("StreamDescriptionSummary")
    #implement if needed

    def _need_update(self, curr_list, desired_list):
        """
        Checks to see if there are any differences in curr_list or desired_list. If they are different True is returned.
        Args:
            curr_list (list): list of dictionaries
            desired_list (list): list of dictionaries
        Returns:
             bool
        """
        # Checks if items need to be added or removed.
        add = list(itertools.filterfalse(lambda x: x in curr_list, desired_list))
        remove = list(itertools.filterfalse(lambda x: x in desired_list, curr_list))
        if add or remove:
            return True
