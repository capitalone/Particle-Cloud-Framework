import moto
import json
import pytest
import boto3
import os
import placebo
from pcf.util import pcf_util
from pcf.core import State
from pcf.core import particle_flavor_scanner
from contextlib import ExitStack

from pcf.particle.aws.route53 import hosted_zone
from pcf.particle.aws.sqs.sqs_queue import SQSQueue
from pcf.particle.aws.cloudfront.cloudfront_distribution import CloudFrontDistribution
from pcf.particle.aws.cloudwatch.cloudwatch_event import CloudWatchEvent
from pcf.particle.aws.cloudwatch.cloudwatch_log import CloudWatchLog
from pcf.particle.aws.dynamodb.dynamodb_table import DynamoDB
from pcf.particle.aws.ec2.autoscaling.launch_configuration import LaunchConfiguration
from pcf.particle.aws.ec2.elb.elb import ElasticLoadBalancing
from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.particle.aws.ecs.ecs_task_definition import ECSTaskDefinition
from pcf.particle.aws.efs.efs_instance import EFSInstance
from pcf.particle.aws.emr.emr_cluster import EMRCluster
from pcf.particle.aws.kms.kms_key import KMSKey
from pcf.particle.aws.s3.s3_bucket import S3Bucket
from pcf.particle.aws.sns.sns_topic import SNSTopic
from pcf.particle.aws.vpc.vpc_instance import VPCInstance

directory = os.path.dirname(__file__)
file = os.path.join(directory, 'testdata.json')
with open(file) as f:
    testdata = json.load(f)

values = testdata.values()
values = [tuple(v) for v in values]


@pytest.mark.parametrize("definition,changes,test_type", values, ids=list(testdata.keys()))
def test_apply(definition, changes, test_type):
    flavor = definition.get("flavor")
    particle_class = particle_flavor_scanner.get_particle_flavor(flavor)
    session = None
    with ExitStack() as stack:
        if test_type[0] == "placebo":
            session = boto3.Session()
            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, test_type[1])
            pill = placebo.attach(session, data_path=filename)
            pill.playback()
        else:
            for context in test_type:
                stack.enter_context(getattr(moto, context)())
        # create
        particle = particle_class(definition, session)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running
        # print(particle.current_state_definition, particle.desired_state_definition)
        assert particle.is_state_definition_equivalent()
        # update
        if changes:
            updated_definition, diff = pcf_util.update_dict(definition, changes)
            if changes.get("aws_resource", {}).get("Tags"):
                updated_definition["aws_resource"]["Tags"] = changes.get("aws_resource", {}).get("Tags")
            elif changes.get("aws_resource", {}).get("tags"):
                updated_definition["aws_resource"]["tags"] = changes.get("aws_resource", {}).get("tags")
            particle = particle_class(updated_definition, session)
            particle.set_desired_state(State.running)
            particle.apply(sync=True)
            assert particle.is_state_definition_equivalent()
        # terminate
        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated
