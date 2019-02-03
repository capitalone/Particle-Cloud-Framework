from pcf.particle.gcp.storage.storage import Storage
from pcf.core import State

import sys
import os

# Edit example json to work in your account
storage_example_json = {
    "pcf_name": "pcf_storage", # Required
    "flavor":"storage", # Required
    "gcp_resource":{
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.create_bucket for full list of parameters
        "Bucket":"example_bucket", # Required
    }
}


# create storage record particle
storage = Storage(storage_example_json)

# example start
storage.set_desired_state(State.running)
storage.apply()

print(storage.get_state())

# example put object
some_binary_data = b'Here we have some data'

print(storage.put_object(blob_name="test-object",file_obj=some_binary_data))
print(storage.put_file(blob_name="test-file", file=os.path.join(sys.path[0],"test.txt")))

# example get object

file_body = storage.get_object(key_name="test-file")['Body']
for line in file_body._raw_stream:
    print(line)

# example terminate

storage.delete_object(blob_name="test-object")
storage.delete_object(blob_name="test-file")

storage.set_desired_state(State.terminated)

storage.apply()

print(storage.get_state())
