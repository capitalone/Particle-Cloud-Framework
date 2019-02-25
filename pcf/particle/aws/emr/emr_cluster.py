# Copyright 2018 Capital One Services, LLC
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

from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.util import pcf_util
from pcf.core.pcf_exceptions import NoResourceException

import logging
logger = logging.getLogger(__name__)


class EMRCluster(AWSResource):
    """
    This is the implementation of Amazon's ECS Cluster.
    """

    flavor = "emr_cluster"
    state_lookup = {
        "starting": State.pending,
        "bootstrapping": State.pending,
        "running": State.running,
        "waiting": State.running,
        "terminating": State.pending,
        "terminated": State.terminated,
        "missing": State.terminated,
        "terminated_with_errors": State.terminated
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    UPDATE_PARAM_CONVERSIONS = {
        "RequestedInstanceCount":"InstanceCount",
        "TargetOnDemandCapacity":"TargetOnDemandCapacity",
        "TargetSpotCapacity":"TargetSpotCapacity"
    }

    FILTERED_UPDATE_PARAMS = {
        "InstanceCount",
        "TargetOnDemandCapacity",
        "TargetSpotCapacity"
    }

    UNIQUE_KEYS = ["aws_resource.Name"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="emr", session=session)
        self.name = self.desired_state_definition["Name"]

    def _set_unique_keys(self):
        """
            Logic that sets keys from state definition that are used to uniquely identify the EMR Cluster
        """
        self.unique_keys = EMRCluster.UNIQUE_KEYS

    def _get_cluster_id(self):
        """
        Get's the cluster Id of the EMR cluster based on cluster name

        Returns:
            ClusterId
        """

        cluster_id = self.current_state_definition.get('Cluster', {}).get("Id")
        if not cluster_id:
            emr_clusters = self.client.list_clusters(ClusterStates=["STARTING","BOOTSTRAPPING","RUNNING","WAITING","TERMINATING"])
            filtered_clusters = [cluster["Id"] for cluster in emr_clusters["Clusters"] if cluster['Name'] == self.name]
            if len(filtered_clusters) == 0:
                return None
            cluster_id = filtered_clusters[0]

        return cluster_id

    def get_status(self):
        """
        Calls boto3 describe_clusters using arn.

        Returns:
             status or {"status":"missing"}
        """
        try:
            cluster_id = self._get_cluster_id()
            if not cluster_id:
                return {"status": "missing"}

            cluster_status_resp = self.client.describe_cluster(ClusterId=cluster_id)
            cluster_type = cluster_status_resp["Cluster"].get("InstanceCollectionType","INSTANCE_GROUP")
            if cluster_type == "INSTANCE_GROUP":
                instance_groups = self.client.list_instance_groups(ClusterId=cluster_id)
                cluster_status_resp["Cluster"]["Instances"] = pcf_util.list_to_dict(key_name='Name',dict_list=instance_groups["InstanceGroups"])

            # INSTANCE_FLEET
            else:
                instance_fleets = self.client.list_instance_fleets(ClusterId=cluster_id)
                cluster_status_resp["Cluster"]["Instances"] = pcf_util.list_to_dict(key_name='Name',dict_list=instance_fleets["InstanceFleets"])

        except NoResourceException:
            return {"status": "missing"}

        return cluster_status_resp.get("Cluster")

    def _terminate(self):
        """
        Calls boto3 terminate_job_flows()

        Returns:
            boto3 terminate_job_flows() response
        """
        return self.client.terminate_job_flows(JobFlowIds=[self._get_cluster_id()])

    def _start(self):
        """
        Calls boto3 run_job_flow()

        Returns:
            boto3 run_job_flow() response
        """
        response = self.client.run_job_flow(**self.desired_state_definition)
        if self.custom_config.get("Tags"):
            tags = self.custom_config.get("Tags")
            tag_set = []
            for k, v in tags.items():
                tag_set.append({
                    "Key": k,
                    "Value": v
                })

            self.client.add_tags(
                ResourceId=self._get_cluster_id(),
                Tags=tag_set
            )
        return response

    def _stop(self):
        """
        Calls _terminate()
        """
        return self.terminate()

    def sync_state(self):
        """
        Calls get_status() and updates the current_state_definition and the state.
        """
        full_status = self.get_status()

        if full_status:
            status = full_status.get("Status", {}).get("State","missing").lower()
            self.state = EMRCluster.state_lookup.get(status)
            self.current_state_definition = full_status

    def _update(self):
        # only updates InstanceCount

        desired_instances = self.desired_state_definition.get("Instances").get("InstanceGroups")

        # instance pool
        if not desired_instances:
            desired_instances = self.desired_state_definition.get("Instances").get("InstanceFleets")

        # TODO neither pool or group
        if not desired_instances:
            return True

        desired_instance_dict = pcf_util.list_to_dict("Name", desired_instances)
        desired_instance_dict = {k : pcf_util.param_filter(v,EMRCluster.FILTERED_UPDATE_PARAMS) for k,v in desired_instance_dict.items()}
        current_instance_dict = {k : pcf_util.keep_and_replace_keys(v,EMRCluster.UPDATE_PARAM_CONVERSIONS) for k,v in self.current_state_definition.get("Instances").items()}
        diff = pcf_util.diff_dict(current_instance_dict,desired_instance_dict)

        for k,v in diff.items():
            curr_instance = self.current_state_definition["Instances"].get(k,{}).get('Id')
            #instance group
            if curr_instance and self.current_state_definition["Instances"].get(k,{}).get('InstanceGroupType'):
                self.client.modify_instance_groups(ClusterId=self._get_cluster_id(),
                                                   InstanceGroups=[{"InstanceGroupId":curr_instance,"InstanceCount":v["InstanceCount"]["updated"]}])
            #instance pool
            elif curr_instance:
                od_cap = v.get("TargetOnDemandCapacity",{}).get("updated",0)
                spot_cap = v.get("TargetSpotCapacity",{}).get("updated",0)
                self.client.modify_instance_fleet(ClusterId=self._get_cluster_id(),
                                                  InstanceFleet={"InstanceFleetId":curr_instance,"TargetOnDemandCapacity":od_cap,"TargetSpotCapacity":spot_cap})


    def is_state_equivalent(self, state1, state2):
        """
        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return EMRCluster.equivalent_states.get(state1) == EMRCluster.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Determines if current state is equivalent to the desired state.

        Returns:
             bool
        """
        desired_instances = self.desired_state_definition.get("Instances").get("InstanceGroups")

        # instance pool
        if not desired_instances:
            desired_instances = self.desired_state_definition.get("Instances").get("InstanceFleets")

        # TODO neither pool or group
        if not desired_instances:
            return True

        desired_instance_dict = pcf_util.list_to_dict("Name", desired_instances)
        desired_instance_dict = {k : pcf_util.param_filter(v,EMRCluster.FILTERED_UPDATE_PARAMS) for k,v in desired_instance_dict.items()}
        current_instance_dict = {k : pcf_util.keep_and_replace_keys(v,EMRCluster.UPDATE_PARAM_CONVERSIONS) for k,v in self.current_state_definition.get("Instances").items()}

        # moto bug with instance fleets
        if not current_instance_dict:
            return True

        diff = pcf_util.diff_dict(current_instance_dict,desired_instance_dict)

        return diff == {}


