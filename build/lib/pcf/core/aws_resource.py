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

import boto3
from pcf.core.particle import Particle
from pcf.util import pcf_util
from pcf.util.aws.aws_lookup import AWSLookup


class AWSResource(Particle):
    """The aws resource class inherits the particle class and adds the aws client. It takes as an input the resource_name (ie ec2)
    and the arn (if known)
    """
    lookup = AWSLookup

    def __init__(self, particle_definition, resource_name, arn=None, session=None):
        super(AWSResource, self).__init__(particle_definition)
        self._arn = arn
        self.resource_name = resource_name
        self.desired_state_definition = self.particle_definition["aws_resource"]
        self.custom_config = self.desired_state_definition.get("custom_config", {})

        self._client = None
        self._resource = None
        self._session = session

    @property
    def client(self):
        if not self._client:
            region_name = self.particle_definition["aws_resource"].get("region_name")
            self._client = self._get_client(self._session, region_name=region_name)
        return self._client

    @property
    def resource(self):
        """Returns the aws resource object"""
        if not self._resource:
            region_name = self.particle_definition["aws_resource"].get("region_name")
            self._resource = self._get_resource(self._session, region_name=region_name)
        return self._resource

    def _get_client(self, session, **kwargs):
        if session: return session.client(self.resource_name, **kwargs)

        return boto3.client(self.resource_name, **kwargs)

    def _get_resource(self, session, **kwargs):
        try:
            if session: return session.resource(self.resource_name, **kwargs)
            return boto3.resource(self.resource_name, **kwargs)
        except:
            pass

    def apply(self, sync=True, cascade=False, validate_config=False, max_timeout=None, src_cascade=None, cache_ttl=15):
        # replace and lookup id values
        self.id_replace()
        super().apply(sync=sync,cascade=cascade, validate_config=validate_config, max_timeout=max_timeout, src_cascade=src_cascade, cache_ttl=15)

    def get_region(self):
        return self.client.meta.region_name

    def set_region(self, session=None, region_name=None):
        self.client = self._get_client(session=session, region_name=region_name)
        self.resource = self._get_resource(session=session, region_name=region_name)

    # Override - some AWS resources have human-readable names
    def get_label(self):
        return self.get_identifier()

    # Override - sometimes an identifier is not an ARN (e.g. ec2 instance ids)
    def get_identifier(self):
        return self.arn

    @property
    def arn(self):
        """
        :Returns
            arn (str): The particle's arn"""
        if not self._arn:
            self._arn = self._get_arn()
        return self._arn

    def _get_arn(self):
        """This gets the arn if it is not provided in the particle definition. This is implemented in each particle.
        """
        raise NotImplementedError

    def id_replace(self):
        """
        Looks through the particle definition for $lookup and replaces them with specified resource with given name
        """
        aws_lookup = self.lookup()
        var_lookup_list = pcf_util.find_nested_vars(self.desired_state_definition, var_list=[])
        for (nested_key, id_var) in var_lookup_list:
            if id_var[0] == "lookup":
                resource = id_var[1]
                names = id_var[2].split(':')
                var = aws_lookup.get_id(resource, names)
                pcf_util.replace_value_nested_dict(curr_dict=self.desired_state_definition,
                                                     list_nested_keys=nested_key.split('.'), new_value=var)
