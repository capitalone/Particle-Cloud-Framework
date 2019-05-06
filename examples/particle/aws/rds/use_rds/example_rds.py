from pcf.particle.aws.rds.rds_instance import RDS
from pcf.core import State

particle_definition = {
    "pcf_name": "rds_test", # Required
    "flavor": "rds_instance", # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/rds.html#RDS.Client.create_db_instance for a full list of parameters
        "DBInstanceIdentifier": "test-instance", # Required
        "DBInstanceClass": "db.m3.medium", # Required
        "Engine": "postgres", # Required
        "MasterUsername": "postgres",
        "DBName": "myDB",
        "AllocatedStorage":10,
        "BackupRetentionPeriod":30,
        "AvailabilityZone":"us-east-1c",
        "EngineVersion":"9.6.2",
        "StorageEncrypted":True,
        "KmsKeyId":"KMS-ID",
        "Port":5432,
        "DBSubnetGroupName":"subnetgroupname",
        "VpcSecurityGroupIds":[
            "sg-11111111"
        ],
        "MasterUserPassword":"supersecret",
        "ApplyImmediately": True,
        "SkipFinalSnapshot": True,
        "DBParameterGroupName": "isrm-postgres96",
        "Tags": [
            {
                "Key": "email",
                "Value": "your.email@example.com"
            },
            {
                "Key": "name",
                "Value": "John Doe"
            }
        ],
        "SkipFinalSnapshot": True
    }
}

rds = RDS(particle_definition)

status = rds.get_status()

#Example for creating RDS instance
rds.set_desired_state(State.running)
rds.apply(sync=False)

#Example for updating RDS instance. RDS updates will happen during the maintenance window unless 'ApplyImmediately' field is set to true.
updated_def = particle_definition['aws_resource']['EngineVersion'] = "9.6.3"
rds = RDS(updated_def)
rds.set_desired_state(State.running)
rds.apply(sync=False)

#Example for deleting RDS instance
rds.set_desired_state(State.terminated)
rds.apply(sync=False)
print(rds.get_state())
