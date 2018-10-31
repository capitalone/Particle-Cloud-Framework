from pcf.particle.aws.s3.s3_bucket import S3Bucket
from pcf.core import State

import sys
import os

# Edit example json to work in your account
s3_bucket_example_json = {
    "pcf_name": "pcf_s3_bucket", # Required
    "flavor":"s3_bucket", # Required
    "aws_resource":{
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.create_bucket for full list of parameters
        "Bucket":"pcf-test", # Required
        "custom_config": {
            "Tags":{
                "Name": "pcf-s3-example"
            }
        }
    }
}

# create S3 Bucket particle
s3 = S3Bucket(s3_bucket_example_json)

# example start
s3.set_desired_state(State.running)
s3.apply()

print(s3.get_state())

# example put object
some_binary_data = b'Here we have some data'

print(s3.client.put_object(Bucket=s3.bucket_name, Key="test-object",Body=some_binary_data))
s3.resource.Bucket(s3.bucket_name).upload_file(Key="test-file", Filename=os.path.join(sys.path[0],"test.txt"))

# example get object

file_body = s3.client.get_object(Bucket=s3.bucket_name, Key="test-file")['Body']
for line in file_body._raw_stream:
    print(line)

# example get tags
print(s3.client.get_bucket_tagging(Bucket=s3.bucket_name).get("TagSet"))

# example terminate

s3.client.delete_object(Bucket=s3.bucket_name, Key="test-object")
s3.client.delete_object(Bucket=s3.bucket_name, Key="test-file")

s3.set_desired_state(State.terminated)
s3.apply()
s3.apply()

print(s3.get_state())
