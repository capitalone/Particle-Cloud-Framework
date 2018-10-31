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

import boto3
import os
from pcf.core.pcf_exceptions import InvalidValueReplaceException
from pcf.core.pcf_exceptions import ResourceLookupNotDefinedException


class AWSLookup:
    """
    Class of all the AWS lookup resources

    """
    methods = locals()

    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

    ec2_resource = boto3.resource("ec2", region_name=region_name)
    ec2_client = boto3.client("ec2", region_name=region_name )

    def __init__(self, resource, names):
        self.resource = resource
        self.names = names

    def get_id(self):
        method = self.methods.get(self.resource)
        if not method:
            raise ResourceLookupNotDefinedException("{} resource lookup does not exist".format(self.resource))
        resource_id = method(self)
        if not resource_id:
            raise ResourceLookupNotDefinedException("No {} resource with {} name".format(self.resource, self.names))
        return resource_id

    def instance_name(self):
            """
            Given instance-id this returns the instance name for ec2.

            Returns:
                 instance_name
            """
            instance_tags = self.ec2_client.describe_tags(Filters=[
                    {
                            'Name': 'resource-id',
                            'Values': self.names
                    },
                    {
                           'Name': 'key',
                            'Values': ['PCFName']
                    },
                ])

            if len(instance_tags['Tags']) != 1:
                    raise InvalidValueReplaceException("instance id is not valid")
            return instance_tags['Tags'][0]['Value']

    def ami(self):
        """
        Uses boto3 api call to get latest ami id

        Returns:
            Image ID with corresponding Image name
        """
        images = self.ec2_resource.images.filter(
            Filters=[
                {
                    'Name': 'name',
                    'Values': self.names
                },
            ],
        )
        image_id = [image.image_id for image in images]
        if len(image_id) > 1:
            raise InvalidValueReplaceException("Ami name returned more than one id")
        if not image_id:
            return None
        return image_id[0]

    def security_groups(self):
        """
        Uses boto3 api call to get latest security group ids

        Returns:
            List of security group IDs
        """
        security_groups = self.ec2_client.describe_security_groups(
            GroupNames=self.names
        )["SecurityGroups"]
        group_ids = []
        for group in security_groups:
            group_ids.append(group["GroupId"])
        return group_ids

    def subnet(self):
        """
        Uses boto3 api call to get latest subnet id

        Returns:
            Subnet ID with corresponding Subnet name
        """
        subnets = self.ec2_client.describe_subnets(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': self.names
                },
            ],
        )["Subnets"]
        if subnets:
            return subnets[0]["SubnetId"]
        return None

    def snapshot(self):
        """
        Uses boto3 api call to get latest snapshot id

        Returns:
            Snapshot ID of Snapshot with corresponding name
        """
        snapshots = self.ec2_client.describe_snapshots(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': self.names
                },
            ],
        )["Snapshots"]
        if snapshots:
            return snapshots[0]["SnapshotId"]
        return None

    def iam(self):
        """
        Used boto3 api call to get latest iam role

        Returns:
            Either instance profile or role with given name
        """
        iam = boto3.client("iam")
        try:
            arn_type = self.names[0]
            name = self.names[1]
            arn = None
            if arn_type == "instance-profile":
                arn = iam.get_instance_profile(InstanceProfileName=name)["InstanceProfile"]["Arn"]
            if arn_type == "role":
                arn = iam.get_role(RoleName=name)["Role"]["Arn"]
            return arn
        except Exception:
            return None

