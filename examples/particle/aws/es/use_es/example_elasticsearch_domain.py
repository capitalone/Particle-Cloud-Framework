from pcf.core import State
from pcf.particle.aws.es.es_domain import ESDomain

#example es domain

es_example_json = {
    'pcf_name': 'pcf_es-1', #required
    'flavor': 'es', #required
    'aws_resource': {
        'DomainName': 'pcf-test-domain-1',
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
        },
        'Tags': [
            {
                'Key': 'ASV',
                'Value': 'ASVCLOUDCUSTODIAN'
            },
            {
                'Key': 'OwnerContact',
                'Value': 'janitorialservices@capitalone.com'
            },
            {
                'Key': 'CMDBEnvironment',
                'Value': 'ENVNPCLOUDMAID'
            }
        ]
    }
}

es_particle = ESDomain(es_example_json)

#example start
es_particle.set_desired_state(State.running)
es_particle.apply()

es_example_json['aws_resource']['SnapshotOptions']['AutomatedSnapshotStartHour'] = 1
es_example_json['aws_resource']['Tags'][1]['Value'] = 'zhb257'
es_example_json['aws_resource']['NodeToNodeEncryptionOptions']['Enabled'] = False

es_particle = ESDomain(es_example_json)
es_particle.set_desired_state(State.running)
es_particle.apply()

es_particle.set_desired_state(State.terminated)

