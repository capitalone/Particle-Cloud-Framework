from pcf.particle.aws.ecs.ecs_task import ECSTaskDefinition
from pcf.core import State

# example ECS Task Definition config json.
ecs_task_def_example_json = {
    "pcf_name": "task-def", # Required
    "flavor": "ecs_task_definition", # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.register_task_definition for full list of available properties
        "family": "pcf-ecs-task-def-example", # Required
        "containerDefinitions": [ # Required
            {
                "name": "pcf-ecs-task-def-example", # Required
                "memory": 60000,
                "cpu": 3800,
                "essential": True,
                "privileged": True,
                "image": "debian:jessie", # Required
                "portMappings": [
                    {
                        "hostPort": 0,
                        "containerPort": 8000,
                        "protocol": "tcp"
                    }
                ],
                "mountPoints": [
                    {
                        "containerPath": "/usr/local/folder",
                        "sourceVolume": "myfolder",
                        "readOnly": True
                    }
                ],
                "environment": [
                    {
                        "name": "http_proxy",
                        "value": "http://proxy.mycompany.com:8080"},
                    {
                        "name": "https_proxy",
                        "value": "http://proxy.mycompany.com:8080"
                    },
                    {
                        "name": "no_proxy",
                        "value": "localhost,127.0.0.1,169.254.169.254,169.254.170.2,.mycompany.com"
                    }
                ],
            }
        ],
        "volumes": [
            {
                "host": {
                    "sourcePath": "/var/lib/somefolder/"
                },
                "name": "myfolder"
            }
        ]
    }
}

# Setup ecs_cluster particle using a sample configuration
ecs_task_definition = ECSTaskDefinition(ecs_task_def_example_json)

# example start
ecs_task_definition.set_desired_state(State.running)
ecs_task_definition.apply()

print(ecs_task_definition.get_state())
print(ecs_task_definition.get_current_state_definition())
