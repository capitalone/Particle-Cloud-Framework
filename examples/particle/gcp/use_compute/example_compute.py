from pcf.particle.gcp.compute.compute import ComputeEngine
from pcf.core import State


# Edit example json to work in your account

# to see full list of configurations see https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#insert
compute_example_json = {
    "pcf_name": "compute",
    "flavor": "compute",
    "gcp_resource": {
        "custom_config":{
            "project":"PROJECT",
            "zone":"us-east4-a"
        },
        "kind": "compute#instance",
        "name": "test",
        "machineType": "projects/PROJECT/zones/us-east4-a/machineTypes/f1-micro",
        "metadata": {}
        }
}


# create compute particle
compute = ComputeEngine(compute_example_json)

# example start
compute.set_desired_state(State.running)
compute.apply()

print(compute.get_state())
print(compute.current_state_definition)

# example terminate

compute.set_desired_state(State.terminated)
compute.apply()

print(compute.get_state())
