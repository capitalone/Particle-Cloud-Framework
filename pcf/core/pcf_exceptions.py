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


class NoResourceException(Exception):
    def __init__(self):
        Exception.__init__(self, "No instance of the resource")


class ParentRequiredException(Exception):
    def __init__(self):
        Exception.__init__(self, "A parent is required, but none or too many were found")


class TooManyResourceException(Exception):
    def __init__(self):
        Exception.__init__(self, "Too many instances of the resource")


class NoCodeException(Exception):
    def __init__(self):
        Exception.__init__(self, "Did not provide local zipfile or zipfile location in S3")


class NoCallbackFunctionException(Exception):
    def __init__(self):
        Exception.__init__(self, "Callback function is not defined.")


class InvalidUpdateParamException(Exception):
    def __init__(self):
        Exception.__init__(self, "Attempted to update invalid parameter fields")


class InvalidConfigException(Exception):
    def __init__(self, message="Particle config validation failed"):
        Exception.__init__(self, message)


class InvalidUniqueKeysException(Exception):
    def __init__(self, message="Particle unique keys validation failed"):
        Exception.__init__(self, message)


class InvalidCacheTTLException(Exception):
    def __init__(self):
        Exception.__init__(self, "cache_ttl cannot be below 10")


class ResourceLookupNotDefinedException(Exception):
    def __init__(self, message="Resource lookup class not defined"):
        Exception.__init__(self, message)


class FlavorMissingException(Exception):
    def __init__(self):
        Exception.__init__(self, "Flavor is missing from the particle definition")


class InvalidTagsException(Exception):
    def __init__(self, message="Tag validation failed"):
        Exception.__init__(self, message)


class InvalidValueReplaceException(Exception):
    def __init__(self, message="Invalid inputs for definition variable replace ($)"):
        Exception.__init__(self, message)


class MissingException(Exception):
    def __init__(self, message="Attempted to use missing value"):
        Exception.__init__(self, message)


class MaxTimeoutException(Exception):
    def __init__(self, message="Max timeout reached while in apply()"):
        Exception.__init__(self, message)


class InvalidState(Exception):
    def __init__(self, message="Attempted to set a state that is not valid"):
        Exception.__init__(self, message)


class MissingInput(Exception):
    def __init__(self, message="Missing Required Input"):
        Exception.__init__(self, message)
