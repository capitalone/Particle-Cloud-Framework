import json
import base64
from pcf.particle.aws.sagemaker.notebook_lifecycle_config import NotebookLifecycleConfig
from pcf.core import State

file = open("./onstart.sh", "rb").read()
onCreate = base64.b64encode(file).decode('utf-8')

config_example_json = {
    "pcf_name": "pcf_notebook_lifecycle_config",  # Required
    "flavor": "sagemaker_notebook_lifecycle_config",  # Required
    "aws_resource": {
        # Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_notebook_instance for full list of parameters
        "NotebookInstanceLifecycleConfigName": "pcf-test-sagemaker-lifecycle-config",
        "OnCreate": [{"Content": onCreate}],
        # "OnStart": [{"Content": "./blah.sh"}],
    }
}

# create Sagemaker Notebook Lifecycle Config particle
config = NotebookLifecycleConfig(config_example_json)

# example start
config.set_desired_state(State.running)
config.apply()

print(config.get_state())

# example terminate
config.set_desired_state(State.terminated)
config.apply()

print(config.get_state())