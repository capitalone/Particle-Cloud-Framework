# Copyright 2019 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

pt = Blob(particle_definition)

pt.set_desired_state(State.running)
pt.apply()
print(pt.get_state())

pt.set_desired_state(State.terminated)
pt.apply()
print(pt.get_state())
