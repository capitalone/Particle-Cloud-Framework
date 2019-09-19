from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.util import pcf_util
import json
import logging
from deepdiff import DeepDiff

logger = logging.getLogger(__name__)


class KMSKey(AWSResource):
    """
    This is an instantiation of an AWS KMS key. For now, only CMKs stored in KMS are supported.
    Keys in External or CloudHSM stores will be added later. The creation of a KMS key does not
    require any inputs with the exception of a :code:`key_name`, which is used to create an "alias"
    for the key. Aliases are unique per region. Upon particle termination, the alias will be
    deleted and the key will be marked for termination (since KMS keys cannot be deleted
    immediately). If the key name/alias given already exists, the particle will be mapped to that
    key, rather than create one from scratch.

    **aws_resource Definition**

    Args:
        custom_config (dict): **[REQUIRED]** A dictionary containing configuration values:

            - :code:`key_name` (str) - **[REQUIRED]** A string used to uniquely identify the key.\
            Transformed into an alias for the key. No spaces.

        Policy (str): A JSON-formatted policy string for the key
        Description (str): A description of the key, visible in the AWS console and CLI calls
        BypassPolicyLockoutSafetyCheck (boolean): A flag used in conjunction with the policy
        parameter to indicate if the . Default value is :code:`False` For more info, see
        `AWS docs <http://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html>`_.
        Tags (list): A list of key-value dictionaries with tag information:

            - :code:`{}` (dict) Containing the following keys:

                - :code:`TagKey` (str) - **[REQUIRED]** The tag name
                - :code:`TagValue` (str) - **[REQUIRED]** The tag value


    Example minimal particle definition:
    code::
        particle_definition = {
            'pcf_name': 'kms_example',
            'flavor': 'kms_key',
            'aws_resource': {
                "custom_config": {
                    "key_name": "kms_alias_name"
                }
            }
        }

    The following states can be handled by the particle:

    +----------------+------------------+-------------------------------------------------------+
    | Particle State | KMS Key State    | Notes                                                 |
    +================+==================+=======================================================+
    | Running        | Enabled          | Will create key if DNE, will adopt key if alias given |
    +----------------+------------------+-------------------------------------------------------+
    | Stopped        | Disabled         | No need to disable prior to deletion                  |
    +----------------+------------------+-------------------------------------------------------+
    | Terminated     | Pending Deletion | Schedules key for deletion in 30 days, removes alias  |
    +----------------+------------------+-------------------------------------------------------+
    | Pending        | Pending Import   | Not used by KMS-generated keys, not supported         |
    +----------------+------------------+-------------------------------------------------------+
    | Pending        | Unavailable      | Not used by KMS-generated keys, not supported         |
    +----------------+------------------+-------------------------------------------------------+

    """

    flavor = 'kms_key'
    """
    Name of the particle type, used in the particle definition
    """

    state_lookup = {
        "Enabled": State.running,
        "PendingDeletion": State.terminated,
        "PendingImport": State.pending,
        "Unavailable": State.pending,
        "Disabled": State.stopped
    }
    """
    Mapping of PCF states to the KMS states used by AWS. Used after describe calls to determine 
    latest state.
    """

    # No required AWS params.
    START_PARAMS = {
        "Policy",
        "Description",
        "CustomKeyStoreId",
        "BypassPolicyLockoutSafetyCheck",
        "Tags"
    }
    """
    A set of the params used by the AWS API in the create_key operation. Used as a filter for 
    the return of describe_key, in order to check if the state is equivalent to the definition.
    """

    UNIQUE_KEYS = ["aws_resource.custom_config.key_name"]
    """
    The key used to uniquely identify the particle. User supplied.
    """

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name='kms', session=session)
        self._set_unique_keys()
        self.key_name = self.desired_state_definition.get('custom_config').get('key_name')

    def sync_state(self):
        """
        Required method: Logic that updates the current state of the particle. Used in methods in
        the base class(es).

        Works by fetching the latest key information, then setting the current_state_definition
        equal to the result. Also updates particle state before exiting.
        """
        status = self._get_status()
        if not status:
            self.state = State.terminated
            self.current_state_definition = {}
            return
        # Remove the BypassPolicyLockout key from the input. Not returned by methods, cant change
        self.desired_state_definition.pop('BypassPolicyLockoutSafetyCheck', None)
        if 'Tags' in self.desired_state_definition:
            status["Tags"] = self.client.list_resource_tags(KeyId=status.get('KeyId')).get('Tags')
        if 'Policy' in self.desired_state_definition:
            status["Policy"] = self.client.get_key_policy(KeyId=status.get('KeyId'),
                                                          PolicyName='default')
        self.current_state_definition = status
        self.state = KMSKey.state_lookup.get(status.get('KeyState'))

    def is_state_definition_equivalent(self):
        """
        Overridden method from base class (particle.py), responsible for testing if the particle
        has reached its desired state.

        Original method ran a diff_dict on the current_state_definition and the
        desired_state_definition (A.K.A. the resource from the particle configuration). Since the
        return of the describe_key operation is used to set the current_state_definition, and it
        would never contain the custom_config key, it was necessary to force a filtering before the
        comparison operation.

        Returns:
            bool
        """
        # Policy, Tags, BypassSafetyLockout not returned by describe API.
        current_filtered = pcf_util.param_filter(self.current_state_definition,
                                                 KMSKey.START_PARAMS)
        desired_filtered = pcf_util.param_filter(self.desired_state_definition,
                                                 KMSKey.START_PARAMS)
        """
        The following code does two diff operations. Here is why:
        
        The create key API and the describe policy API take/return a JSON formatted string for the 
        policy. Since the user has to supply a string, and since the operations dealing with the 
        policy all take a string, the idea of deserializing their input (and the return of the 
        other APIs) doesn't seem right. It would confuse the update process (assuming update for 
        policies is introduced), and it would add a bit more serialization than is necessary.

        The solution used here was to keep the policy as a JSON-formatted string in the state 
        dictionaries. However, this means if a DeepDiff is performed on the strings, there is a 
        high chance of failure just due to formatting and ordering, even if the policies are the 
        same. So first, if there is a Policy attribute, do a DeepDiff of just the JSON parsed from 
        the strings of both, then if they match, remove the elements from the dictionaries. Then 
        there is another DeepDiff on the rest of the state, which wont fail erroneously now that 
        the policy strings have been removed.

        There is another fun little detail to note here. By deleting the policy from the desired 
        state definition, it prevents future lookups of the policy, and comparisons of the policy 
        with the current state, since both are only performed if the Policy key is present. When 
        the user goes to update the policy, the key is reintroduced, and this whole process would 
        happen once more.
        """
        if 'Policy' in desired_filtered:
            policy_diff = DeepDiff(json.loads(desired_filtered['Policy']),
                                   json.loads(current_filtered['Policy']), ignore_order=True)
            if policy_diff:
                logger.debug("Key policy is not equivalent for {0} with diff: {1}".format(
                    self.key_name, json.dumps(policy_diff)))
                logger.warning(
                    'Update for policies not implemented. Will assert equivalence (incorrectly)')
                # TODO: Change to return False once policy updates are supported
                return True
            # Remove policy strings since they are equivalent
            desired_filtered.pop('Policy')
            current_filtered.pop('Policy')
        diff = DeepDiff(desired_filtered, current_filtered, ignore_order=True)
        if not diff or len(diff) == 0:
            return True
        else:
            print(diff)
            logger.debug("State is not equivalent for {0} with diff: {1}".format(
                self.get_pcf_id(), diff))
            return False

    def _terminate(self):
        """
        Required method: Used in methods in the base class(es).

        Schedules the deletion of the key. CMKs cannot be deleted immediately. Defaults to 30 days.
        Also deletes alias associated with key, so the particle can be re-used immediately, even if
        the key isn't technically deleted yet.

        Returns:
            dict (response of boto3 kms schedule_key_deletion)
        """
        response = self.client.schedule_key_deletion(KeyId=self.current_state_definition.get(
            'KeyId'))
        self.client.delete_alias(AliasName='alias/'+self.key_name)
        return response

    def _start(self):
        """
        Required method: Used in methods in the base class(es).

        Creates a customer-managed key (CMK), or if the alias specified already exists, re-enables
        an existing one. The functionality needs to be mixed, since this function is called in both
        the Terminated --> Running and the Stopped --> Running state transitions. Return object is
        supplied for convenience, and is not used in any operations.

        Returns:
            dict (response of boto3 kms create_key or enable_key, depending on transition type)
        """
        if self.current_state_definition:
            return self.client.enable_key(KeyId=self.current_state_definition.get('KeyId'))
        else:
            # TODO add check for KeyId in desired state definition so existing keys can be reused
            start_definition = pcf_util.param_filter(self.get_desired_state_definition(),
                                                     KMSKey.START_PARAMS)
            create_response = self.client.create_key(**start_definition)
            # TODO add a check for uniqueness of alias
            self.client.create_alias(AliasName='alias/'+self.key_name,
                                     TargetKeyId=create_response.get('KeyMetadata').get('KeyId'))
            return create_response

    def _stop(self):
        """
        Required method: Used in methods in the base class(es).

        This method will disable the key. Return object is supplied for convenience, and is not
        used in any operations.

        Returns:
            dict (response of disable_key function)
        """
        return self.client.disable_key(KeyId=self.current_state_definition.get('KeyId'))

    def _update(self):
        """
        Required method: Used in methods in the base class(es).

        Currently does nothing. Needs to be implemented for updates that do not change state, such
        as modifying tags or description.
        """
        logger.debug("update is not implemented for {0}".format(self.get_pcf_id()))

    def _set_unique_keys(self):
        """
        Required method: Used in methods in the base class(es).

        Sets the instance variable for unique_keys to the value of the class variable. Bad things
        happen if this method or both instantiations of the unique_keys variable do not exist.
        """
        self.unique_keys = KMSKey.UNIQUE_KEYS

    def _get_status(self):
        """
        Using the :code:`_get_alias()` method, this method will query for the a key that has the
        name specified, and return the result of the describe_key API call for that key. If DNE,
        returns empty dictionary.

        Note: The setting of the instance attribute :code:`_arn` is done in this method. It cannot
        be done in the start method, since the method may not be called if the key already exists.
        This method is called by sync_state, so it is always run.

        Returns:
             dict ('KeyMetadata' from describe_key API call, or empty if DNE)
        """
        alias = self._get_alias()
        status = {} if not alias else self.client.describe_key(KeyId=alias.get('TargetKeyId')).get('KeyMetadata')
        if not self._arn:
            self._arn = status.get('Arn')
        if not hasattr(self, 'key_id') and status:
            self.key_id = status.get('KeyId')
        return status

    def _validate_config(self):
        """
        Custom logic that that validates particle's configurations
        """
        # TODO implement - add checks for spaces in key_name, required fields, etc.
        raise NotImplementedError

    def _get_arn(self):
        """
        Returns the ARN of the key.

        Returns:
             str
        """
        return self._arn

    def _get_alias(self):
        """
        Returns the alias record for the provided key_name in custom configuration.

        Returns:
             :code:`{}` (dict) Containing nothing, or the keys above:
                 - :code:`AliasName` (str) -  The alias name (always starts with "alias/")
                 - :code:`AliasArn` (str) - The ARN for the key alias
                 - :code:`TargetKeyId` (str) - The unique identifier for the key the alias is\
                    associated with
        """
        alias_list = self.client.list_aliases()
        for alias in alias_list.get('Aliases'):
            if alias.get('AliasName') == 'alias/' + self.key_name:
                return alias
        return {}
