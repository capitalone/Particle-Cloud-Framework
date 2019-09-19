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
from pcf.core.pcf_exceptions import NoResourceException
from pcf.core import State
import time


class ECSCluster(AWSResource):
    """
    This is the implementation of Amazon's ECS Cluster.
    """

    flavor = "ecs_cluster"
    state_lookup = {
        "missing": State.terminated,
        "active": State.running,
        "inactive": State.terminated
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    UNIQUE_KEYS = ["aws_resource.clusterName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(
            particle_definition=particle_definition,
            resource_name="ecs",
            arn=particle_definition.get('arn'),
            session=session
        )
        self.cluster_name = self.desired_state_definition["clusterName"]

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECS Cluster

        """
        self.unique_keys = ECSCluster.UNIQUE_KEYS

    def get_label(self):
        """
        Returns:
            ECS Cluster name
        """
        return self.desired_state_definition["clusterName"]

    def _get_arn(self):
        """
        Calls boto3 describe_clusters() and parses response to get ECS Cluster arn

        Returns:
            ECS Cluster arn
        """
        cluster_status_resp = self.client.describe_clusters(
            clusters=[self.desired_state_definition["clusterName"]]
        )
        cluster_statuses = cluster_status_resp.get("clusters", [])

        if cluster_statuses:
            return cluster_statuses[0].get("clusterArn")
        else:
            raise NoResourceException()

    def get_status(self):
        """
        Calls boto3 describe_clusters using arn.

        Returns:
             status or {"status":"missing"}
        """
        try:
            cluster_status_resp = self.client.describe_clusters(clusters=[self.arn])
        except NoResourceException:
            return {"status": "missing"}

        except Exception as e:
            err_msg = e.args[0]
            # May be able to change this. Boto now reports missing in the response, not through exception
            if err_msg and err_msg.endswith("core is not a cluster"):
                return {"status": "missing"}
            else:
                raise e

        failures = cluster_status_resp.get("failures")
        if failures:
            for failure in failures:
                if failure.get('arn') == self.arn and 'MISSING' == failure.get('reason'):
                    return {"status": "missing"}
            raise Exception("cluster status returned unexpected results: {}".format(cluster_status_resp))

        return cluster_status_resp.get("clusters")[0]

    def _terminate(self):
        """
        Calls boto3 delete_cluster()

        Returns:
            boto3 delete_cluster() response
        """
        return self.client.delete_cluster(cluster=self.arn)

    def _start(self):
        """
        Calls boto3 create_cluster()

        Returns:
            boto3 create_cluster() response
        """
        return self.client.create_cluster(
            clusterName=self.desired_state_definition["clusterName"]
        )

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
            status = full_status.get("status", "missing").lower()
            self.state = ECSCluster.state_lookup.get(status)
            self.current_state_definition = full_status

    def _update(self):
        pass

    def is_state_equivalent(self, state1, state2):
        """
        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return ECSCluster.equivalent_states.get(state1) == ECSCluster.equivalent_states.get(state2)
