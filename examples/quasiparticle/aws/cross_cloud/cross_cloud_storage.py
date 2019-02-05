from pcf.particle.aws.s3.s3_bucket import S3Bucket
from pcf.core import State
from pcf.quasiparticle.cross_cloud.cross_cloud_storage import CrossCloudStorage
import os
import sys

# Edit example json to work in your account
cross_cloud_storage_example = {
    "pcf_name": "cross_cloud_storage", # Required
    "flavor": "cross_cloud_storage",
    "particles": [{
        "flavor":"s3_bucket", # Required
            "aws_resource":{
                # Refer to https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.create_bucket for full list of parameters
                "Bucket":"pcf-testing", # Required
                "custom_config": {
                    "Tags":{
                        "Name": "pcf-s3-example"
                    }
                }
            }
        },
    {
        "flavor":"storage", # Required
            "gcp_resource":{
                # Refer to https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.create_bucket for full list of parameters
                "name":"pcf-testing", # Required
            }
    }]
}


# create S3 Bucket particle
cross_cloud_storage = CrossCloudStorage(cross_cloud_storage_example)

# example start
cross_cloud_storage.set_desired_state(State.running)
cross_cloud_storage.apply()

print(cross_cloud_storage.get_state())

# example put object
some_binary_data = b'Here we have some data'

print(cross_cloud_storage.put_object(Bucket="pcf-testing", Key="test-object", Body=some_binary_data))
print(cross_cloud_storage.put_object(Bucket="pcf-testing", Key="test-object", Filename=os.path.join(sys.path[0],"test.txt")))

# example put terminate
cross_cloud_storage.delete_object(Bucket="pcf-testing", Key="test-object")
cross_cloud_storage.delete_object(Bucket="pcf-testing", Key="test-file")

cross_cloud_storage.set_desired_state(State.terminated)
cross_cloud_storage.apply()

# print(cross_cloud_storage.get_state())
