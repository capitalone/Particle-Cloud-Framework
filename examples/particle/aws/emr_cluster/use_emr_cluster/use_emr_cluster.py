from pcf.particle.aws.emr_cluster.emr_cluster import EMRCluster
from pcf.core import State

# Edit example json to work in your account
particle_definition_instance_group ={
    "pcf_name":"emr",
    "flavor":"emr_cluster",
    "aws_resource": {
        "ReleaseLabel":"emr-5.19.0",
        "Instances":{
            "KeepJobFlowAliveWhenNoSteps":True,
            "InstanceGroups":[{
                "InstanceRole":"MASTER",
                "Name":"master",
                "InstanceCount":1,
                "InstanceType":'m3.xlarge',
            }]
        },
        "JobFlowRole":"EMR_EC2_DefaultRole",
        "Name":"test",
        "ServiceRole":"EMR_DefaultRole"
    }
}

particle_definition_instance_fleet = {
    "pcf_name": "pcf_cluster",
    "flavor": "emr_cluster",
    "aws_resource": {
        "ReleaseLabel":"emr-5.19.0",
        "Instances":{
            "KeepJobFlowAliveWhenNoSteps":True,
            "InstanceFleets":[{
                "InstanceFleetType":"MASTER",
                "Name":"master",
                "TargetOnDemandCapacity":1,
                "InstanceTypeConfigs": [{
                    "InstanceType":'m3.xlarge',
                }]
            }]
        },
        "JobFlowRole":"EMR_EC2_DefaultRole",
        "Name":"test",
        "ServiceRole":"EMR_DefaultRole"
    }
}

# Input desired EMR config
emr = EMRCluster(particle_definition_instance_group)

# Start
emr.set_desired_state(State.running)
emr.apply()
print(emr.state)
print(emr.current_state_definition)

# Example Update (only updates non master instance counts, TargetOnDemandCapacity, or TargetSpotCapacity)
# particle_definition_instance_group["aws_resource"]["Instances"]["InstanceGroups"][0]["InstanceCount"] = 2
# particle_definition_instance_fleet["aws_resource"]["Instances"]["InstanceFleets"][0]["TargetOnDemandCapacity"] = 2
# emr = EMRCluster(particle_definition_instance_group)
# emr.set_desired_state(State.running)
# emr.apply()
# print(emr.state)
# print(emr.current_state_definition)

# Terminate
emr.set_desired_state(State.terminated)
emr.apply()
print(emr.state)
