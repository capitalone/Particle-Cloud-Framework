from pcf.core.gcp_resource import GCPResource
from pcf.core import State
from pcf.util import pcf_util
import googleapiclient.discovery
from google.cloud import exceptions
import logging

logger = logging.getLogger(__name__)


class VMInstance(GCPResource):

    """
    This is the implementation of Google's compute service.
    """
    flavor = "compute"

    state_lookup = {
        "RUNNING": State.running,
        "TERMINATED": State.terminated,
        "STOPPED": State.stopped,
        "SUSPENDED": State.terminated,
        "PROVISIONING": State.pending,
        "STAGING": State.pending,
        "STOPPING": State.pending,
        "SUSPENDING": State.pending,
    }
    equivalent_states = {}

    UNIQUE_KEYS = ["gcp_resource.name"]

    def __init__(self, particle_definition):
        super(VMInstance, self).__init__(particle_definition=particle_definition, resource=compute)
        self.name = self.desired_state_definition["name"]
        self.zone = self.custom_config["zone"]
        self.project = self.custom_config["project"]
        self._set_unique_keys()
        self._client = self.resource

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the storage bucket

        """
        self.unique_keys = VMInstance.UNIQUE_KEYS

    def get_status(self):
        """
        Determines if the instance exists

        Returns:
             status (dict)
        """
        try:
            instance = self.client.instances().get(project=self.project, zone=self.zone, instance=self.name).execute()
            if instance:
                return instance
            return {"status": "TERMINATED"}

        except:
            return {"status": "TERMINATED"}

    def _terminate(self):
        """
        Deletes the instance

        Returns:
             response of gcp instances().delete()
        """
        return self.client.instances().delete(project=self.project, zone=self.zone, instance=self.name).execute()

    def _start(self):
        """
        Creates the instance

        Returns:
             response of  gcp instances().insert()
        """
        return  self.client.instances().insert(project=self.project, zone=self.zone, body=self.get_desired_state_definition()).execute()

    def _stop(self):
        """
        Stops the instance
        """
        return self.client.instances().stop(project=self.project, zone=self.zone, instance=self.name).execute()

    def sync_state(self):
        """
        Calls get status and then sets the current state.
        """
        full_status = self.get_status()

        if full_status:
            if full_status.get('status'):
                self.state = VMInstance.state_lookup[full_status.get('status')]
            else:
                self.state = State.terminated

            self.current_state_definition = full_status

    def is_state_definition_equivalent(self):
        """
        Determines if desired_state_definition and current_state_definition are equivalent

        Returns:
             bool
        """
        logger.debug("is_state_definition_equivalent and _update are not implemented for {0}".format(self.get_pcf_id()))
        return True
        #TODO: This needs to be updated along with the _update implementation

        # filtered_desired_state_definition = pcf_util.param_filter(self.desired_state_definition,{"custom_config"}, remove=True)
        # diff = pcf_util.diff_dict(self.current_state_definition,filtered_desired_state_definition)
        #
        # if not diff or len(diff) == 0:
        #     return True
        #
        # return False

    def _update(self):
        """
        Not Implemented
        """
        pass
