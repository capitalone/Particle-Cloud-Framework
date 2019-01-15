import moto
import pytest
from pcf.core import State
from pcf.core import particle_flavor_scanner

from pcf.particle.aws.route53 import hosted_zone


@pytest.mark.parametrize("definition,updated_definition,mototag", [
    (
        {
            "pcf_name": "pcf_hosted_zone",
            "flavor": "route53_hosted_zone",
            "aws_resource": {
                "Name": "www.hoooooos.com.",
                "custom_config": {
                    "Tags": [
                        {
                            "Key": "Owner",
                            "Value": "Hoo"
                        },
                        {
                            "Key": "UID",
                            "Value": "abc123"
                        }
                    ]
                },
                "VPC": {
                    "VPCRegion": "us-east-1",
                    "VPCId": "vpc-12345"
                },
                "CallerReference": "werhasdkfboi12hasdfak",
                "HostedZoneConfig": {
                    "Comment": "hoo",
                    "PrivateZone": True
                },
                # "DelegationSetId": ""
                }
        },
        {
            "pcf_name": "pcf_hosted_zone",
            "flavor": "route53_hosted_zone",
            "aws_resource": {
                "Name": "www.hoooooos.com.",
                "custom_config": {
                    "Tags": [
                        {
                            "Key": "Owner",
                            "Value": "Hoo"
                        },
                        {
                            "Key": "UID",
                            "Value": "abc123"
                        }
                    ]
                },
                "VPC": {
                    "VPCRegion": "us-east-1",
                    "VPCId": "vpc-12345"
                },
                "CallerReference": "werhasdkfboi12hasdfak",
                "HostedZoneConfig": {
                    "Comment": "hoo",
                    "PrivateZone": True
                },
                # "DelegationSetId": ""
                }
        },
        "mock_route53"
    ),
])
def test_apply(definition, updated_definition, mototag):
    flavor = definition.get("flavor")
    particle_class = particle_flavor_scanner.get_particle_flavor(flavor)
    mock = getattr(moto, mototag)
    with mock():
        particle = particle_class(definition)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running

        particle = particle_class(updated_definition)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.is_state_definition_equivalent()

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated
