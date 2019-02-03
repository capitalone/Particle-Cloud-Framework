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
import hashlib
import logging
import boto3
import codecs

from botocore.errorfactory import ClientError

logger = logging.getLogger(__name__)


class LambdaFunction(AWSResource):
    """This is the implementation of Amazon's lambda service. This particle works with function code in a zipfile located
    locally and in s3. Note that having a zipfile locally versus s3 has a slightly different configuration format.
    """
    flavor = "lambda_function"
    START_PARAM_FILTER = {
        "FunctionName",
        "Runtime",
        "Role",
        "Handler",
        "Code",
        "Description",
        "Timeout",
        "MemorySize",
        "Publish",
        "VpcConfig",
        "DeadLetterConfig",
        "Environment",
        "KMSKeyArn",
        "TracingConfig",
        "Tags",
    }

    RETURN_PARAM_FILTER = {
        "FunctionName",
        "Runtime",
        "Role",
        "Handler",
        "Description",
        "Timeout",
        "MemorySize",
        "VpcConfig",
        "DeadLetterConfig",
        "Environment",
        "KMSKeyArn",
        "TracingConfig",
        "CodeSha256",
    }

    UPDATE_PARAM_FILTER = {
        "FunctionName",
        "Runtime",
        "Role",
        "Handler",
        "Description",
        "Timeout",
        "MemorySize",
        "VpcConfig",
        "DeadLetterConfig",
        "Environment",
        "KMSKeyArn",
        "TracingConfig",
    }

    S3_PARAM_CONVERSIONS = {
        "S3Bucket": "Bucket",
        "S3Key": "Key",
        "s3ObjectVersion": "VersionId"
    }

    UNIQUE_KEYS = ["aws_resource.FunctionName"]

    def __init__(self, particle_definition):
        super(LambdaFunction, self).__init__(particle_definition=particle_definition,
                                     resource_name="lambda")
        self.function_name = self.desired_state_definition["FunctionName"]
        self.is_zip_local = True if self.desired_state_definition['Code'].get("ZipFile") else False
        self._s3_client = None
        self.desired_state_definition["CodeSha256"] = self.__zipfile_to_sha256()

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Lambda Function

        """
        self.unique_keys = LambdaFunction.UNIQUE_KEYS

    def _terminate(self):
        """
        Starts the lambda particle that matches the function_name

        :return: response of boto3 delete_function
        """
        return self.client.delete_function(FunctionName=self.function_name)

    def get_status(self):
        """
        Calls the get function configuration boto call and returns status missing if the function does not exist.
        Otherwise will return the current definition.

        Returns:
            current definition
        """
        try:
            current_definition = self.client.get_function_configuration(FunctionName=self.function_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Function {} was not found. State is terminated".format(self.function_name))
                return {"status": "missing"}
            else:
                raise e

        return current_definition

    def _start(self):
        """
        Starts the lambda particle that matches desired state definition

        :return: response of boto3 create_function
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        start_definition = pcf_util.param_filter(new_desired_state_def, LambdaFunction.START_PARAM_FILTER)
        if self.is_zip_local:
            start_definition["Code"]["ZipFile"] = self.file_get_contents()

        self.client.create_function(**start_definition)

    def _stop(self):
        """
        Lambda function does not have a stopped state so calls terminate.
        """
        return self.terminate()

    def sync_state(self):
        """
        Lambda function implementation of sync state. Calls get status and sets the current state.
        """
        status_def = self.get_status()
        if status_def.get("status") == "missing":
            self.state = State.terminated
            return

        self.current_state_definition = status_def
        self.state = State.running

    def file_get_contents(self):
        """Function gets and reads contents of local zipfile

        Returns:
            file contents
        """
        filename = self.desired_state_definition["Code"]["ZipFile"]
        with open(filename, 'rb') as f:
            return f.read()


    @property
    def s3client(self):
        """
        Create a s3 client if the zipfile is located in s3.

        Returns:
            s3 client
        """
        if not self._s3_client:
            region_name = self.particle_definition["aws_resource"].get("region_name")
            self._s3_client = boto3.client("s3", region_name=region_name)
        return self._s3_client

    def _update(self):
        """
            Updates the lambda function particle to match current state definition. There is a different
            function call if the update is the function code in the zipfile or a configuration variable.

        """
        if self.desired_state_definition["CodeSha256"] != self.current_state_definition["CodeSha256"]:
            if self.is_zip_local:
                self.client.update_function_code(FunctionName=self.function_name, ZipFile=self.file_get_contents())
            else:
                self.client.update_function_code(FunctionName=self.function_name, **self.desired_state_definition["Code"])

            self.desired_state_definition["CodeSha256"] = self.__zipfile_to_sha256()

        # update lambda configuration other than the code
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        update_definition = pcf_util.param_filter(new_desired_state_def, LambdaFunction.UPDATE_PARAM_FILTER)
        if diff_dict != {}:
            self.client.update_function_configuration(**update_definition)

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and current state definitions.

        Returns:
            bool
        """
        self.get_state()
        desired_definition = pcf_util.param_filter(self.desired_state_definition, LambdaFunction.RETURN_PARAM_FILTER)
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, desired_definition)
        return diff_dict == {}

    def __zip_local_to_sha256(self):
        """
        Hashes the contents of a local zipfile using sha256

        Returns:
            base 64 hash
        """
        with open(self.desired_state_definition["Code"]["ZipFile"], "rb") as f:
            zfile = f.read()
        hashed_zfile = hashlib.sha256(zfile).hexdigest()
        hashed_b64 = codecs.encode(codecs.decode(hashed_zfile, 'hex'), 'base64').decode().strip('\n')
        return hashed_b64

    def __s3_to_sha256(self):
        """
       Looks to see if the zipfile located in s3 has a tag with the latest sha256. If there is no tag it calculates the hash
       and adds the tag.

       Returns:
           base 64 hash
       """
        s3_kwargs = pcf_util.keep_and_replace_keys(self.desired_state_definition["Code"], LambdaFunction.S3_PARAM_CONVERSIONS)

        # check if tag already contains hashed value
        tags = self.s3client.get_object_tagging(**s3_kwargs)
        for kv in tags["TagSet"]:
            if kv['Key'] == "CodeSha256":
                return kv['Value']

        obj = self.s3client.get_object(**s3_kwargs)
        zfile = obj["Body"].read()
        hashed_zfile = hashlib.sha256(zfile).hexdigest()
        hashed_b64 = codecs.encode(codecs.decode(hashed_zfile, 'hex'), 'base64').decode().strip('\n')
        self.s3client.put_object_tagging(Tagging={"TagSet": [{"Key": "CodeSha256", "Value": hashed_b64}]}, **s3_kwargs)
        return hashed_b64

    def __zipfile_to_sha256(self):
        """returns the contents of the lambda code as a sha256 hash. There is a separate process for the code
        stored locally or in s3

        Returns:
            hash

        """
        if self.is_zip_local:
            return self.__zip_local_to_sha256()

        else:
            return self.__s3_to_sha256()








