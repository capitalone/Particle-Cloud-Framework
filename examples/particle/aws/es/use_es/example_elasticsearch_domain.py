from pcf.core import State
from pcf.particle.aws.es.es_domain import ESDomain

#example es

es_example_json = {
    'pcf_name': 'pcf_es', #required
    'flavor': 'es', #required
    'aws_resource': {
        'DomainName': 'pcf-test-domain',
        'ElasticsearchVersion': '6.7',
        'ElasticsearchClusterConfig': {
            'InstanceType': 'm4.large.elasticsearch',
            'InstanceCount': 2,
            'ZoneAwarenessEnabled': True,
            'ZoneAwarenessConfig': {
                'AvailabilityZoneCount': 2
            }
        },
        'EBSOptions': {
            'EBSEnabled': True,
            'VolumeType': 'io1',
            'VolumeSize': 50,
            'Iops': 1000,
        },
#        'AccessPolicies': str({
#            'Version': '2012-10-17',
#            'Statement':[
#            {
#                'Effect': 'Allow',
#                'Principal': {
#                    'AWS': ["*"]
#                },
#                'Action': ['es:*'],
#                "Resource": 'arn:aws:es:us-east-1:471176887411:domain/pcf_test_domain/*'
#                }
#            ]
#        }),
        'SnapshotOptions' : {
            'AutomatedSnapshotStartHour': 0
        },
        'VPCOptions': {
            'SubnetIds': [
                'subnet-6bf0d333',
                'subnet-3738020a'
            ],
            'SecurityGroupIds': [
                'sg-2d991c57'
            ]
        },
        'EncryptionAtRestOptions': {
            'Enabled': True
        },
        'NodeToNodeEncryptionOptions': {
            'Enabled': True
        }
    }
}

es_particle = ESDomain(es_example_json)

#example start
es_particle.set_desired_state(State.running)
es_particle.apply()


