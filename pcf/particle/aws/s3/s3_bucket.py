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


class S3Bucket(AWSResource):
    """
    This is the implementation of Amazon's S3 service.
    """
    flavor = "s3_bucket"
    state_lookup = {
        "missing": State.terminated,
        "active": State.running,
        "inactive": State.terminated
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAMS_FILTER = {
        "ACL",
        "Bucket",
        "CreateBucketConfiguration",
        "GrantFullControl",
        "GrantRead",
        "GrantReadACL",
        "GrantReadACP",
        "GrantWrite",
        "GrantWriteACP",
    }

    UNIQUE_KEYS = ["aws_resource.Bucket"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="s3", session=session)
        self.bucket_name = self.desired_state_definition["Bucket"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the S3 Bucket
        """
        self.unique_keys = S3Bucket.UNIQUE_KEYS

    def get_status(self):
        """
        Determines if the bucket exists
        Returns:
             status (dict)
        """
        bucket_object = self.resource.Bucket(self.bucket_name)
        if bucket_object.creation_date:
            return {"status":"active"}
        else:
            return {"status": "missing"}

    def _terminate(self):
        """
        Deletes the S3 bucket
        Returns:
             response of boto3 delete_bucket
        """
        return self.client.delete_bucket(Bucket=self.bucket_name)

    def _start(self):
        """
        Creates the S3 bucket
        Adds Tags to the S3 bucket if specified in custom_config
        Returns:
             response of boto3 create_bucket
        """
        create_definition = pcf_util.param_filter(self.get_desired_state_definition(), S3Bucket.START_PARAMS_FILTER)
        response = self.client.create_bucket(**create_definition)

        if self.custom_config.get("Tags"):
            tags = self.custom_config.get("Tags")
            tag_set = []
            for k, v in tags.items():
                tag_set.append({
                    "Key": k,
                    "Value": v
                })

            self.client.put_bucket_tagging(
                Bucket=self.bucket_name,
                Tagging={
                    "TagSet":tag_set
                }
            )

        return response

    def _stop(self):
        """
        S3 bucket does not have a stopped state so it calls terminate.
        """
        return self.terminate()

    def sync_state(self):
        """
        Calls get status and then sets the current state.
        """
        full_status = self.get_status()

        if full_status:
            status = full_status.get("status", "missing").lower()
            self.state = S3Bucket.state_lookup.get(status)

            # need way to determine current state definition without making so many api calls
            self.current_state_definition = self.desired_state_definition

    def _update(self):
        """
        Not Implemented
        """
        pass

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent. Uses equivalent_states defined in the S3Bucket class.
        Args:
            state1 (State):
            state1 (State):
        Returns:
            bool
        """
        return S3Bucket.equivalent_states.get(state1) == S3Bucket.equivalent_states.get(state2)
