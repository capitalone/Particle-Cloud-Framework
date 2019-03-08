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

import time
import logging
import json
import commentjson

from pcf.core import State, STATE_STRING_TO_ENUM, pcf_exceptions
from pcf.util import pcf_util

logger = logging.getLogger(__name__)


class MetaParticle(type):
    def __new__(cls, name, bases, namespace):
        new_class = type.__new__(cls, name, bases, dict(namespace))

        if not hasattr(cls, 'registry'):
            cls.registry = {}

        flavor = namespace.get("flavor", None)

        if flavor and isinstance(flavor, str):
            cls.registry[flavor.lower()] = new_class

        return new_class


class Particle(object, metaclass=MetaParticle):
    flavor = None
    """
    Type of particle
    """

    def __init__(self, particle_definition):
        """
        Args:
            particle_definition(json): Particle definition in json format. Depends of each particle
            implementation, but always requires a pcf_name field.
        """
        # If particle definition is passed as a json file, load it as a dictionary and continue
        if isinstance(particle_definition, str):
            with open(particle_definition) as file:
                particle_definition = commentjson.loads(file.read())
            file.close()
        self.particle_definition = particle_definition
        self.name = self.particle_definition["pcf_name"]
        self.validate_unique_id()
        self.persist_on_termination = self.particle_definition.get("persist_on_termination", False)
        self.persist_on_update = self.particle_definition.get("persist_on_update", False)
        self.callbacks = self.particle_definition.get("callbacks", {})
        self.desired_state = STATE_STRING_TO_ENUM.get(self.particle_definition.get("desired_state"))
        self.current_state_definition = {}
        self.desired_state_definition = {}
        self.custom_config = {}
        self.pcf_id = self.get_pcf_id()
        self.state_transition_table = {
            (State.terminated, State.running): self.start,
            (State.stopped, State.running): self.start,
            (State.stopped, State.terminated): self.terminate,
            (State.running, State.stopped): self.stop,
            (State.running, State.terminated): self.terminate
        }
        self.parents = set()
        self.children = set()

        self.current_state_transiton = None
        self.current_state_transition_start_time = None

        self.state_last_refresh_time = None
        self.state_cache_ttl = 15
        self.state_dirty = False

        self.unique_keys = []

    def get_pcf_id(self):
        """
        generates an pcf id using the flavor and the pcf name

        Returns:
            pcf id
        """
        return pcf_util.generate_pcf_id(self.flavor, self.name)

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition using dot notation that are used to uniquely identify the instance
        of this particle
        """
        raise NotImplementedError

    def validate_unique_id(self):
        """
        Throws an error if particle flavor or any unique identifiers are missing
        """
        flavor_name = self.particle_definition.get("flavor")
        if not flavor_name:
            raise pcf_exceptions.FlavorMissingException
        try:
            # get list from UNIQUE_KEYS
            unique_identifier_list = pcf_util.get_particle_unique_identifiers(flavor_name)

            for uid in unique_identifier_list:
                if not pcf_util.find_nested_dict_value(self.particle_definition, uid.split('.')):
                    raise pcf_exceptions.InvalidUniqueKeysException
        except AttributeError:
            # UNIQUE_KEYS list does not exist - disregard and move on (Only when UNIQUE_KEYS is not defined in a class)
            pass

    def get_state(self):
        """
        Calls sync state and afterward returns the current state. Uses cached state if available.

        Returns:
            state
        """
        if not self.use_cached_state():
            self.sync_state()
            self.state_last_refresh_time = time.time()
            logger.info("Refreshed state for {0}: {1}".format(self.pcf_id, self.state))
        else:
            logger.debug("Using cached state for {0}: {1}".format(self.pcf_id, self.state))
        return self.state

    def sync_state(self):
        """
        Logic that determines what the current state of the particle is. This is implemented for each individual
        particle

        """
        raise NotImplementedError

    def use_cached_state(self):
        """
        Returns true if the last cached time is greater than cache_ttl variable.

        Returns:
             bool
        """
        if self.state_dirty or not self.state_last_refresh_time:
            self.state_dirty = False
            return False
        else:
            time_delta = time.time() - self.state_last_refresh_time
            if time_delta > self.state_cache_ttl:
                return False
        return True

    def set_desired_state(self, desired_state):
        """
        Sets the particle's desired state

        Arg:
            desired_state (str): one of running,stopped,terminated.
        """
        if isinstance(desired_state, str):
            self.desired_state = STATE_STRING_TO_ENUM.get(desired_state.lower())
            if not self.desired_state:
                raise pcf_exceptions.InvalidState
        else:
            self.desired_state = desired_state
        logger.info("{0}: setting desired state to {1}".format(self.pcf_id, self.desired_state))

    def measure(self):
        return self.__dict__

    def _validate_config(self):
        """
        Custom logic that that validates particle's configurations
        """
        raise NotImplementedError

    def apply(self, sync=True, cascade=False, validate_config=False, max_timeout=None, src_cascade=None, cache_ttl=15):
        """
        Triggers the state transition functions based on the state transition table.

        Args:
            sync (bool): apply state transitions synchronously
            cascade (bool): apply state transitions to all family members
            validate_config (bool): specify whether or not to call particle config validation function
            max_timeout (int): raise the max timeout exception after x(int) seconds reached, defaults to None
            src_cascade ("parent","child", or "none"): direction of cascade logic
            cache_ttl (int): allows self.state_cache_ttl to be configured to any time interval
        Returns:
            State transition response
        """
        if max_timeout:
            start_timeout = time.time()

        logger.debug("{0}: start applying state transition with modes: sync={1} cascade={2} validate_config={3}".format(self.pcf_id, sync,
                                                                                                    cascade, validate_config))

        if validate_config:
            self._validate_config()

        state_transition_response = None

        if cache_ttl < 10:
            raise pcf_exceptions.InvalidCacheTTLException

        self.state_cache_ttl = cache_ttl
        if self.desired_state:
            self.apply_cascade("parent", desired_state=self.desired_state, sync=sync, src_cascade=src_cascade)

            # persist particle on terminate
            if self.persist_on_termination is True and self.desired_state == State.terminated:
                logger.debug("{0}: termination protection is set to True".format(self.pcf_id))
                return True

            # pass in parent variables to desired state definition
            if cascade:
                self.get_and_replace_parent_variables()

            while not self.is_state_equivalent(self.get_state(), self.desired_state):
                if max_timeout and (time.time() - start_timeout) >= max_timeout:
                    raise pcf_exceptions.MaxTimeoutException

                if self.state == State.pending:
                    self.wait()

                    if not sync: break
                else:
                    logger.debug(
                        "{0}: current state ({1}) doesn't match the desired_state ({2}) retrieving state transition function".format(
                            self.pcf_id, self.state, self.desired_state))
                    state_transition_func = self.get_state_transition_function(self.state, self.desired_state)

                    if not state_transition_func:
                        raise Exception("Invalid state transition for {0} from {1} to {2}".format(self.name, self.state,
                                                                                                  self.desired_state))

                    self.current_state_transiton = (self.state, self.desired_state)
                    self.current_state_transition_start_time = time.time()
                    state_transition_response = state_transition_func(sync=sync, cascade=cascade)

                    # trigger callback
                    if state_transition_response and self.callbacks.get(state_transition_func.__name__):
                        if not self.callbacks.get(state_transition_func.__name__)["function"]:
                            raise pcf_exceptions.NoCallbackFunctionException

                        if self.callbacks.get(state_transition_func.__name__).get("kwargs"):
                            kwargs = self.callbacks.get(state_transition_func.__name__)["kwargs"]
                            if kwargs.get("particle"):
                                kwargs["particle"] = self  # pass self to function as kwarg
                            self.callbacks.get(state_transition_func.__name__)["function"](**kwargs)
                        else:
                            self.callbacks.get(state_transition_func.__name__)["function"]()

                    self.state_dirty = True

                    if not sync: break

                    self.wait()

            while self.get_state() == self.desired_state == State.running and not self.is_state_definition_equivalent():
                if max_timeout and (time.time() - start_timeout) >= max_timeout:
                    raise pcf_exceptions.MaxTimeoutException

                try:
                    logger.debug(
                        "{0}: current_state_definition ({1}) doesn't match the desired_state_definition ({2})".format(
                            self.pcf_id, json.dumps(self.current_state_definition),
                            json.dumps(self.get_desired_state_definition())))
                except Exception:
                    logger.debug(
                        "{0}: current_state_definition ({1}) doesn't match the desired_state_definition ({2})".format(
                            self.pcf_id, self.current_state_definition, self.get_desired_state_definition()))

                # persist particle on update
                if self.persist_on_update:
                    logger.debug("{0}: update protection is set to True".format(self.pcf_id))
                    break

                if self.state == State.pending:
                    self.wait()

                    if not sync: break
                else:
                    self.state_dirty = True
                    self.update(sync=sync, cascade=cascade)

                if not sync: break
                self.wait()

        self.current_state_transiton = None
        self.current_state_transition_start_time = None

        if not state_transition_response:
            return {"msg": "The current state for {0} is already at {1} state".format(self.name, self.get_state())}

        return state_transition_response

    def apply_cascade(self, direction, desired_state=None, sync=True, src_cascade=None):
        """
        Args:
            direction ("parent","child", or "none"): direction of cascade logic
            desired_state: the desired state of the particle
            sync (bool): apply state transitions synchronously
            src_cascade ("parent","child", or "none"): direction of cascade logic
        """
        if direction and (not src_cascade or src_cascade == direction):
            if direction.lower() == "parent":
                if not desired_state: desired_state = self.desired_state

                for parent in self.parents:
                    if desired_state and not parent.desired_state:
                        parent.set_desired_state(self.desired_state)
                    parent.apply(sync=sync, cascade=True, src_cascade=direction)

                    if (not parent.is_state_equivalent(parent.desired_state, parent.get_state())
                        or not parent.is_state_definition_equivalent()):
                        return False
            elif direction.lower() == "child":
                for child in self.children:
                    if desired_state and not child.desired_state:
                        child.set_desired_state(self.desired_state)
                    # skip child apply if child has persist_on_termination set to True
                    if child.persist_on_termination is True and self.desired_state == State.terminated:
                        logger.debug("{0}: termination protection is set to True".format(child.pcf_id))
                    else:
                        child.apply(sync=sync, cascade=True, src_cascade=direction)

                        if (not child.is_state_equivalent(child.desired_state, child.get_state())
                            or not child.is_state_definition_equivalent()):
                            return False

        return True

    def get_and_replace_parent_variables(self):
        """
        Checks the particles desired state definition and checks to see if there are values that
        dependent on one of its parents.
        The format should look like $flavor:pcf_name$key_in_parent_current_state_definition.
        If there are values then this function looks for the corresponding parents and adds those
        values to this particles desired_state_definition.
        """
        var_lookup_list = pcf_util.find_nested_vars(self.desired_state_definition, var_list=[])
        for (nested_key, id_var) in var_lookup_list:
            if id_var[0] == "inherit":
                pcf_id = id_var[1]
                parent_var = id_var[2]
                try:
                    parent = next(p for p in self.parents if p.pcf_id == pcf_id)
                except StopIteration:
                    raise pcf_exceptions.InvalidValueReplaceException("{} parent was not found".format(pcf_id))
                else:
                    var = pcf_util.find_nested_dict_value(curr_dict=parent.current_state_definition,
                                                            list_nested_keys=parent_var.split('.'))
                    if not var:
                        raise pcf_exceptions.InvalidValueReplaceException("{} var was not found in {}".format(parent_var, pcf_id))
                pcf_util.replace_value_nested_dict(curr_dict=self.desired_state_definition,
                                                     list_nested_keys=nested_key.split('.'), new_value=var)

    def register_state_transition(self, start_state, end_state, transition_function):
        """
        Registers the correct transition function

        Args:
            start_state: starting state of the transition
            end_state: ending state of the transition
            transition_function: associated transition function
        """
        self.state_transition_table[(start_state, end_state)] = transition_function

    def get_state_transition_function(self, start_state, end_state):
        """
        Gets the corresponding transition function

        Args:
            start_state: starting state of the transition
            end_state: ending state of the transition
        """
        return self.state_transition_table.get((start_state, end_state), None)

    def start(self, sync=True, cascade=False):
        """
        Calls sync state then calls _start()

        Args:
            sync (bool): apply state transitions synchronously
            cascade (bool): apply state transitions to all family members

        """
        logger.debug(
            "{0}: start starting particle with modes: sync={1} cascade={2}".format(self.pcf_id, sync, cascade))

        if cascade:
            if not self.apply_cascade("parent", desired_state=State.running, sync=sync): return

        self.sync_state()
        return self._start()

    def _start(self):
        """
        Logic that starts the particle. This is implemented for each individual
        particle
        """
        raise NotImplementedError

    def stop(self, sync=True, cascade=False):
        """
        Calls sync state then calls _stop()

        Args:
            sync (bool): apply state transitions synchronously
            cascade (bool): apply state transitions to all family members
        """
        logger.debug(
            "{0}: start stopping particle with modes: sync={1} cascade={2}".format(self.pcf_id, sync, cascade))

        if cascade:
            if not self.apply_cascade("child", desired_state=State.stopped, sync=sync): return

        self.sync_state()
        return self._stop()

    def _stop(self):
        """
        Logic that stops the particle. This is implemented for each individual
        particle
        """
        raise NotImplementedError

    def terminate(self, sync=True, cascade=False):
        """
        Calls sync state then calls _terminate()

        Args:
            sync (bool): apply state transitions synchronously
            cascade (bool): apply state transitions to all family members
        """
        logger.debug(
            "{0}: start terminating particle with modes: sync={1} cascade={2}".format(self.pcf_id, sync, cascade))

        if cascade:
            if not self.apply_cascade("child", desired_state=State.terminated, sync=sync): return

        self.sync_state()
        return self._terminate()

    def _terminate(self):
        """
        Logic that terminates the particle. This is implemented for each individual
        particle
        """
        raise NotImplementedError

    def update(self, sync=True, cascade=False):
        """
        Calls sync state then calls _update()

        Args:
            sync (bool): apply state transitions synchronously
            cascade (bool): apply state transitions to all family members
        """
        logger.debug(
            "{0}: start updating particle with modes: sync={1} cascade={2}".format(self.pcf_id, sync, cascade))
        resp = self._update()

        if cascade:
            if not self.apply_cascade("child", sync=sync): return
        return resp

    def _update(self):
        """
        Logic that updates the particle. This is implemented for each individual
        particle
        """
        raise NotImplementedError

    def link_relatives(self, pcf):
        """
        links children and parents to each other

        Args:
            pcf: pcf field
        """
        parents = self.particle_definition.get("parents", [])
        for parent in parents:
            self.link_to_parent(pcf, parent)

        children = self.particle_definition.get("children", [])
        for child in children:
            self.link_to_child(pcf, child)

    def link_to_parent(self, pcf, parent_pcf_id):
        """
        Adds parent id to pcf parents list and adds self to children list

        Args:
            pcf: pcf field
            parent_pcf_id: parent pcf id
        """
        parent = pcf.get_particle_from_pcf_id(parent_pcf_id)
        if parent:
            self.parents.add(parent)
            parent.children.add(self)
        else:
            raise Exception("Context missing parent {}".format(parent_pcf_id))

    def link_to_child(self, pcf, child_pcf_id):
        """
        Adds child id to pcf children list and adds self to parent list

        Args:
            pcf: pcf field
            child_pcf_id: child pcf id
        """
        child = pcf.get_particle_from_pcf_id(child_pcf_id)
        if child:
            self.children.add(child)
            child.parents.add(self)
        else:
            raise Exception("Context missing child {}".format(child_pcf_id))

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent.

        Args:
            state1:
            state2:
        Returns:
             bool
        """
        return state1 == state2

    def is_state_definition_equivalent(self):
        """
        Determines if state definitions are equivalent

        Returns:
            bool
        """
        self.get_state()
        diff = pcf_util.diff_dict(self.current_state_definition, self.get_desired_state_definition())

        if not diff or len(diff) == 0:
            return True
        else:
            # can't json dump function
            if diff.get('callbacks'):
                diff['callbacks'] = {'new':'<function>'}
            logger.debug("State is not equivalent for {0} with diff: {1}".format(self.get_pcf_id(), json.dumps(diff)))
            return False

    def get_desired_state_definition(self):
        """
        Returns:
            desired_state_definition
        """
        return self.desired_state_definition

    def get_current_state_definition(self):
        """
        Returns:
            current_state_definition
        """
        return self.current_state_definition

    def wait(self):
        time.sleep(1)

    def get_attribute_value(self, attribute_key, state_definition_to_use="c>d", default=None):
        definitions_to_use = state_definition_to_use.split(">")
        definitions = []

        for definition_to_use in definitions_to_use:
            if definition_to_use and definition_to_use.lower()[0] == "d":
                definitions.append(self.get_desired_state_definition())
            elif definition_to_use and definition_to_use.lower()[0] == "c":
                definitions.append(self.get_current_state_definition())

        value = pcf_util.get_item_from_dicts(attribute_key, *definitions)
        if value is not None:
            return value
        else:
            return default
