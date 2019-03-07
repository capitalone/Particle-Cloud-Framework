from pcf.particle.aws.s3.s3_bucket import S3Bucket
from pcf.core import State
from pcf.quasiparticle.cross_cloud.cross_cloud_storage.cross_cloud_storage import CrossCloudStorage
import os
import sys

# Edit example json to work in your account
cross_cloud_storage_example = {
    "pcf_name": "cross_cloud_storage", # Required
    "flavor": "cross_cloud_storage",
    "storage_name": 'pcf-testing'
}

# create S3 Bucket particle
cross_cloud_storage = CrossCloudStorage(cross_cloud_storage_example)

# example start
cross_cloud_storage.set_desired_state(State.running)
cross_cloud_storage.apply()

print(cross_cloud_storage.get_state())

# example put object
some_binary_data = b'Here we have some data'

cross_cloud_storage.put_object(Bucket="pcf-testing", Key="test-object", Body=some_binary_data)
cross_cloud_storage.put_object(Bucket="pcf-testing", Key="test-file", Filename=os.path.join(sys.path[0],"test.txt"))

# example put terminate
cross_cloud_storage.delete_object(Bucket="pcf-testing", Key="test-object")
cross_cloud_storage.delete_object(Bucket="pcf-testing", Key="test-file")

cross_cloud_storage.set_desired_state(State.terminated)
cross_cloud_storage.apply()

print(cross_cloud_storage.get_state())

 