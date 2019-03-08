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

from pcf.util.aws.tag_specifications import TagSpecifications


TS_LOL_CATS = TagSpecifications('sad', lol='cats')
TS_CATS_LOL = TagSpecifications('sad', cats='lol')
TS_GG_CATS_LOL_CATS = TagSpecifications('sad', gg='cats', lol='cats')
TS_LOL_CATS_GG_CATS = TagSpecifications('sad', lol='cats', gg='cats')
TS_EMPTY = TagSpecifications('sad')


class TestTagSpecification:
    def test_init(self):
        tag_specification = TagSpecifications("gg", rofl="lol")
        assert tag_specification.tags == {"rofl":"lol"}
        assert tag_specification.resource_type == "gg"

        ############## Test Separator ###############
        tag_specification = TagSpecifications("gg", rofl="lol", lol="cats")
        assert tag_specification.tags == {"rofl":"lol", "lol": "cats"}
        assert tag_specification.resource_type == "gg"

        ############## Test Separator ###############
        tag_specification = TagSpecifications("gg")
        assert tag_specification.tags == {}
        assert tag_specification.resource_type == "gg"

    def test_render(self):
        tag_specification = TagSpecifications("gg", rofl="lol")
        rendered_tags = tag_specification.render()

        assert len(rendered_tags) == 1
        assert rendered_tags[0]["ResourceType"] == "gg"
        assert len(rendered_tags[0]["Tags"]) == 1
        assert rendered_tags[0]["Tags"][0] == {"Key": "rofl", "Value": "lol"}

        ############## Test Separator ###############
        tag_specification = TagSpecifications("gg", rofl="lol", lol="cats")
        rendered_tags = tag_specification.render()

        allowed_tag_specs = [{"Key": "lol", "Value": "cats"}, {"Key": "rofl", "Value": "lol"}]

        assert len(rendered_tags) == 1
        assert rendered_tags[0]["ResourceType"] == "gg"
        assert len(rendered_tags[0]["Tags"]) == 2
        assert rendered_tags[0]["Tags"][0] in allowed_tag_specs
        assert rendered_tags[0]["Tags"][1] in allowed_tag_specs

        ############## Test Separator ###############
        tag_specification = TagSpecifications("gg")
        rendered_tags = tag_specification.render()

        assert len(rendered_tags) == 1
        assert rendered_tags[0]["ResourceType"] == "gg"
        assert len(rendered_tags[0]["Tags"]) == 0

    def test_add_tag(self):
        tag_specification = TagSpecifications("gg", rofl="lol")
        tag_specification.add_tag("lol", "cats")

        assert tag_specification.tags == {"rofl":"lol", "lol": "cats"}

        tag_specification.add_tag("lol", "wp")
        assert tag_specification.tags == {"rofl":"lol", "lol": "wp"}

    def test_add_tags(self):
        tag_specification = TagSpecifications("gg", rofl="lol")
        tag_specification.add_tags(lol="cats", gg="wp")

        assert tag_specification.tags == {"rofl":"lol", "lol": "cats", "gg":"wp"}

        tag_specification.add_tags()

        assert tag_specification.tags == {"rofl":"lol", "lol": "cats", "gg":"wp"}

        tag_specification.add_tags(lol="meow", rofl="copter")

        assert tag_specification.tags == {"rofl":"copter", "lol": "meow", "gg":"wp"}

        tag_specification.add_tags(**{"gg":"wp", "gl":"hf"})

        assert tag_specification.tags == {"rofl":"copter", "lol": "meow", "gg":"wp", "gl":"hf"}

    def test_delete_tag(self):
        tag_specification = TagSpecifications("gg", rofl="lol")
        tag_specification.delete_tag("gl")

        assert tag_specification.tags == {"rofl":"lol"}

        tag_specification.delete_tag(None)
        assert tag_specification.tags == {"rofl":"lol"}

        tag_specification.delete_tag("rofl")
        assert tag_specification.tags == {}

        tag_specification.delete_tag("rofl")
        assert tag_specification.tags == {}

    def test_delete_tags(self):
        tag_specification = TagSpecifications("gg", rofl="lol", lol="cats")
        tag_specification.delete_tags()
        assert tag_specification.tags == {"rofl":"lol", "lol":"cats"}

        tag_specification.delete_tags("gg", "gl")
        assert tag_specification.tags == {"rofl":"lol", "lol":"cats"}

        tag_specification.delete_tags("rofl", "lol")
        assert tag_specification.tags == {}


    def test_create_from_aws_response(self):
        aws_response_full = {
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'gl',
                            'Value': 'hf'
                        },
                    ]
                },
            ]
        }

        tag_specification = TagSpecifications.create_from_aws_response(aws_response_full)
        assert tag_specification.resource_type == 'instance'
        assert tag_specification.tags == {'gl': 'hf'}

        ############## Test Separator ###############
        aws_response_partial = [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'gg',
                            'Value': 'wp'
                        },
                    ]
                },
            ]

        tag_specification = TagSpecifications.create_from_aws_response(aws_response_partial)
        assert tag_specification.resource_type == 'instance'
        assert tag_specification.tags == {'gg': 'wp'}

        def test_subtract_empty():
            assert (TS_CATS_LOL - TS_EMPTY).tags == { 'cats': 'lol' }
            assert (TS_GG_CATS_LOL_CATS - TS_EMPTY).tags == { 'gg': 'cats', 'lol': 'cats'}
            assert (TS_EMPTY - TS_CATS_LOL).tags == {}
            assert (TS_EMPTY - TS_GG_CATS_LOL_CATS).tags == {}

        def test_subtract_unordered():
            assert (TS_GG_CATS_LOL_CATS - TS_LOL_CATS_GG_CATS).tags == {}
            assert (TS_LOL_CATS_GG_CATS - TS_GG_CATS_LOL_CATS).tags == {}

        def test_subract_one_tag():
            assert (TS_GG_CATS_LOL_CATS - TS_LOL_CATS).tags == { 'gg': 'cats' }
            assert (TS_LOL_CATS - TS_GG_CATS_LOL_CATS).tags == {}

        def test_subtract_disjoint():
            assert (TS_GG_CATS_LOL_CATS - TS_CATS_LOL).tags == { 'gg': 'cats', 'lol': 'cats' }
            assert (TS_CATS_LOL - TS_GG_CATS_LOL_CATS).tags == { 'cats': 'lol' }
