from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.core import State

# example ECS Cluster config json
ecs_cluster_example_json = {
    "pcf_name": "pcf_ecs_cluster",  # Required
    "flavor": "ecs_cluster",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.create_cluster for full list of parameters
        "clusterName": "pcf_example"  # Required
    }
}

# Setup ecs_cluster particle using a sample configuration
ecs_cluster = ECSCluster(ecs_cluster_example_json)

# example start
ecs_cluster.set_desired_state(State.running)
ecs_cluster.apply()

print(ecs_cluster.get_state())
print(ecs_cluster.get_current_state_definition())

# example terminate
ecs_cluster.set_desired_state(State.terminated)
ecs_cluster.apply()

print(ecs_cluster.get_state())
