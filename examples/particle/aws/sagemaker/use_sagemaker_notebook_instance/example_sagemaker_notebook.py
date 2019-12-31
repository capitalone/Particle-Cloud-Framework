from pcf.particle.aws.sagemaker.notebook_instance import NotebookInstance
from pcf.core import State

# Edit example json to work in your account
notebook_instance_name = "pcf-test"
notebook_example_json = {
    "pcf_name": "pcf_notebook",  # Required
    "flavor": "sagemaker_notebook_instance",  # Required
    "aws_resource": {
        # Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_notebook_instance for full list of parameters
        "NotebookInstanceName": notebook_instance_name,  # Required
        "InstanceType": "ml.t2.medium",  # Required
        "RoleArn": "arn:aws:iam::123456789012:role/some-role",  # Required,
        "Tags": [
            {
                'Key': 'ggwp',
                'Value': 'lolcat'
            }
        ],

        "RootAccess": "Enabled"
    }
}

# create Sagemaker Notebook particle
notebook = NotebookInstance(notebook_example_json)

# example start
notebook.set_desired_state(State.running)
notebook.apply()

print(notebook.get_state())
rsp = notebook.client.create_presigned_notebook_instance_url(NotebookInstanceName=notebook_instance_name)
print(rsp.get("AuthorizedUrl"))


# example stop
notebook.set_desired_state(State.stopped)
notebook.apply()

print(notebook.get_state())


# example terminate
notebook.set_desired_state(State.terminated)
notebook.apply()

print(notebook.get_state())
