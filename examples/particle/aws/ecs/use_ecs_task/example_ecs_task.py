from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.particle.aws.ecs.ecs_task_definition import ECSTaskDefinition
from pcf.particle.aws.ecs.ecs_task import ECSTask
from pcf.core import State
from pcf.core.pcf import PCF

# Example ECS Cluster config json
# ECS Cluster is a required parent for ECS Service
ecs_cluster_example_json = {
    "pcf_name": "pcf_ecs_cluster",  # Required
    "flavor": "ecs_cluster",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.create_cluster for full list of parameters
        "clusterName": "pcf_example"  # Required
    }
}
# Setup required parent ecs_cluster particle using a sample configuration
ecs_cluster = ECSCluster(ecs_cluster_example_json)

# Example ECS Task Definition config json
# ECS Task Defintion is a required parent for ECS Service
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
# Setup required parent ecs_task_definition particle using a sample configuration
ecs_task_def = ECSTaskDefinition(ecs_task_def_example_json)

# example ECS Task config json
ecs_task_example_json = {
    "pcf_name": 'pcf_ecs_service', # Required
    "flavor": "ecs_service", # Required
    "parents": [
        ecs_cluster.get_pcf_id(),  # Required. This replaces Cluster in aws_resource
        ecs_task_def.get_pcf_id()  # Required. This replaces taskDefinition in aws_resource
    ],
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.run_task for a full list of parameters
        #"count": 1, # Required
        "launchType": "EC2"
    }
}
# Setup ecs_service particle using a sample configuration
ecs_task = ECSTask(ecs_task_example_json)

pcf = PCF([])
pcf.add_particles((
    ecs_cluster,
    ecs_task_def,
    ecs_task,
))
pcf.link_particles(pcf.particles)
pcf.apply(sync=True, cascade=True)

# example start
ecs_cluster.set_desired_state(State.running)
ecs_task_def.set_desired_state(State.running)
ecs_task.set_desired_state(State.running)
pcf.apply(sync=True, cascade=True)

print(ecs_task.get_state())
print(ecs_task.get_current_state_definition())

# example terminate
# ecs_task.set_desired_state(State.terminated)
# ecs_task.set_desired_state(State.terminated)
# ecs_task.set_desired_state(State.terminated)
# pcf.apply(sync=True, cascade=True)
# print(ecs_task.get_state())
