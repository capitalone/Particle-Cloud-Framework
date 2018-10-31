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

class TagSpecifications(object):
    DEFAULT_RESOURCE_TYPE = None
    KEY = "Key"
    VALUE = "Value"

    def __init__(self, resource_type, **kwargs):
        self.resource_type = resource_type if resource_type else self.DEFAULT_RESOURCE_TYPE
        self.tags = kwargs if kwargs else {}

    def render(self):
        tags_list = []
        for k, v in self.tags.items():
            tags_list.append({
                self.KEY: k,
                self.VALUE: v
            })

        return [
            {
                'ResourceType': self.resource_type,
                'Tags': tags_list
            }
        ]

    def add_tag(self, name, value):
        self.tags[name] = value

    def add_tags(self, *tags, **kvp):
        for tag in tags:
            self.add_tag(tag['Key'], tag['Value'])

        for k, v in kvp.items():
            self.add_tag(k, v)

    def delete_tag(self, name):
        if name in self.tags:
            self.tags.pop(name)

    def delete_tags(self, *names):
        for name in names:
            self.delete_tag(name)

    @classmethod
    def create_from_aws_response(cls, aws_response):
        tag_specifications_resp = []
        if isinstance(aws_response, dict):
            tag_specifications_resp = aws_response.get("TagSpecifications")
        elif isinstance(aws_response, list):
            tag_specifications_resp = aws_response

        if len(tag_specifications_resp) == 1:
            resource_type = tag_specifications_resp[0]["ResourceType"]
            tags = tag_specifications_resp[0]["Tags"]
            tags_dict = {}

            for tag in tags:
                tags_dict[tag[cls.KEY]] = tag[cls.VALUE]

            return TagSpecifications(resource_type, **tags_dict)

        else:
            raise Exception("Invalid AWS response format: {}".format(aws_response))

    def __sub__(self, other):
        if self.resource_type != other.resource_type:
            raise ValueError('resource_type must be the same')

        result = TagSpecifications(resource_type=self.resource_type)
        difference = self.tags.items() - other.tags.items()
        result.add_tags(**dict(difference))
        return result

class EC2InstanceTagSpecifications(TagSpecifications):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__("instance", **kwargs)


class EBSTagSpecifications(TagSpecifications):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__("volume", **kwargs)
