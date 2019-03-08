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

from pcf.particle.aws.ec2.alb.alb import ApplicationLoadBalancing
from pcf.core import State
from moto import mock_elbv2, mock_ec2

class TestALB():

    particle_definition = {
        "pcf_name": "alb-pcf",
        "flavor": "alb",
        "aws_resource": {
            "Name": "alb-pcf",
            "Scheme": "internal",
            "SecurityGroups": [],
            "Subnets": [],
            "Tags": [{'Key':'test', 'Value': 'test_value'}],
            "custom_config": {
                "Listeners": [
                    {
                        "LoadBalancerArn": "",  # Required
                        "Protocol": "HTTP",  # Required
                        "Port": 80,  # Required,
                        "DefaultActions": [
                            {
                                "Type": "forward",
                                "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/pcf-test"
                            }
                        ]
                    }
                ]
            },
        }
    }

    @mock_elbv2
    def test_get_current_def(self):
        particle = ApplicationLoadBalancing(self.particle_definition)
        des_def = particle.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @mock_elbv2
    @mock_ec2
    def test_get_status(self):
        client = boto3.client('elbv2', region_name='us-east-1')
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        vpc = ec2.create_vpc(CidrBlock='172.16.0.0/12', InstanceTenancy='default')
        subnet1 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1a'
        )
        subnet2 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1b'
        )
        client.create_load_balancer(
            Name='alb-pcf',
            Scheme='internal',
            Subnets=[subnet1.id, subnet2.id]
        )

        particle = ApplicationLoadBalancing(self.particle_definition)
        status = particle.get_status()

        assert status.get('LoadBalancerName') == 'alb-pcf'

    @mock_elbv2
    @mock_ec2
    def test_apply_states(self):
        client = boto3.client('elbv2', region_name='us-east-1')
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        security_group = ec2.create_security_group(
            GroupName='a-security-group', Description='First One')
        vpc = ec2.create_vpc(CidrBlock='172.16.0.0/12', InstanceTenancy='default')
        subnet1 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1a'
        )
        subnet2 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1b'
        )
        subnet3 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1c'
        )

        self.particle_definition["aws_resource"]["SecurityGroups"] = [security_group.id]
        self.particle_definition["aws_resource"]["Subnets"] = [subnet1.id, subnet2.id]
        particle = ApplicationLoadBalancing(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        # Moto always returns StatusCode provisioning so I have to manually test apply/update
        particle.apply(sync=False)

        assert particle.is_state_definition_equivalent() == True

        # Test update
        self.particle_definition["aws_resource"]["Subnets"] = [subnet1.id, subnet2.id, subnet3.id]
        particle = ApplicationLoadBalancing(self.particle_definition)
        particle.apply(sync=False)
        # Moto always returns StatusCode provisioning so I have to manually test apply/update
        particle.update()

        alb_status = particle.get_status()
        subnets = [x["SubnetId"] for x in alb_status['AvailabilityZones']]
        assert subnets == self.particle_definition["aws_resource"]["Subnets"]

    @mock_elbv2
    @mock_ec2
    def test_create_listeners(self):
        client = boto3.client('elbv2', region_name='us-east-1')
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        security_group = ec2.create_security_group(
            GroupName='a-security-group', Description='First One')
        vpc = ec2.create_vpc(CidrBlock='172.16.0.0/12', InstanceTenancy='default')
        subnet1 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1a'
        )
        subnet2 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='172.16.0.0/12',
            AvailabilityZone='us-east-1b'
        )

        # create target group required as a parameter for create_listener()
        response = client.create_target_group(
            Name='a-target',
            Protocol='HTTP',
            Port=8080,
            VpcId=vpc.id,
            HealthCheckProtocol='HTTP',
            HealthCheckPort='8080',
            HealthCheckPath='/',
            HealthCheckIntervalSeconds=5,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=5,
            UnhealthyThresholdCount=2,
            Matcher={'HttpCode': '200'})

        target_group = response.get("TargetGroups")[0]
        target_group_arn = target_group["TargetGroupArn"]

        self.particle_definition["aws_resource"]["SecurityGroups"] = [security_group.id]
        self.particle_definition["aws_resource"]["Subnets"] = [subnet1.id, subnet2.id]
        particle_with_listener = ApplicationLoadBalancing(self.particle_definition)

        # Test start
        particle_with_listener.set_desired_state(State.running)
        particle_with_listener.apply(sync=False)

        # Test listeners
        listeners = particle_with_listener.client.describe_listeners(LoadBalancerArn=particle_with_listener.arn)
        assert listeners['Listeners'][0]['Port'] == 80
