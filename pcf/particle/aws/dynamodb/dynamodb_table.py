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
from botocore.errorfactory import ClientError

import logging
import itertools

logger = logging.getLogger(__name__)


class DynamoDB(AWSResource):
    """
    This is the implementation of Amazon's DynamoDB service
    """

    flavor = "dynamodb_table"
    state_lookup = {
        "creating": State.pending,
        "updating": State.pending,
        "deleting": State.pending,
        "active": State.running
    }

    START_PARAM_FILTER = {
        "AttributeDefinitions",
        "TableName",
        "KeySchema",
        "ProvisionedThroughput",
        "LocalSecondaryIndexes",
        "GlobalSecondaryIndexes",
        "Tags"
    }

    UPDATE_PARAM_FILTER = {
        "AttributeDefinitions",
        "TableName",
        "ProvisionedThroughput",
        "GlobalSecondaryIndexUpdates",
        "StreamSpecification",
    }

    REMOVE_PARAM_FILTER = {
        "CreationDateTime",
        "TableArn",
        "TableSizeBytes",
        "TableStatus",
        "ItemCount",
    }

    THROUGHPUT_PARAM_FILTER = {
        "ReadCapacityUnits" ,
        "WriteCapacityUnits"
    }

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="dynamodb", session=session)
        self.table_name = self.desired_state_definition["TableName"]

    def _terminate(self):
        """
        Terminates the dynamodb particle that matches the table_name

        Returns:
            response of boto3 delete_table
        """
        return self.client.delete_table(TableName=self.table_name)

    def get_status(self):
        """
        Calls the describe table boto call and returns status missing if the function does not exist.
        Otherwise will return the current definition

        Returns:
            current definition
        """
        try:
            current_definition = self.client.describe_table(TableName=self.table_name)["Table"]

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Table {} was not found. State is terminated".format(self.table_name))
                return {"status": "missing"}
            else:
                raise e

        return current_definition

    def _start(self):
        """
        Starts the dynamodb particle that matches the desired state function

        Returns:
            reponse of boto3 create_table
        """

        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), DynamoDB.START_PARAM_FILTER)
        response = self.client.create_table(**start_definition)
        self._arn = response["TableDescription"]["TableArn"]

        return response

    def _stop(self):
        """
        DynamoDB does not have a stopped state so calls terminate.
        """

        return self._terminate()

    def sync_state(self):
        """
        DynamoDB implementation of sync state. Calls get status and sets the current state.
        """
        status_def = self.get_status()
        if status_def.get("status") == "missing":
            self.state = State.terminated
            return

        self.current_state_definition = status_def
        self.state = self.state_lookup[self.current_state_definition["TableStatus"].lower()]

    def put_item(self, item_value, **kwargs):
        """
        Puts an item in the DynamoDB table

        Args:
            item (dict): a map of attribute name/value pairs, one for each attribute
            **kwargs: options for boto3 put_item
        """
        return self.client.put_item(TableName=self.table_name, Item=item_value, **kwargs)

    def delete_item(self, key_value, **kwargs):
        """
        Deletes a single item in DynamoDB table by primary key

        Args:
            key_value(dict): a map of attribute names to AttributeValue objects
            **kwargs: options for boto3 delete_item
        """
        return self.client.delete_item(TableName=self.table_name, Key=key_value, **kwargs)

    def get_item(self, key_value, **kwargs):
        """
        Returns a set of attributes for the item with the given primary key

        Args:
            key_value(dict): a map of attribute names to AttributeValue objects
            **kwargs: options for boto3 get_item
        """
        return self.client.get_item(TableName=self.table_name, Key=key_value, **kwargs)

    def _update(self):
        """
        Updates the dynamodb particle to match current state definition.
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        if diff_dict != {}:
            new_desired_state_def["ProvisionedThroughput"] = pcf_util.param_filter(new_desired_state_def["ProvisionedThroughput"], DynamoDB.THROUGHPUT_PARAM_FILTER)
            update_definition = pcf_util.param_filter(new_desired_state_def, DynamoDB.UPDATE_PARAM_FILTER)
            self.client.update_table(**update_definition)

        # compare tags
        if self._arn:
            table_arn = self._arn
            current_tags = self.client.list_tags_of_resource(ResourceArn=table_arn)["Tags"]
        else:
            table_arn = self.current_state_definition.get("TableArn")
            current_tags =  self.client.list_tags_of_resource(ResourceArn=table_arn)["Tags"]

        desired_tags = self.desired_state_definition.get("Tags", [])

        if self._need_update(current_tags, desired_tags):
            add = list(itertools.filterfalse(lambda x: x in current_tags, desired_tags))
            remove = list(itertools.filterfalse(lambda x: x in desired_tags, current_tags))
            if remove:
                self.client.untag_resource(
                    ResourceArn=table_arn,
                    TagKeys=[x.get('Key') for x in remove]
                )
            if add:
                self.client.tag_resource(
                    ResourceArn=table_arn,
                    Tags=list(add)
                )

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and current state definitions.

        Returns:
            bool
        """
        self.get_state()
        current_definition = pcf_util.param_filter(self.current_state_definition, DynamoDB.REMOVE_PARAM_FILTER, True)
        desired_definition = pcf_util.param_filter(self.desired_state_definition, DynamoDB.START_PARAM_FILTER)

        # compare tags
        if self._arn:
          current_tags = self.client.list_tags_of_resource(ResourceArn=self._arn)["Tags"]
        else:
          current_tags =  self.client.list_tags_of_resource(ResourceArn=self.current_state_definition.get("TableArn"))["Tags"]

        desired_tags = desired_definition.get("Tags", [])

        new_desired_state_def, diff_dict = pcf_util.update_dict(current_definition, desired_definition)
        # self.create_table() does not return "Tags" as an attribute therefore, current_state_definition does not have
        # any reference to Tags, so it is removed from the comparison between current_definition and desired_definition
        diff_dict.pop('Tags', None)

        return diff_dict == {} and not self._need_update(current_tags, desired_tags)

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
        return False
