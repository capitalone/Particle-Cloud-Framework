from pcf.core.gcp_resource import GCPResource
from pcf.core import State
import logging
import io
from google.cloud import storage
from google.cloud import exceptions

logger = logging.getLogger(__name__)


class Bucket(GCPResource):

    """
    This is the implementation of Google's storage service.
    """
    flavor = "storage"

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    UNIQUE_KEYS = ["gcp_resource.name"]

    def __init__(self, particle_definition):
        super(Bucket, self).__init__(particle_definition=particle_definition, resource=storage)
        self.bucket_name = self.desired_state_definition["name"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the storage bucket

        """
        self.unique_keys = Bucket.UNIQUE_KEYS

    def get_status(self):
        """
        Determines if the bucket exists

        Returns:
             status (dict)
        """
        try:
            bucket = self.client.get_bucket(self.bucket_name)
            return bucket
        except exceptions.NotFound:
            return {"status": "missing"}

    def _terminate(self):
        """
        Deletes the storage bucket

        Returns:
             response of gcp delete
        """
        return self.client.bucket(bucket_name=self.bucket_name).delete()

    def _start(self):
        """
        Creates the storage bucket

        Returns:
             response of  create_bucket
        """

        return self.client.bucket(bucket_name=self.bucket_name).create()

    def _stop(self):
        """
        Storage bucket does not have a stopped state so it calls terminate.
        """
        return self.terminate()

    def sync_state(self):
        """
        Calls get status and then sets the current state.
        """
        full_status = self.get_status()

        if full_status:
            if isinstance(full_status, self.resource.Bucket):
                self.state = State.running
            else:
                self.state = State.terminated

            self.current_state_definition = self.desired_state_definition

    def download_object(self, blob_name, file_obj, **kwargs):
        """
        Downloads a file from the Storage bucket.

        Args:
            blob_name (str): Object name (Required)
            file_obj (str): file name for the download (Required)
            **kwargs: Options for gcp get_object (optional)
        """
        bucket = self.client.get_bucket(self.bucket_name)

        return self.resource.Blob(blob_name, bucket).download_file(file_obj, **kwargs)

    def delete_object(self, blob_name):
        """
        Deletes an object in the storage bucket.

        Args:
            blob_name (str): Object Key name (Required)
        """
        bucket = self.client.get_bucket(self.bucket_name)

        return bucket.delete_blob(blob_name)

    def list_objects(self, **kwargs):
        """
        Lists all objects in the storage bucket.

        Args:
            **kwargs: Options for gcp list_objects (optional)
        """
        bucket = self.client.get_bucket(self.bucket_name)
        return list(bucket.list_blobs(**kwargs))

    def put_object(self, blob_name, file_obj, **kwargs):
        """
        Puts an object in the Storage bucket.

        Args:
            blob_name (str): Object Key name (Required)
            file_obj (object): the object to put into the bucket (Required)
            **kwargs: Options for gcp put_object (optional)
        """
        bucket = self.client.get_bucket(self.bucket_name)
        stream = io.BytesIO(file_obj)

        return self.resource.Blob(blob_name, bucket).upload_from_file(stream, file_obj, **kwargs)

    def put_file(self, blob_name, file, **kwargs):
        """
        Puts a file in the Storage bucket.

        Args:
            blob_name (str): Object Key name (Required)
            file (file): the file to put into the bucket (Required)
            **kwargs: Options for gcp upload_file (optional)
        """
        bucket = self.client.get_bucket(self.bucket_name)

        return self.resource.Blob(blob_name, bucket).upload_from_filename(file, **kwargs)

    def _update(self):
        """
        Not Implemented
        """
        pass

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent. Uses equivalent_states defined in the Storage class.

        Args:
            state1 (State):
            state1 (State):

        Returns:
            bool
        """
        return Bucket.equivalent_states.get(state1) == Bucket.equivalent_states.get(state2)

