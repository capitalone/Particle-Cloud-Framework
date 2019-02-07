from pcf.particle.azure.storage.blob import Blob
from pcf.core import State


particle_definition = {
    "pcf_name": "pcf_storage", # Required
    "flavor": "blob", # Required
    "azure_resource": {
        "name": "pcf-blob", # Required
        "storage_account": "wahoo", # Required
        "resource_group": "hoo-resource-group", # Required
        "public": True
    }
}

blob = Blob(particle_definition)

blob.set_desired_state(State.running)
blob.apply()
print(blob.get_state())

blob.set_desired_state(State.terminated)
blob.apply()
print(blob.get_state())
